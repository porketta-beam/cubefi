const axios = require('axios');

exports.getRealtimePrice = async (ticker) => {
  // 실제 증권사 Open API 연동이 필요합니다. (여기선 예시)
  // 예시: 랜덤 가격 반환
  return {
    ticker,
    price: 60000 + Math.floor(Math.random() * 10000),
    time: new Date().toISOString()
  };
}; 