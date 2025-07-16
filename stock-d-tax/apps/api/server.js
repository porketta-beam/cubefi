require('dotenv').config();
const express = require('express');
const cors = require('cors');
const http = require('http');
const socketIo = require('socket.io');
const { getRealtimePrice } = require('./services/stockApi');
const taxRoutes = require('./routes/tax');
const chatbotRoutes = require('./routes/chatbot');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "http://localhost:3000",
    methods: ["GET", "POST"]
  }
});

// 미들웨어
app.use(cors());
app.use(express.json());

// 라우트
app.use('/api/tax', taxRoutes);
app.use('/api/chatbot', chatbotRoutes);


// 기본 라우트
app.get('/', (req, res) => {
  res.json({ message: 'Stock D-TAX API Server' });
});



// WebSocket 연결
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);
  
  // 실시간 주가 데이터 전송
  const priceInterval = setInterval(async () => {
    try {
      const price = await getRealtimePrice('005930'); // 삼성전자
      socket.emit('priceUpdate', price);
    } catch (error) {
      console.error('Error fetching price:', error);
    }
  }, 5000); // 5초마다 업데이트
  
  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
    clearInterval(priceInterval);
  });
});

const PORT = process.env.PORT || 4000;
server.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`);
  console.log(`WebSocket server ready`);
}); 