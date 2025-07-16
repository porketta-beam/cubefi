import { useState } from 'react';
import Head from 'next/head';

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  const handleLogin = () => {
    setIsLoggedIn(true);
    setShowLoginModal(false);
  };

  return (
    <>
      <Head>
        <title>Stock D-TAX | 주식투자 세금 최적화 서비스</title>
        <meta name="description" content="주식투자 세금을 최적화하고 절세 전략을 제공하는 스마트한 서비스" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Header */}
      <header className="homepage-header">
        <div className="homepage-header-container">
          
          <nav className="homepage-nav">
            <a href="#features" className="nav-link">서비스 소개</a>
            <a href="#calculator" className="nav-link">세금 계산기</a>
            <a href="#comparison" className="nav-link">계좌 비교</a>
            <a href="#mydata" className="nav-link">자산 연결</a>
          </nav>
          
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <h1 className="hero-title">
              주식투자 세금, <br />
              <span className="gradient-text">더 똑똑하게 관리하세요</span> 💡
            </h1>
            <p className="hero-description">
              복잡한 주식 세금 계산부터 절세 전략까지,<br />
              Stock D-TAX와 함께 투자 수익을 극대화하세요!
            </p>
            <div className="hero-cta">
              <button className="cta-primary" onClick={() => setShowLoginModal(true)}>
                <span>🚀</span> 무료로 시작하기
              </button>
              <button className="cta-secondary">
                <span>📹</span> 서비스 둘러보기
              </button>
            </div>
          </div>
          <div className="hero-visual">
            <div className="hero-cards">
              <div className="hero-card card-1">
                <div className="card-icon">💰</div>
                <div className="card-title">실시간 세금 계산</div>
                <div className="card-amount positive">+2,450,000원</div>
              </div>
              <div className="hero-card card-2">
                <div className="card-icon">🏦</div>
                <div className="card-title">ISA 절세 효과</div>
                <div className="card-amount">456,000원 절약</div>
              </div>
              <div className="hero-card card-3">
                <div className="card-icon">📈</div>
                <div className="card-title">포트폴리오 수익률</div>
                <div className="card-amount positive">+12.4%</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section" id="features">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">왜 Stock D-TAX를 선택해야 할까요? 🤔</h2>
            <p className="section-subtitle">복잡한 세금 계산, 이제 간단하게 해결하세요</p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🧮</div>
              <h3 className="feature-title">정확한 세금 계산</h3>
              <p className="feature-description">
                국내/해외 주식, 배당소득세까지<br />
                모든 세금을 정확하게 계산해드려요
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔗</div>
              <h3 className="feature-title">마이데이터 연동</h3>
              <p className="feature-description">
                증권사 계좌를 안전하게 연결하여<br />
                자동으로 거래 내역을 불러와요
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">💡</div>
              <h3 className="feature-title">AI 절세 컨설팅</h3>
              <p className="feature-description">
                개인 맞춤형 절세 전략을<br />
                AI가 실시간으로 제안해드려요
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3 className="feature-title">계좌별 비교 분석</h3>
              <p className="feature-description">
                일반/ISA/IRP/연금저축까지<br />
                최적의 투자 방법을 찾아드려요
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Target Users Section */}
      <section className="target-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">이런 분들에게 추천해요! 👥</h2>
          </div>
          <div className="target-grid">
            <div className="target-card">
              <div className="target-emoji">🔰</div>
              <h3 className="target-title">주식 초보자</h3>
              <p className="target-description">
                "세금이 얼마나 나올지 모르겠어요"<br />
                복잡한 세금 계산, 저희가 도와드릴게요!
              </p>
            </div>
            <div className="target-card">
              <div className="target-emoji">💼</div>
              <h3 className="target-title">직장인 투자자</h3>
              <p className="target-description">
                "연말정산 때 놀라지 않고 싶어요"<br />
                미리미리 세금을 계산하고 준비하세요!
              </p>
            </div>
            <div className="target-card">
              <div className="target-emoji">📈</div>
              <h3 className="target-title">액티브 트레이더</h3>
              <p className="target-description">
                "거래량이 많아서 세금이 복잡해요"<br />
                실시간으로 세금 부담을 확인하세요!
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* MyData CTA Section */}
      <section className="mydata-section" id="mydata">
        <div className="container">
          <div className="mydata-content">
            <div className="mydata-text">
              <h2 className="mydata-title">
                <span className="mydata-icon">🔗</span>
                내 자산 연결하기
              </h2>
              <p className="mydata-description">
                증권사 계좌를 안전하게 연결하고<br />
                실시간으로 세금과 수익률을 확인하세요!
              </p>
              <ul className="mydata-benefits">
                <li>✅ 주요 증권사 모두 지원</li>
                <li>✅ 은행급 보안 시스템</li>
                <li>✅ 실시간 자동 업데이트</li>
                <li>✅ 완전 무료 서비스</li>
              </ul>
              <button className="mydata-cta-btn" onClick={() => setShowLoginModal(true)}>
                <span>🚀</span> 지금 바로 연결하기
              </button>
            </div>
            <div className="mydata-visual">
              <div className="mydata-cards">
                <div className="broker-card">
                  <div className="broker-logo">🏦</div>
                  <div className="broker-name">키움증권</div>
                  <div className="broker-status connected">연결됨</div>
                </div>
                <div className="broker-card">
                  <div className="broker-logo">🏛️</div>
                  <div className="broker-name">삼성증권</div>
                  <div className="broker-status connected">연결됨</div>
                </div>
                <div className="broker-card">
                  <div className="broker-logo">🏢</div>
                  <div className="broker-name">미래에셋</div>
                  <div className="broker-status">연결 가능</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Tax Saving Alert Section */}
      <section className="tax-saving-section">
        <div className="container">
          <div className="tax-saving-content">
            <div className="tax-saving-header">
              <h2 className="section-title">이번 달 절세 현황 📈</h2>
              <p className="section-subtitle">똑똑한 투자로 이만큼 아꼈어요!</p>
            </div>
            <div className="tax-saving-cards">
              <div className="saving-card main-card">
                <div className="saving-icon">💰</div>
                <div className="saving-title">이번 달 절세 금액</div>
                <div className="saving-amount">234,000원</div>
                <div className="saving-description">지난 달 대비 +15.2% 증가</div>
              </div>
              <div className="saving-card">
                <div className="saving-icon">📅</div>
                <div className="saving-title">연말까지 예상 절세</div>
                <div className="saving-amount">1,890,000원</div>
              </div>
              <div className="saving-card">
                <div className="saving-icon">🎯</div>
                <div className="saving-title">절세 목표 달성률</div>
                <div className="saving-amount">73.4%</div>
              </div>
            </div>
            <div className="tax-saving-alert">
              <div className="alert-content">
                <div className="alert-icon">🚨</div>
                <div className="alert-text">
                  <strong>연말 절세 알림!</strong><br />
                  올해 남은 기간 동안 추가로 456,000원을 더 절약할 수 있어요!
                </div>
                <button className="alert-cta">절세 전략 보기</button>
              </div>
        </div>
      </div>
        </div>
      </section>

      {/* Account Comparison Section */}
      <section className="comparison-section" id="comparison">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">계좌별 세금 비교 🏦</h2>
            <p className="section-subtitle">어떤 계좌가 가장 유리할까요?</p>
          </div>
          <div className="comparison-grid">
            <div className="comparison-card">
              <div className="account-header">
                <div className="account-icon">💳</div>
                <div className="account-name">일반 계좌</div>
                <div className="account-badge basic">기본</div>
              </div>
              <div className="account-features">
                <div className="feature-item">
                  <span className="feature-label">세율</span>
                  <span className="feature-value">20% (분리과세)</span>
                </div>
                <div className="feature-item">
                  <span className="feature-label">연간 한도</span>
                  <span className="feature-value">제한 없음</span>
                </div>
                <div className="feature-item">
                  <span className="feature-label">장점</span>
                  <span className="feature-value">자유로운 거래</span>
                </div>
              </div>
              <div className="account-tax">
                <div className="tax-label">예상 세금</div>
                <div className="tax-amount">490,000원</div>
              </div>
            </div>

            <div className="comparison-card recommended">
              <div className="account-header">
                <div className="account-icon">🌟</div>
                <div className="account-name">ISA 계좌</div>
                <div className="account-badge recommended">추천</div>
              </div>
              <div className="account-features">
                <div className="feature-item">
                  <span className="feature-label">세율</span>
                  <span className="feature-value">9.9% (우대)</span>
                </div>
                <div className="feature-item">
                  <span className="feature-label">연간 한도</span>
                  <span className="feature-value">2,000만원</span>
                </div>
                <div className="feature-item">
                  <span className="feature-label">장점</span>
                  <span className="feature-value">200만원 비과세</span>
                </div>
              </div>
              <div className="account-tax">
                <div className="tax-label">예상 세금</div>
                <div className="tax-amount">242,250원</div>
              </div>
              <div className="saving-badge">247,750원 절약!</div>
            </div>

            <div className="comparison-card">
              <div className="account-header">
                <div className="account-icon">🏛️</div>
                <div className="account-name">IRP 계좌</div>
                <div className="account-badge pension">연금</div>
              </div>
              <div className="account-features">
                <div className="feature-item">
                  <span className="feature-label">세율</span>
                  <span className="feature-value">3.3~5.5%</span>
                </div>
                <div className="feature-item">
                  <span className="feature-label">연간 한도</span>
                  <span className="feature-value">700만원</span>
                </div>
                <div className="feature-item">
                  <span className="feature-label">장점</span>
                  <span className="feature-value">세액공제</span>
                </div>
              </div>
              <div className="account-tax">
                <div className="tax-label">예상 세금</div>
                <div className="tax-amount">134,750원</div>
              </div>
      </div>

            <div className="comparison-card">
              <div className="account-header">
                <div className="account-icon">🎯</div>
                <div className="account-name">연금저축</div>
                <div className="account-badge pension">연금</div>
              </div>
              <div className="account-features">
                <div className="feature-item">
                  <span className="feature-label">세율</span>
                  <span className="feature-value">3.3~5.5%</span>
                </div>
                <div className="feature-item">
                  <span className="feature-label">연간 한도</span>
                  <span className="feature-value">600만원</span>
                </div>
                <div className="feature-item">
                  <span className="feature-label">장점</span>
                  <span className="feature-value">세액공제</span>
                </div>
              </div>
              <div className="account-tax">
                <div className="tax-label">예상 세금</div>
                <div className="tax-amount">134,750원</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="homepage-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <div className="footer-logo">
                <span className="logo-icon">📊</span>
                Stock D-TAX
              </div>
              <p className="footer-description">
                주식투자 세금 최적화의 새로운 기준
              </p>
            </div>
            <div className="footer-links">
              <div className="footer-section">
                <h4 className="footer-title">서비스</h4>
                <ul className="footer-list">
                  <li><a href="#calculator">세금 계산기</a></li>
                  <li><a href="#comparison">계좌 비교</a></li>
                  <li><a href="#mydata">자산 연결</a></li>
                  <li><a href="#consulting">AI 컨설팅</a></li>
                </ul>
              </div>
              <div className="footer-section">
                <h4 className="footer-title">고객센터</h4>
                <ul className="footer-list">
                  <li><a href="/faq">자주 묻는 질문</a></li>
                  <li><a href="/contact">문의하기</a></li>
                  <li><a href="/guide">이용 가이드</a></li>
                </ul>
              </div>
              <div className="footer-section">
                <h4 className="footer-title">정보</h4>
                <ul className="footer-list">
                  <li><a href="/about">회사 소개</a></li>
                  <li><a href="/privacy">개인정보처리방침</a></li>
                  <li><a href="/terms">이용약관</a></li>
                </ul>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2024 Stock D-TAX. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="modal-overlay">
          <div className="login-modal">
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
    </>
  );
}