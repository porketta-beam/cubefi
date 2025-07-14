const express = require('express');
const { calculateTax } = require('../controllers/taxController');
const router = express.Router();

// 세금 계산 API
router.post('/calculate', calculateTax);

// 세금 정보 조회 API
router.get('/info', (req, res) => {
  res.json({
    domestic: {
      threshold: 20000000,
      rate: 0.154,
      description: "국내주식 양도소득세 (분리과세)"
    },
    foreign: {
      rate: 0.22,
      description: "해외주식 양도소득세"
    },
    dividend: {
      rate: 0.154,
      description: "배당소득세"
    }
  });
});

module.exports = router; 