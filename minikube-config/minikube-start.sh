#!/bin/bash

# Остановка при ошибке
set -e

minikube stop
minikube delete

# Запуск Minikube
echo "Запускаем Minikube..."
minikube start --driver=docker

# Устанавливаем переменные окружения для использования Docker с Minikube
echo "Переключаем Docker на Minikube..."
eval $(minikube -p minikube docker-env)

# Пересборка Docker-образов внутри Minikube
echo "Собираем Docker-образы..."
docker build -t security-deployment:latest ../services/security-service
docker build -t frontend-deployment:latest ../services/frontend-service
docker build -t backend-deployment:latest ../services/backend-service
docker build -t logs-deployment:latest ../services/logs-service
docker build -t db-deployment:latest ../services/db-service

# Применяем все манифесты Kubernetes
echo "Применяем Kubernetes манифесты..."
kubectl apply -f ../kubernetes/

# # Проверяем, что все Pods запущены
echo "Ожидание запуска Pods..."
kubectl wait --for=condition=ready pod --all

# Запускаем туннель для доступа к сервису NodePort
echo "Запускаем Minikube Tunnel..."
minikube tunnel &
echo "Minikube Tunnel запущен в фоновом режиме."

# Получаем IP Minikube и выводим инструкции
IP=$(minikube ip)
echo "Приложение готово."

kubectl port-forward service/security-service 8080:5000
