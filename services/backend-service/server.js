const express = require('express');
const app = express();

app.get('/get-data', (req, res) => {
  res.send('Hello from backend-service!');
});

app.listen(4000, () => {
  console.log('Backend-service running on port 4000');
});
