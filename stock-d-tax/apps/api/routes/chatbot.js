const express = require('express');
const { generateResponse } = require('../services/openaiService');
const router = express.Router();

// 챗봇 메시지 처리
router.post('/message', async (req, res) => {
  try {
    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({ 
        error: '메시지가 필요합니다.' 
      });
    }

    // OpenAI API로 응답 생성
    const response = await generateResponse(message);
    
    res.json({
      success: true,
      data: {
        message: response,
        timestamp: new Date().toISOString()
      }
    });
    
  } catch (error) {
    console.error('Chatbot error:', error);
    res.status(500).json({ 
      error: '챗봇 응답 생성 중 오류가 발생했습니다.' 
    });
  }
});

module.exports = router; 