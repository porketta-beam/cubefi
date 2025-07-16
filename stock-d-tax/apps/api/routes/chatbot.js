const express = require('express');
const multer = require('multer');
const { generateResponse } = require('../services/openaiService');
const router = express.Router();

// Multer 설정
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 5 * 1024 * 1024 // 5MB 제한
  }
});

// 챗봇 메시지 처리 (텍스트 + 이미지)
router.post('/message', upload.single('image'), async (req, res) => {
  try {
    console.log('Chatbot request received:', {
      body: req.body,
      file: req.file ? `${req.file.originalname} (${req.file.size} bytes)` : 'No file'
    });

    const { message } = req.body;
    const imageFile = req.file;
    
    if (!message && !imageFile) {
      console.log('Error: No message or image provided');
      return res.status(400).json({ 
        error: '메시지 또는 이미지가 필요합니다.' 
      });
    }

    let userMessage = message || '이미지를 분석해주세요';
    
    // 이미지가 있는 경우 이미지 정보 추가
    if (imageFile) {
      userMessage += `\n[이미지 첨부됨: ${imageFile.originalname}]`;
    }

    console.log('Processing message:', userMessage);

    // OpenAI API로 응답 생성
    const response = await generateResponse(userMessage);
    
    console.log('Generated response:', response.substring(0, 100) + '...');
    
    res.json({
      success: true,
      response: response,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Chatbot error:', error);
    res.status(500).json({ 
      error: '챗봇 응답 생성 중 오류가 발생했습니다.' 
    });
  }
});

module.exports = router; 