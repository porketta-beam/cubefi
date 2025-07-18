import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

export default function TaxBotWidget() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: '안녕하세요! 스탁디택스봇입니다. 세금, 절세, 신고 등 궁금한 점을 물어보세요!'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      const response = await axios.post('http://localhost:8001/api/chatbot/message', {
        message: inputMessage
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.data.data.message
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chatbot error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
      };
      setMessages(prev => [...prev, errorMessage]);
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

  // 줄바꿈을 <br> 태그로 변환하는 함수
  const formatMessage = (text) => {
    return text.split('\n').map((line, index) => (
      <span key={index}>
        {line}
        {index < text.split('\n').length - 1 && <br />}
      </span>
    ));
  };

  return (
    <div className="taxbot-widget">
      <h3>스탁디택스봇</h3>
      <div className="chatbot-container">
        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`chat-message ${message.type}`}>
              {formatMessage(message.content)}
            </div>
          ))}
          {isLoading && (
            <div className="chat-message bot loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="메시지를 입력하세요..."
            disabled={isLoading}
            style={{ flex: 1 }}
          />
          <button 
            onClick={sendMessage} 
            disabled={isLoading || !inputMessage.trim()}
            style={{ flexShrink: 0 }}
          >
            전송
          </button>
        </div>
      </div>
      <p>세금, 절세, 신고 등 궁금한 점을 챗봇에 물어보세요!</p>
    </div>
  );
} 