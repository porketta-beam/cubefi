'use client'

import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState, useRef, useEffect } from 'react';
import { flushSync } from 'react-dom';
import React from 'react';
import { sendChatMessage } from '../util/websocket';

export default function Header() {
  const router = useRouter();
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([
    {
      id: 1,
      type: 'bot',
      message: '안녕하세요! D-TAX BOT입니다. 주식 투자 세금에 대해 궁금한 점이 있으시면 언제든 물어보세요. 📊💰\n\n빠른 질문 버튼을 클릭하거나 직접 질문해주세요!'
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState(''); // 스트리밍 중인 메시지
  const [streamingId, setStreamingId] = useState(null); // 스트리밍 중인 메시지 ID
  const streamingRef = useRef(null); // 스트리밍 메시지 DOM 참조
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const chatbotRef = useRef(null);
  const messagesEndRef = useRef(null);

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



  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;

    await sendMessage(chatMessage);
  };

  const sendMessage = async (message) => {
    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now(),
      type: 'user',
      message: message
    };
    setChatHistory(prev => [...prev, userMessage]);
    setChatMessage('');
    setIsTyping(true);

    try {
      // WebSocket 방식 - 모듈화된 유틸리티 사용
      let botMsg = '';
      const botMessageId = Date.now() + 1;
      
      // 스트리밍 상태 초기화
      setStreamingId(botMessageId);
      setStreamingMessage('');
      setIsTyping(false);

      try {
        await sendChatMessage(message, {
          onStart: () => {
            console.log('스트리밍 시작');
            botMsg = '';
            setStreamingMessage('');
          },
          onChunk: (content) => {
            console.log('청크 내용:', content);
            botMsg += content;
            
            // DOM 직접 업데이트로 즉시 반영
            if (streamingRef.current) {
              streamingRef.current.textContent = botMsg;
            }
            
            // 스크롤 즉시 적용
            requestAnimationFrame(scrollToBottom);
          },
          onDone: () => {
            console.log('스트리밍 완료');
            // 최종 메시지를 채팅 히스토리에 추가
            setChatHistory(prev => [...prev, {
              id: botMessageId,
              type: 'bot',
              message: botMsg || '응답을 받지 못했습니다.'
            }]);
            
            // 스트리밍 상태 정리
            setStreamingId(null);
            setStreamingMessage('');
          },
          onError: (errorMessage) => {
            console.error('WebSocket 오류:', errorMessage);
            setChatHistory(prev => [...prev, {
              id: botMessageId,
              type: 'bot',
              message: errorMessage || 'WebSocket 연결 오류가 발생했습니다. 네트워크를 확인해주세요.'
            }]);
            setStreamingId(null);
            setStreamingMessage('');
          }
        });
      } catch (error) {
        console.error('WebSocket 연결 실패:', error);
        setChatHistory(prev => [...prev, {
          id: botMessageId,
          type: 'bot',
          message: '연결 시간이 초과되었습니다. 다시 시도해주세요.'
        }]);
        setStreamingId(null);
        setStreamingMessage('');
      }
    } catch (error) {
      // 에러 시 기본 응답
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        message: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
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
          
          <form className="chatbot-input" onSubmit={handleChatSubmit}>
            <input
              type="text"
              placeholder="주식 세금에 대해 궁금한 점을 물어보세요..."
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              disabled={isTyping}
            />
            <button type="submit" disabled={!chatMessage.trim() || isTyping}>
              ➤
            </button>
          </form>
        </div>
      )}
    </>
  );
}