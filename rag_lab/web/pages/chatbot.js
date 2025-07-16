import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const EXAMPLES = [
  {
    q: '올해 국내주식 실현수익이 2,000만원을 넘었는데 종합과세 세율이 어떻게 적용되나요?',
    a: '초과분은 근로소득 등과 합산해 누진세율(6.6~49.5%)이 적용됩니다. ISA 계좌 활용, 실현수익 분산 등 절세 전략을 추천드립니다.'
  },
  {
    q: '내년에는 어떻게 분산 매도하면 좋을까요?',
    a: '실현수익을 연도별로 분산하거나 손실 종목을 일부 매도해 손익통산을 활용하면 세금 부담을 줄일 수 있습니다.'
  },
  {
    q: '해외주식 실현수익이 250만원을 넘으면?',
    a: '초과분에 대해 20% 세율이 적용됩니다. 손실 종목 매도, 연도별 분산 매도 등 절세 전략을 활용하세요.'
  }
];

export default function ChatbotPage() {
  const [messages, setMessages] = useState([
    { type: 'bot', content: '안녕하세요! 스탁디택스봇입니다. 세금, 절세, 신고 등 궁금한 점을 물어보세요!' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (msg) => {
    if (!msg.trim()) return;
    setMessages((prev) => [...prev, { type: 'user', content: msg }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:4000/api/chatbot/message', {
        message: msg
      });

      setMessages((prev) => [
        ...prev,
        { type: 'bot', content: response.data.data.message }
      ]);
    } catch (error) {
      console.error('Chatbot error:', error);
      setMessages((prev) => [
        ...prev,
        { type: 'bot', content: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div className="dashboard-container">
      <h1>스탁디택스 챗봇</h1>
      <div className="taxbot-widget" style={{maxWidth:600,margin:'0 auto'}}>
        <div className="chatbot-container">
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-message ${m.type}`}>{m.content}</div>
            ))}
            {isLoading && (
              <div className="chat-message bot loading">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="세금, 절세, 신고 등 궁금한 점을 입력하세요..."
              disabled={isLoading}
            />
            <button onClick={() => sendMessage(input)} disabled={isLoading || !input.trim()}>
              전송
            </button>
          </div>
        </div>
        <div style={{marginTop:16, color:'#888', fontSize:'0.98rem'}}>
          <b>예시 질문:</b><br/>
          {EXAMPLES.map((ex, i) => (
            <div key={i} style={{marginTop:4}}>
              <span style={{color:'#2ee86c'}}>Q.</span> {ex.q}<br/>
              <span style={{color:'#ff6384'}}>A.</span> {ex.a}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 