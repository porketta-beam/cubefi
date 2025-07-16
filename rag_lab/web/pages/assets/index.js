import { useState } from 'react';
import AssetsDashboard from '../../components/assets/AssetsDashboard';
import DomesticStocks from '../../components/assets/DomesticStocks';
import ForeignStocks from '../../components/assets/ForeignStocks';
import DividendStocks from '../../components/assets/DividendStocks';
import ISAAccount from '../../components/assets/ISAAccount';
import IRPAccount from '../../components/assets/IRPAccount';
import PensionAccount from '../../components/assets/PensionAccount';

export default function Assets() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
<<<<<<< HEAD:ai/web/pages/assets/index.js
    { id: 'dashboard', name: '내 자산 요약' },
=======
    { id: 'dashboard', name: '대시보드' },
>>>>>>> origin/cbo:rag_lab/web/pages/assets/index.js
    { id: 'domestic', name: '국내주식' },
    { id: 'foreign', name: '해외주식' },
    { id: 'dividend', name: '배당주' },
    { id: 'isa', name: 'ISA 계좌' },
    { id: 'irp', name: 'IRP 계좌' },
    { id: 'pension', name: '연금저축계좌' }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <AssetsDashboard />;
      case 'domestic':
        return <DomesticStocks />;
      case 'foreign':
        return <ForeignStocks />;
      case 'dividend':
        return <DividendStocks />;
      case 'isa':
        return <ISAAccount />;
      case 'irp':
        return <IRPAccount />;
      case 'pension':
        return <PensionAccount />;
      default:
        return <AssetsDashboard />;
    }
  };

  // 이주현 더미데이터
  const user = {
    name: '이주현',
    age: 30,
    job: 'IT 기업 대리',
    salary: 3500000,
    salaryYear: 42000000,
    risk: '중립(위험과 안정 병행)',
    experience: '5년(국내주식, 해외주식, 펀드, 예적금)',
    goal: '아파트 구매 자금 준비',
    interest: '세금 부담 최소화, 실질 수익 극대화, 절세 전략'
  };

  return (
<<<<<<< HEAD:ai/web/pages/assets/index.js
    <div className="dashboard-container">
      <div className="assets-header">
        <h1>내 자산</h1>
        <p>보유하고 있는 모든 금융상품을 한눈에 확인하세요</p>
        <br></br>
=======
    <div className="assets-container">
      <div className="assets-header">
        <h1>내 자산</h1>
        <p>보유하고 있는 모든 금융상품을 한눈에 확인하세요</p>
>>>>>>> origin/cbo:rag_lab/web/pages/assets/index.js
      </div>
      <div className="user-summary-cards">
        <div className="user-card">
          <div className="user-avatar">👤</div>
          <div>
            <div className="user-name">{user.name} <span className="user-age">({user.age}세)</span></div>
            <div className="user-job">{user.job}</div>
          </div>
        </div>
        <div className="user-card">
          <div className="user-label">월급(세전)</div>
          <div className="user-value">{user.salary.toLocaleString()}원</div>
          <div className="user-label">연봉</div>
          <div className="user-value">{user.salaryYear.toLocaleString()}원</div>
        </div>
        <div className="user-card">
          <div className="user-label">투자성향</div>
          <div className="user-value">{user.risk}</div>
          <div className="user-label">경험</div>
          <div className="user-value">{user.experience}</div>
        </div>
        <div className="user-card">
          <div className="user-label">목표</div>
          <div className="user-value">{user.goal}</div>
          <div className="user-label">관심사</div>
          <div className="user-value">{user.interest}</div>
        </div>
      </div>
      <div className="assets-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.name}
          </button>
        ))}
      </div>
      <div className="assets-content">
        {renderContent()}
      </div>
    </div>
  );
} 