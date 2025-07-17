import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState, useRef, useEffect } from 'react';

export default function Header() {
  const router = useRouter();
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([
    {
      id: 1,
      type: 'bot',
      message: '안녕하세요! D-TAX BOT입니다. 주식 투자 세금에 대해 궁금한 점이 있으시면 언제든 물어보세요. 📊💰\n\n빠른 질문 버튼을 클릭하거나 직접 질문해주세요!',
      image: null
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [selectedImage, setSelectedImage] = useState(null);
  const chatbotRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const isActive = (path) => router.pathname === path;

  // 빠른 질문들
  const quickQuestions = [
    "분리과세가 뭔가요?",
    "해외주식 세금은 어떻게 되나요?",
    "실현손익과 미실현손익 차이점",
    "양도소득세 계산 방법",
    "절세 전략 추천해주세요"
  ];

  // 자동 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  // 드래그 시작
  const handleMouseDown = (e) => {
    if (e.target.closest('.chatbot-header') && !e.target.closest('.chatbot-close')) {
      setIsDragging(true);
      const rect = chatbotRef.current.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
    }
  };

  // 드래그 중
  const handleMouseMove = (e) => {
    if (isDragging) {
      const newX = e.clientX - dragOffset.x;
      const newY = e.clientY - dragOffset.y;
      
      // 화면 경계 체크
      const maxX = window.innerWidth - chatbotRef.current.offsetWidth;
      const maxY = window.innerHeight - chatbotRef.current.offsetHeight;
      
      setPosition({
        x: Math.max(0, Math.min(newX, maxX)),
        y: Math.max(0, Math.min(newY, maxY))
      });
    }
  };

  // 드래그 종료
  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragOffset]);

  // 이미지 업로드 처리
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // 드래그 앤 드롭 처리
  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target.result);
      };
      reader.readAsDataURL(files[0]);
    }
  };

  // 이미지 제거
  const removeImage = () => {
    setSelectedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim() && !selectedImage) return;

    await sendMessage(chatMessage, selectedImage);
  };

  const sendMessage = async (message, image = null) => {
    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now(),
      type: 'user',
      message: message,
      image: image
    };
    setChatHistory(prev => [...prev, userMessage]);
    setChatMessage('');
    setSelectedImage(null);
    setIsTyping(true);

    try {
      // API 호출 (이미지 포함)
      const formData = new FormData();
      formData.append('message', message || '이미지를 분석해주세요');
      if (image) {
        // Base64 이미지를 Blob으로 변환
        const response = await fetch(image);
        const blob = await response.blob();
        formData.append('image', blob, 'image.jpg');
      }

      const apiResponse = await fetch('http://localhost:8000/api/chatbot/message', {
        method: 'POST',
        body: formData,
      });

      if (!apiResponse.ok) {
        throw new Error(`HTTP error! status: ${apiResponse.status}`);
      }

      const data = await apiResponse.json();
      console.log('API Response:', data);
      
      // 봇 응답 추가 (이미지 포함 가능)
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        message: data.response || data.data?.message || '응답을 받지 못했습니다.',
        image: data.image || null
      };
      setChatHistory(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chatbot API Error:', error);
      // 에러 시 기본 응답
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        message: `죄송합니다. 일시적인 오류가 발생했습니다. (${error.message})`,
        image: null
      };
      setChatHistory(prev => [...prev, botMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickQuestion = (question) => {
    sendMessage(question);
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

  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  const handleLogin = () => {
    setIsLoggedIn(true);
    setShowLoginModal(false);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setShowProfileDropdown(false);
  };

  const toggleProfileDropdown = () => {
    setShowProfileDropdown(!showProfileDropdown);
  };

  // 외부 클릭 시 프로필 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showProfileDropdown && !event.target.closest('.user-profile-container')) {
        setShowProfileDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showProfileDropdown]);

  return (
    <>
      <header className="header">
        <div className="header-container">
          <div className="header-left">
            <Link href="/" className="logo">
              Stock D-TAX
            </Link>
            <nav className="header-nav">
            <Link href="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>서비스 소개</Link>
            <Link href="/dashboard" className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}>대시보드</Link>
              <Link href="/chart" className={`nav-link ${isActive('/chart') ? 'active' : ''}`}>차트</Link>
              <Link href="/assets" className={`nav-link ${isActive('/assets') ? 'active' : ''}`}>자산</Link>
            </nav>
          </div>
          <div className="header-chatbot">
            <button 
              className={`chatbot-toggle ${isChatbotOpen ? 'active' : ''}`}
              onClick={() => setIsChatbotOpen(!isChatbotOpen)}
            >
              <span className="chatbot-icon">🤖</span>
              <span className="chatbot-text">D-TAX BOT</span>
            </button>
          </div>
          <div className="header-right">
            <div className="homepage-auth">
              {!isLoggedIn ? (
                <button 
                  className="login-btn"
                  onClick={() => setShowLoginModal(true)}
                >
                  로그인
                </button>
              ) : (
                <div className="user-profile-container">
                  <div 
                    className={`user-profile ${showProfileDropdown ? 'active' : ''}`}
                    onClick={toggleProfileDropdown}
                  >
                    <span className="user-avatar">👤</span>
                    <span className="user-name">이주현님</span>
                    <span className="dropdown-arrow">{showProfileDropdown ? '▲' : '▼'}</span>
                  </div>
                  {showProfileDropdown && (
                    <div className="profile-dropdown">
                      <Link href="/assets" className="dropdown-item" onClick={() => setShowProfileDropdown(false)}>
                        <span className="dropdown-icon">💼</span>
                        <span>내 자산 보러가기</span>
                      </Link>
                      <button className="dropdown-item logout-item" onClick={handleLogout}>
                        <span className="dropdown-icon">🚪</span>
                        <span>로그아웃</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
            <button className="header-icon" title="다운로드">&#8681;</button>
            <button className="header-icon" title="도움말">&#10068;</button>
            <button className="header-icon" title="메뉴">&#9776;</button>
          </div>
        </div>
      </header>

      {/* 로그인 모달 */}
      {showLoginModal && (
        <div className="modal-overlay" onClick={() => setShowLoginModal(false)}>
          <div className="login-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">로그인</h3>
              <button 
                className="modal-close"
                onClick={() => setShowLoginModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="login-form">
                <div className="form-group">
                  <label>이메일</label>
                  <input type="email" placeholder="이메일을 입력하세요" />
                </div>
                <div className="form-group">
                  <label>비밀번호</label>
                  <input type="password" placeholder="비밀번호를 입력하세요" />
                </div>
                <button className="login-submit-btn" onClick={handleLogin}>
                  로그인
                </button>
                <div className="login-divider">
                  <span>또는</span>
                </div>
                <div className="social-login">
                  <button className="social-btn kakao">
                    <span>💬</span> 카카오 로그인
                  </button>
                  <button className="social-btn naver">
                    <span>N</span> 네이버 로그인
                  </button>
                  <button className="social-btn google">
                    <span>G</span> 구글 로그인
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 챗봇 드롭다운 */}
      {isChatbotOpen && (
        <div 
          className="header-chatbot-dropdown"
          ref={chatbotRef}
          style={{
            left: position.x,
            top: position.y,
            cursor: isDragging ? 'grabbing' : 'default'
          }}
          onMouseDown={handleMouseDown}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <div className="chatbot-header">
            <div className="chatbot-title">
              <span className="chatbot-avatar">🤖</span>
              <span>D-TAX BOT</span>
            </div>
            <button 
              className="chatbot-close"
              onClick={() => setIsChatbotOpen(false)}
            >
              ✕
            </button>
          </div>
          <div className="chatbot-messages">
            {chatHistory.map((msg) => (
              <div key={msg.id} className={`chatbot-message ${msg.type}`}>
                {formatMessage(msg.message)}
                {msg.image && (
                  <div className="message-image">
                    <img src={msg.image} alt="첨부된 이미지" />
                  </div>
                )}
              </div>
            ))}
            {isTyping && (
              <div className="chatbot-message bot typing">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          {/* 빠른 질문 버튼들 */}
          <div className="quick-questions">
            {quickQuestions.map((question, index) => (
              <button
                key={index}
                className="quick-question-btn"
                onClick={() => handleQuickQuestion(question)}
                disabled={isTyping}
              >
                {question}
              </button>
            ))}
          </div>
          
          {/* 이미지 업로드 영역 */}
          {selectedImage && (
            <div className="image-preview">
              <img src={selectedImage} alt="선택된 이미지" />
              <button className="remove-image" onClick={removeImage}>
                ✕
              </button>
            </div>
          )}
          
          <form className="chatbot-input" onSubmit={handleChatSubmit}>
            <div className="input-actions">
              <button
                type="button"
                className="image-upload-btn"
                onClick={() => fileInputRef.current?.click()}
                disabled={isTyping}
                title="이미지 업로드"
              >
                📷
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                style={{ display: 'none' }}
              />
            </div>
            <input
              type="text"
              placeholder="주식 세금에 대해 궁금한 점을 물어보세요..."
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              disabled={isTyping}
            />
            <button type="submit" disabled={(!chatMessage.trim() && !selectedImage) || isTyping}>
              ➤
            </button>
          </form>
        </div>
      )}
    </>
  );
} 