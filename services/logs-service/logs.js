const http = require('http');

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/log-suspicious') {
    let body = '';

    // Собираем данные из запроса
    req.on('data', chunk => {
      body += chunk.toString();
    });

    req.on('end', () => {
      try {
        // Парсим данные и выводим их в консоль
        const data = JSON.parse(body);
        console.log(`[${data.timestamp}][${data.service}] Suspicious activity detected: IP = ${data.ip}`);
        
        // Отправляем успешный ответ
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ message: 'Log received' }));
      } catch (err) {
        // Обрабатываем ошибки
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON format' }));
      }
    });
  } else {
    // Обработка других маршрутов
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

server.listen(5000, () => {
  console.log('Logs-service running on port 5000');
});