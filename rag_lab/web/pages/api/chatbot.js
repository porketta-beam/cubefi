import multer from 'multer';
import { createRouter } from 'next-connect';

// multer 설정
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB 제한
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('이미지 파일만 업로드 가능합니다.'), false);
    }
  },
});

const router = createRouter();

// 이미지 업로드 미들웨어
router.use(upload.single('image'));

router.post(async (req, res) => {
  try {
    const { message } = req.body;
    const imageFile = req.file;

    if (!message && !imageFile) {
      return res.status(400).json({ message: 'Message or image is required' });
    }

    let requestBody = { message: message || '이미지를 분석해주세요' };

    // 이미지가 있는 경우 백엔드로 전송
    if (imageFile) {
      const formData = new FormData();
      formData.append('message', requestBody.message);
      formData.append('image', new Blob([imageFile.buffer], { type: imageFile.mimetype }), imageFile.originalname);

      // 백엔드 챗봇 API 호출 (이미지 포함)
      const response = await fetch('http://localhost:8000/api/chatbot/message', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Backend API error');
      }

      const data = await response.json();
      
      res.status(200).json({ 
        response: data.data.message,
        image: data.image || null
      });
    } else {
      // 텍스트만 있는 경우 기존 방식
      const response = await fetch('http://localhost:4000/api/chatbot/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Backend API error');
      }

      const data = await response.json();
      
      res.status(200).json({ 
        response: data.data.message,
        image: data.image || null
      });
    }
  } catch (error) {
    console.error('Chatbot API error:', error);
    
    // 에러 시 기본 응답
    const defaultResponses = [
      "주식 투자 세금에 대해 궁금한 점이 있으시면 구체적으로 질문해주세요!",
      "분리과세, 종합과세, 양도소득세 등 어떤 세금에 대해 알고 싶으신가요?",
      "국내주식과 해외주식의 세금 차이점에 대해 설명드릴 수 있습니다.",
      "실현손익과 미실현손익의 세금 처리 방법을 알려드릴 수 있어요.",
      "이미지 분석에 실패했습니다. 다시 시도해주세요."
    ];
    
    const randomResponse = defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
    
    res.status(200).json({ 
      response: randomResponse,
      image: null
    });
  }
});

export default router.handler();

export const config = {
  api: {
    bodyParser: false,
  },
}; 