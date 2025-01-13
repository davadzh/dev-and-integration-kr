from flask import Flask, request, abort, jsonify, redirect
import time
from collections import defaultdict
import requests

app = Flask(__name__, static_folder="static", static_url_path="/static")
FRONTEND_SERVICE_URL = "http://frontend-service:3000"
BACKEND_CLUSTER_URL = "http://backend-service:4000/get-data"
LOGS_SERVICE_URL = "http://logs-service:5000/log-suspicious"

# Настройки ограничения запросов
RATE_LIMIT = 30  # Максимальное количество запросов
TIME_WINDOW = 60  # Временное окно в секундах

# Хранилище для данных о запросах и токенах
request_logs = defaultdict(list)

def is_request_allowed(client_ip):
    """Проверка частоты запросов для конкретного IP."""
    current_time = time.time()
    # Удаляем старые запросы, вышедшие за пределы временного окна
    request_logs[client_ip] = [
        ts for ts in request_logs[client_ip] if current_time - ts < TIME_WINDOW
    ]
    # Проверяем, превышает ли количество запросов лимит
    if len(request_logs[client_ip]) >= RATE_LIMIT:
        return False
    # Логируем текущий запрос
    request_logs[client_ip].append(current_time)
    return True

def log_suspicious_ip(ip, service):
    try:
        response = requests.post(
            LOGS_SERVICE_URL,
            json={"ip": ip, "service": service, "timestamp": time.time()},
            timeout=5
        )
        if response.status_code == 200:
            print("Suspicious IP logged successfully.")
        else:
            print(f"Failed to log IP. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error logging suspicious IP: {e}")

@app.route("/", methods=["GET"])
def proxy():
    client_ip = request.remote_addr
    if not is_request_allowed(client_ip):
        log_suspicious_ip(client_ip, 'Frontend')
        abort(429, "Too Many Requests")

    # Прокси запросы на frontend-service
    url = f"{FRONTEND_SERVICE_URL}"
    try:
        response = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
        )
        return (response.content, response.status_code, response.headers.items())
    except requests.exceptions.RequestException:
        return jsonify({"error": "Service unavailable"}), 503

@app.route("/api", methods=["GET"])
def proxy_to_backend():
    client_ip = request.remote_addr
    if not is_request_allowed(client_ip):
        log_suspicious_ip(client_ip, 'Backend')
        abort(429, "Too Many Requests")
    
    try:
        # Отправляем запрос к backend-сервису
        backend_response = requests.get(BACKEND_CLUSTER_URL)
        
        # Проверяем статус ответа
        if backend_response.status_code != 200:
            return jsonify({"error": f"Backend error: {backend_response.status_code}"}), backend_response.status_code
        
        # Возвращаем данные, полученные от backend-сервиса
        return jsonify({"data": backend_response.text})

    except requests.exceptions.RequestException as e:
        # Обрабатываем ошибки соединения
        return jsonify({"error": "Unable to reach backend service", "details": str(e)}), 503


@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({"error": "Too Many Requests", "message": str(e.description)}), 429

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)