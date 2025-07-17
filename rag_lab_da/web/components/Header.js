'use client'

import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState, useRef, useEffect } from 'react';
import { flushSync } from 'react-dom';
import React from 'react';

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
  const [streamingMessage, setStreamingMessage] = useState(''); // 스트리밍 중인 메시지
  const [streamingId, setStreamingId] = useState(null); // 스트리밍 중인 메시지 ID
  const streamingRef = useRef(null); // 스트리밍 메시지 DOM 참조
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
      if (image) {
        // 이미지가 있는 경우 기존 방식대로 /api/chatbot 사용
        const formData = new FormData();
        formData.append('message', message || '이미지를 분석해주세요');
        // Base64 이미지를 Blob으로 변환
        const response = await fetch(image);
        const blob = await response.blob();
        formData.append('image', blob, 'image.jpg');

        const apiResponse = await fetch('/api/chatbot', {
          method: 'POST',
          body: formData,
        });

        const data = await apiResponse.json();
        const botMessage = {
          id: Date.now() + 1,
          type: 'bot',
          message: data.response,
          image: data.image || null
        };
        setChatHistory(prev => [...prev, botMessage]);
      } else {
        /* 기존 fetch 방식 (주석처리)
        // 이미지가 없는 경우 FastAPI 서버의 /chat으로 스트림 요청
        const apiResponse = await fetch('http://localhost:8000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message }),
        });

        if (!apiResponse.ok) {
          throw new Error(`HTTP error! status: ${apiResponse.status}`);
        }
        if (!apiResponse.body) throw new Error('No stream response');

        let botMsg = '';
        const botMessageId = Date.now() + 1;
        
        // 스트리밍 상태 초기화
        setStreamingId(botMessageId);
        setStreamingMessage('');
        setIsTyping(false); // 스트림 시작 시 로딩 인디케이터 제거

        const reader = apiResponse.body.getReader();
        const decoder = new TextDecoder('utf-8');
        
        try {
          let done = false;
          let buffer = '';
          
          while (!done) {
            const { value, done: doneReading } = await reader.read();
            done = doneReading;
            
            if (value) {
              const chunk = decoder.decode(value, { stream: true });
              console.log('받은 청크:', chunk); // 디버깅용
              
              // 즉시 처리 방식 - 청크를 바로 누적
              buffer += chunk;
              
              // 완전한 SSE 이벤트만 처리 (data: content\n\n)
              let processedLength = 0;
              const lines = buffer.split('\n');
              
              for (let i = 0; i < lines.length - 1; i++) { // 마지막 불완전한 라인 제외
                const line = lines[i];
                console.log('받은 라인:', line); // 디버깅용
                
                if (line.startsWith('data: ')) {
                  const content = line.slice(6).trim(); // 'data: ' 제거
                  console.log('처리할 내용:', content); // 디버깅용
                  if (content && content !== '[DONE]') {
                    botMsg += content;
                    console.log('누적 메시지:', botMsg); // 디버깅용
                    // 스트리밍 메시지 실시간 업데이트
                    setStreamingMessage(botMsg);
                    
                    // 스트리밍 중 자동 스크롤
                    setTimeout(scrollToBottom, 10);
                  }
                }
                processedLength += lines[i].length + 1; // +1 for \n
              }
              
              // 처리된 부분을 버퍼에서 제거, 마지막 불완전한 라인은 유지
              buffer = buffer.slice(processedLength);
            }
          }
          
          // 스트리밍 완료 - chatHistory에 최종 메시지 추가
          setChatHistory(prev => [...prev, {
            id: botMessageId,
            type: 'bot',
            message: botMsg || '응답을 받지 못했습니다.',
            image: null
          }]);
          setStreamingId(null);
          setStreamingMessage('');
          
        } catch (streamError) {
          console.error('Stream reading error:', streamError);
          setChatHistory(prev => prev.map(msg =>
            msg.id === botMessageId ? { 
              ...msg, 
              message: '스트림 처리 중 오류가 발생했습니다.',
              isStreaming: false 
            } : msg
          ));
        } finally {
          reader.releaseLock();
        }
        */

        // WebSocket 방식 - 개선된 실시간 렌더링
        const ws = new WebSocket('ws://localhost:8000/ws/chat');
        let botMsg = '';
        const botMessageId = Date.now() + 1;
        
        // 스트리밍 상태 초기화
        setStreamingId(botMessageId);
        setStreamingMessage('');
        setIsTyping(false);

        // 연결 타임아웃 설정
        const connectionTimeout = setTimeout(() => {
          if (ws.readyState !== WebSocket.OPEN) {
            ws.close();
            setChatHistory(prev => [...prev, {
              id: botMessageId,
              type: 'bot',
              message: '연결 시간이 초과되었습니다. 다시 시도해주세요.',
              image: null
            }]);
            setStreamingId(null);
            setStreamingMessage('');
          }
        }, 5000);

        ws.onopen = () => {
          console.log('WebSocket 연결됨');
          clearTimeout(connectionTimeout);
          // 메시지 전송
          ws.send(JSON.stringify({ message }));
        };

        ws.onmessage = (event) => {
          console.log('받은 메시지:', event.data);
          
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'start') {
              console.log('스트리밍 시작');
              botMsg = '';
              setStreamingMessage('');
            } else if (data.type === 'chunk') {
              // 스트리밍 청크 처리 - 실시간 렌더링 개선
              console.log('청크 내용:', data.content);
              botMsg += data.content;
              
              // DOM 직접 업데이트로 즉시 반영 (React 상태 업데이트 제거)
              if (streamingRef.current) {
                streamingRef.current.textContent = botMsg;
              }
              
              // 스크롤 즉시 적용
              requestAnimationFrame(scrollToBottom);
              
            } else if (data.type === 'done') {
              console.log('스트리밍 완료');
              // 최종 메시지를 채팅 히스토리에 추가
              setChatHistory(prev => [...prev, {
                id: botMessageId,
                type: 'bot',
                message: botMsg || '응답을 받지 못했습니다.',
                image: null
              }]);
              
              // 스트리밍 상태 정리
              setStreamingId(null);
              setStreamingMessage('');
              ws.close();
              
            } else if (data.type === 'error') {
              console.error('서버 오류:', data.message);
              setChatHistory(prev => [...prev, {
                id: botMessageId,
                type: 'bot',
                message: `오류: ${data.message}`,
                image: null
              }]);
              setStreamingId(null);
              setStreamingMessage('');
              ws.close();
            }
          } catch (parseError) {
            console.error('JSON 파싱 오류:', parseError, 'Raw data:', event.data);
            // JSON 파싱 실패시 원본 데이터 처리
            if (typeof event.data === 'string' && event.data.trim()) {
              botMsg += event.data;
              if (streamingRef.current) {
                streamingRef.current.textContent = botMsg;
              }
            }
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket 오류:', error);
          clearTimeout(connectionTimeout);
          setChatHistory(prev => [...prev, {
            id: botMessageId,
            type: 'bot',
            message: 'WebSocket 연결 오류가 발생했습니다. 네트워크를 확인해주세요.',
            image: null
          }]);
          setStreamingId(null);
          setStreamingMessage('');
        };

        ws.onclose = (event) => {
          console.log('WebSocket 연결 종료', event.code, event.reason);
          clearTimeout(connectionTimeout);
          
          // 비정상 종료 처리
          if (event.code !== 1000 && streamingId === botMessageId) {
            setChatHistory(prev => [...prev, {
              id: botMessageId,
              type: 'bot',
              message: botMsg || '연결이 중단되었습니다. 다시 시도해주세요.',
              image: null
            }]);
            setStreamingId(null);
            setStreamingMessage('');
          }
        };
      }
    } catch (error) {
      // 에러 시 기본 응답
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        message: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
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

  return (
    <>
      <header className="header">
        <div className="header-container">
          <div className="header-left">
            <Link href="/" className="logo">
              Stock D-TAX
            </Link>
            <nav className="header-nav">
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
            <div className="profile">
              <div className="profile-avatar" style={{background:'#2ee86c'}}>🐦</div>
              <div>
                <div className="profile-name">이주현</div>
              </div>
            </div>
            <button className="header-icon" title="다운로드">&#8681;</button>
            <button className="header-icon" title="도움말">&#10068;</button>
            <button className="header-icon" title="메뉴">&#9776;</button>
          </div>
        </div>
      </header>

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
                {msg.message}
                {msg.image && (
                  <div className="message-image">
                    <img src={msg.image} alt="첨부된 이미지" />
                  </div>
                )}
              </div>
            ))}
            {streamingId && (
              <div key={streamingId} className="chatbot-message bot" ref={streamingRef}>
              </div>
            )}
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