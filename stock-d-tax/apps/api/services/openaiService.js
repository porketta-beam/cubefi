const OpenAI = require('openai');
require('dotenv').config({ path: '../config.env' });

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// 세금 관련 지식 베이스 (RAG용)
const taxKnowledgeBase = [
  {
    category: "국내주식 양도소득세",
    content: "국내주식 양도소득세는 분리과세로 15.4%입니다. 2,000만원 이하는 15.4%, 초과분은 종합소득세율이 적용됩니다. 종합소득세율은 소득에 따라 6.6%~49.5%까지 적용됩니다."
  },
  {
    category: "해외주식 양도소득세", 
    content: "해외주식 양도소득세는 22%로 국내주식보다 높습니다. 해외주식은 종합과세로 처리되며, 다른 소득과 합산하여 과세됩니다."
  },
  {
    category: "배당소득세",
    content: "배당소득세는 15.4%입니다. 배당소득은 분리과세로 처리되며, 연간 배당소득이 2,000만원 이하인 경우 15.4%가 적용됩니다."
  },
  {
    category: "세금 신고",
    content: "주식 양도소득세는 매년 5월에 종합소득세 신고와 함께 신고합니다. 증권사에서 발급하는 거래내역서를 준비해야 합니다."
  },
  {
    category: "절세 방법",
    content: "주식 투자 절세 방법: 1) 손실과 이익을 상계하여 과세표준을 줄이기, 2) 장기투자로 세율 혜택 받기, 3) 연말정산 시 손실공제 활용하기"
  }
];

// RAG: 관련 지식 검색
function findRelevantKnowledge(userQuestion) {
  const relevantDocs = taxKnowledgeBase.filter(doc => {
    const keywords = userQuestion.toLowerCase().split(' ');
    return keywords.some(keyword => 
      doc.content.toLowerCase().includes(keyword) || 
      doc.category.toLowerCase().includes(keyword)
    );
  });
  
  return relevantDocs.map(doc => `${doc.category}: ${doc.content}`).join('\n\n');
}

// OpenAI API 호출
async function generateResponse(userMessage) {
  try {
    // RAG: 관련 지식 검색
    const relevantKnowledge = findRelevantKnowledge(userMessage);
    
    const systemPrompt = `당신은 주식 투자 세금 전문가입니다. 다음 세금 관련 지식을 바탕으로 사용자의 질문에 답변해주세요:

${relevantKnowledge}

답변 시 다음 규칙을 따라주세요:
1. 정확하고 이해하기 쉽게 설명
2. 구체적인 수치와 예시 제공
3. 친근하고 도움이 되는 톤으로 답변
4. 한국어로 답변`;

    const completion = await openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userMessage }
      ],
      max_tokens: 500,
      temperature: 0.7,
    });

    return completion.choices[0].message.content;
  } catch (error) {
    console.error('OpenAI API Error:', error);
    return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
  }
}

module.exports = {
  generateResponse
}; 