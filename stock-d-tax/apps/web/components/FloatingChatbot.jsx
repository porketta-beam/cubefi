import { useState, useEffect, useRef } from 'react';

export default function FloatingChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [showBubble, setShowBubble] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: '안녕하세요! D-TAX BOT입니다. 주식 투자 세금에 대해 궁금한 점이 있으시면 언제든 물어보세요! 📊💰'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // 30초마다 말풍선 표시
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isOpen) {
        setShowBubble(true);
        setTimeout(() => setShowBubble(false), 3000); // 3초 후 말풍선 사라짐
      }
    }, 30000); // 30초마다

    // 초기 실행 (5초 후)
    const initialTimeout = setTimeout(() => {
      if (!isOpen) {
        setShowBubble(true);
        setTimeout(() => setShowBubble(false), 3000);
      }
    }, 5000);

    return () => {
      clearInterval(interval);
      clearTimeout(initialTimeout);
    };
  }, [isOpen]);

  // 자동 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleToggle = () => {
    setIsOpen(!isOpen);
    setShowBubble(false); // 챗봇 열면 말풍선 숨김
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // API 호출 (헤더 챗봇과 동일한 방식)
      const formData = new FormData();
      formData.append('message', inputMessage);

      const apiResponse = await fetch('http://localhost:8000/api/chatbot/message', {
        method: 'POST',
        body: formData,
      });

      if (!apiResponse.ok) {
        throw new Error(`HTTP error! status: ${apiResponse.status}`);
      }

      const data = await apiResponse.json();
      console.log('Floating Chatbot API Response:', data);
      
      // 봇 응답 추가
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.response || data.data?.message || '응답을 받지 못했습니다.'
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Floating Chatbot API Error:', error);
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
      };
      setMessages(prev => [...prev, botMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (text) => {
    return text.split('\n').map((line, index) => (
      <span key={index}>
        {line}
        {index < text.split('\n').length - 1 && <br />}
      </span>
    ));
  };

  return (
    <div className="floating-chatbot">
      {/* 말풍선 */}
      {showBubble && !isOpen && (
        <div className="chatbot-bubble">
          <div className="bubble-content">
            안녕하세요! D-TAX 챗봇입니다 💬
          </div>
          <div className="bubble-arrow"></div>
        </div>
      )}

      {/* 챗봇 창 */}
      {isOpen && (
        <div className="floating-chatbot-window">
          <div className="floating-chatbot-header">
            <div className="chatbot-title">
              <span className="chatbot-avatar">🤖</span>
              <span>D-TAX BOT</span>
            </div>
            <button 
              className="chatbot-close"
              onClick={handleToggle}
            >
              ✕
            </button>
          </div>
          
          <div className="floating-chatbot-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`floating-chat-message ${msg.type}`}>
                {formatMessage(msg.content)}
              </div>
            ))}
            {isLoading && (
              <div className="floating-chat-message bot loading">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <div className="floating-chatbot-input">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              disabled={isLoading}
            />
            <button onClick={sendMessage} disabled={isLoading || !inputMessage.trim()}>
              ➤
            </button>
          </div>
        </div>
      )}

      {/* 플로팅 버튼 */}
      <button 
        className={`floating-chatbot-button ${isOpen ? 'active' : ''}`}
        onClick={handleToggle}
      >
        {isOpen ? '✕' : '💬'}
      </button>
    </div>
  );
} 