import { useState, useEffect } from 'react';
import Head from 'next/head';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import styles from '../styles/TaxCalculator.module.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function ChartPage() {
  const [activeTab, setActiveTab] = useState('foreign'); // 'foreign' or 'dividend'
  const [foreignStocks, setForeignStocks] = useState([]);
  const [dividendStocks, setDividendStocks] = useState([]);
  
  // 폼 상태
  const [newStock, setNewStock] = useState({
    name: '',
    ticker: '',
    avgPrice: '',
    currentPrice: '',
    quantity: '',
    realizedProfit: '', // 실현수익
    expectedDividend: '' // 예상배당 (배당주만)
  });

  // 계산 결과 상태
  const [calculations, setCalculations] = useState({
    foreign: {
      totalRealized: 0,
      totalUnrealized: 0,
      totalCombined: 0,
      taxableAmount: 0,
      tax: 0,
      afterTaxProfit: 0
    },
    dividend: {
      totalRealized: 0,
      totalExpected: 0,
      totalCombined: 0,
      taxableAmount: 0,
      tax: 0,
      afterTaxProfit: 0,
      isComprehensive: false
    }
  });

  // 경고 상태
  const [alerts, setAlerts] = useState([]);
  const [showStrategyModal, setShowStrategyModal] = useState(false); // 모달 상태 추가

  // 계산 함수
  const calculateTaxes = () => {
    // 해외주식 계산
    const foreignTotal = foreignStocks.reduce((acc, stock) => {
      const realized = parseFloat(stock.realizedProfit) || 0;
      const unrealized = (parseFloat(stock.currentPrice) - parseFloat(stock.avgPrice)) * parseFloat(stock.quantity) || 0;
      return {
        realized: acc.realized + realized,
        unrealized: acc.unrealized + unrealized,
        combined: acc.combined + realized + unrealized
      };
    }, { realized: 0, unrealized: 0, combined: 0 });

    const foreignTaxableAmount = Math.max(0, foreignTotal.combined - 2500000); // 250만원 공제
    const foreignTax = foreignTaxableAmount * 0.22; // 22% 세율

    // 배당주 계산
    const dividendTotal = dividendStocks.reduce((acc, stock) => {
      const realized = parseFloat(stock.realizedProfit) || 0;
      const expected = parseFloat(stock.expectedDividend) || 0;
      return {
        realized: acc.realized + realized,
        expected: acc.expected + expected,
        combined: acc.combined + realized + expected
      };
    }, { realized: 0, expected: 0, combined: 0 });

    const isComprehensive = dividendTotal.combined > 20000000; // 2000만원 초과시 종합과세
    const dividendTaxableAmount = Math.max(0, dividendTotal.combined - 20000000);
    const dividendTax = isComprehensive ? dividendTaxableAmount * 0.35 : dividendTotal.combined * 0.154; // 종합과세 35% vs 분리과세 15.4%

    // 계산 결과 업데이트
    setCalculations({
      foreign: {
        totalRealized: foreignTotal.realized,
        totalUnrealized: foreignTotal.unrealized,
        totalCombined: foreignTotal.combined,
        taxableAmount: foreignTaxableAmount,
        tax: foreignTax,
        afterTaxProfit: foreignTotal.combined - foreignTax
      },
      dividend: {
        totalRealized: dividendTotal.realized,
        totalExpected: dividendTotal.expected,
        totalCombined: dividendTotal.combined,
        taxableAmount: dividendTaxableAmount,
        tax: dividendTax,
        afterTaxProfit: dividendTotal.combined - dividendTax,
        isComprehensive
      }
    });

    // 경고 생성
    const newAlerts = [];
    
    if (foreignTotal.combined > 2000000) {
      newAlerts.push({
        type: 'warning',
        icon: '⚠️',
        text: `해외주식 수익이 250만원을 초과했습니다. 초과분 ${(foreignTotal.combined - 2500000).toLocaleString()}원에 대해 22% 세금이 부과됩니다.`
      });
    }

    if (dividendTotal.combined > 15000000) {
      newAlerts.push({
        type: 'warning',
        icon: '🚨',
        text: `배당수익이 1,500만원을 초과했습니다. 2,000만원 초과 시 종합과세 전환을 고려하세요.`
      });
    }

    if (isComprehensive) {
      newAlerts.push({
        type: 'warning',
        icon: '📊',
        text: `배당수익이 2,000만원을 초과하여 종합과세 대상입니다. 세율이 크게 증가할 수 있습니다.`
      });
    }

    if (newAlerts.length === 0) {
      newAlerts.push({
        type: 'info',
        icon: '✅',
        text: '현재 세금 부담이 최적화된 상태입니다.'
      });
    }

    setAlerts(newAlerts);
  };

  // 종목 추가
  const addStock = () => {
    if (!newStock.name || !newStock.avgPrice || !newStock.currentPrice || !newStock.quantity) {
      alert('필수 정보를 모두 입력해주세요.');
      return;
    }

    const stock = {
      id: Date.now(),
      ...newStock,
      avgPrice: parseFloat(newStock.avgPrice),
      currentPrice: parseFloat(newStock.currentPrice),
      quantity: parseFloat(newStock.quantity),
      realizedProfit: parseFloat(newStock.realizedProfit) || 0,
      expectedDividend: parseFloat(newStock.expectedDividend) || 0
    };

    if (activeTab === 'foreign') {
      setForeignStocks([...foreignStocks, stock]);
    } else {
      setDividendStocks([...dividendStocks, stock]);
    }

    // 폼 초기화
    setNewStock({
      name: '',
      ticker: '',
      avgPrice: '',
      currentPrice: '',
      quantity: '',
      realizedProfit: '',
      expectedDividend: ''
    });
  };

  // 종목 삭제
  const deleteStock = (id) => {
    if (activeTab === 'foreign') {
      setForeignStocks(foreignStocks.filter(stock => stock.id !== id));
    } else {
      setDividendStocks(dividendStocks.filter(stock => stock.id !== id));
    }
  };

  // 계산 트리거
  useEffect(() => {
    calculateTaxes();
  }, [foreignStocks, dividendStocks]);

  const currentStocks = activeTab === 'foreign' ? foreignStocks : dividendStocks;
  const currentCalc = calculations[activeTab];

  // 차트 데이터 준비 - 실시간 연동
  const dividendLimit = 20000000; // 2000만원 한도
  const foreignLimit = 2500000; // 250만원 한도
  
  // 실제 계산된 값 또는 최소 한도값 사용
  const dividendProfit = Math.max(calculations.dividend.totalCombined, dividendLimit);
  const dividendTax = calculations.dividend.tax;
  const dividendLabels = ['배당소득 현황'];

  const isOverDividend = calculations.dividend.totalCombined > dividendLimit;
  const dividendBarData = {
    labels: dividendLabels,
    datasets: isOverDividend
      ? [
          {
            label: '종합과세 대상액',
            data: [calculations.dividend.totalCombined],
            backgroundColor: '#ff6384',
            borderRadius: 6,
            barThickness: 100,
            stack: 'total',
          },
        ]
      : [
          {
            label: '현재 배당수익',
            data: [calculations.dividend.totalCombined],
            backgroundColor: '#36a2eb',
            borderRadius: 6,
            barThickness: 100,
            stack: 'total',
          },
          {
            label: '분리과세 가능액',
            data: [dividendLimit - calculations.dividend.totalCombined],
            backgroundColor: '#2ee86c88',
            borderRadius: 6,
            barThickness: 100,
            stack: 'total',
          },
        ],
  };

  // 양도소득세 차트 데이터 - 실시간 연동
  const transferProfit = Math.max(calculations.foreign.totalCombined, foreignLimit);
  const transferTax = calculations.foreign.tax;
  const transferLabels = ['해외주식 현황'];
  
  const isOverForeign = calculations.foreign.totalCombined > foreignLimit;
  const transferBarData = {
    labels: transferLabels,
    datasets: isOverForeign
      ? [
      {
            label: '과세 대상액',
            data: [calculations.foreign.totalCombined - foreignLimit],
        backgroundColor: '#ff6384',
        borderRadius: 6,
        barThickness: 100,
        stack: 'total',
      },
      {
            label: '비과세 한도',
            data: [foreignLimit],
            backgroundColor: '#2ee86c88',
            borderRadius: 6,
            barThickness: 100,
            stack: 'total',
          },
        ]
      : [
          {
            label: '현재 수익',
            data: [calculations.foreign.totalCombined],
            backgroundColor: '#36a2eb',
            borderRadius: 6,
            barThickness: 100,
            stack: 'total',
          },
          {
            label: '비과세 가능액',
            data: [foreignLimit - calculations.foreign.totalCombined],
        backgroundColor: '#2ee86c88',
        borderRadius: 6,
        barThickness: 100,
        stack: 'total',
      },
    ],
  };
  
  const accountBarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#fff',
          font: { size: 14, weight: '600' },
          padding: 20,
          usePointStyle: true,
          pointStyle: 'rectRounded',
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(46, 232, 108, 0.3)',
        borderWidth: 1,
        cornerRadius: 8,
        callbacks: {
          label: function (context) {
            const value = context.raw?.toLocaleString() ?? '';
            return `${context.dataset.label}: ₩${value}`;
          },
        },
        titleFont: { size: 14, weight: '600' },
        bodyFont: { size: 13 },
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        ticks: {
          color: '#b0b8c1',
          font: { size: 11 },
          callback: function(value) {
            if (value === 0) return '₩0';
            if (value >= 1000000) {
              return `₩${(value / 10000).toFixed(0)}만`;
            }
            return `₩${value.toLocaleString()}`;
          },
        },
        grid: { 
          color: 'rgba(255,255,255,0.05)',
          lineWidth: 1,
        },
        border: {
          color: 'rgba(255,255,255,0.1)',
        },
      },
      y: {
        ticks: {
          display: false,
        },
        grid: { 
          display: false,
        },
        border: {
          display: false,
        },
      },
    },
  };

  // 배당소득세 차트 옵션 (동적 스케일)
  const dividendBarOptions = {
    ...accountBarOptions,
    scales: {
      ...accountBarOptions.scales,
      x: {
        ...accountBarOptions.scales.x,
        stacked: true,
        max: Math.max(dividendProfit, dividendLimit * 1.2),
        ticks: {
          ...accountBarOptions.scales.x.ticks,
          callback: function(value) {
            if (value === 0 || value === dividendLimit || value === dividendProfit) {
              return `₩${value.toLocaleString()}`;
            }
            return '';
          },
        },
      },
      y: {
        ...accountBarOptions.scales.y,
        stacked: true,
      },
    },
  };

  // 양도소득세 차트 옵션 (동적 스케일)
  const transferBarOptions = {
    ...accountBarOptions,
    scales: {
      ...accountBarOptions.scales,
      x: {
        ...accountBarOptions.scales.x,
        stacked: true,
        max: Math.max(transferProfit, foreignLimit * 1.2),
        ticks: {
          ...accountBarOptions.scales.x.ticks,
          callback: function(value) {
            if (value === 0 || value === foreignLimit || value === transferProfit) {
              return `₩${value.toLocaleString()}`;
            }
            return '';
          },
        },
      },
      y: {
        ...accountBarOptions.scales.y,
        stacked: true,
      },
    },
  };

  return (
    <>
      <Head>
        <title>세금 계산기 - Stock D-TAX</title>
        <meta name="description" content="보유 포지션까지 포함한 통합 세금 계산기" />
      </Head>

      <div className={styles.taxCalculatorContainer}>
        <h1 className={styles.pageTitle}>통합 세금 계산기</h1>
        
        {/* 통합 세금 정보 및 현황 카드 */}
        <div className={styles.infoCardsSection}>
          <div className={styles.infoCard}>
            <div className={styles.infoCardHeader}>
              <span className={styles.infoCardIcon}>🌍</span>
              <h3 className={styles.infoCardTitle}>해외주식 양도소득세</h3>
            </div>
            <div className={styles.infoCardContent}>
              {/* 현재 상태 배지 - 한도 정보 포함 */}
              <div className={`${styles.statusBadge} ${isOverForeign ? styles.danger : styles.safe}`} style={{margin: '20px 0'}}>
                <span className={styles.statusIcon}>{isOverForeign ? '⚠️' : '✅'}</span>
                <div className={styles.statusContent}>
                  <span className={styles.statusText}>
                    {isOverForeign 
                      ? '과세 대상 (초과분 22% 세율)'
                      : '비과세 한도 내 (세금 없음)'
                    }
                  </span>
                  <span className={styles.statusLimit}>연간 250만원</span>
                </div>
              </div>

              {/* 현재 수익 통계 */}
              <div className={styles.chartStats} style={{margin: '20px 0'}}>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>현재 총수익</span>
                  <span className={styles.statValue}>
                    {calculations.foreign.totalCombined.toLocaleString()}원
                  </span>
                </div>
                <div className={styles.statDivider}></div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>한도</span>
                  <span className={`${styles.statValue} ${styles.limit}`}>
                    250만원
                  </span>
                </div>
              </div>

              {/* 차트 */}
              <div className={styles.chartWrapper}>
                <Bar data={transferBarData} options={transferBarOptions} />
              </div>
              
              {/* 설명 */}
              <p className={styles.infoDescription}>
                해외주식 매매로 발생한 <strong>실현손익 + 미실현손익</strong>이 연간 250만원을 초과하는 경우, 
                초과분에 대해 <strong>22% 세율</strong>이 적용됩니다.
              </p>
              
              <div className={styles.strategyButtonWrapper}>
                <button className={styles.strategyButton} onClick={() => setShowStrategyModal(true)}>
                  절세 전략 확인하기
                </button>
              </div>
            </div>
          </div>

          <div className={styles.infoCard}>
            <div className={styles.infoCardHeader}>
              <span className={styles.infoCardIcon}>💰</span>
              <h3 className={styles.infoCardTitle}>배당소득세</h3>
            </div>
            <div className={styles.infoCardContent}>
              {/* 현재 상태 배지 - 한도 정보 포함 */}
              <div className={`${styles.statusBadge} ${isOverDividend ? styles.danger : styles.safe}`} style={{margin: '20px 0'}}>
                <span className={styles.statusIcon}>{isOverDividend ? '⚠️' : '✅'}</span>
                <div className={styles.statusContent}>
                  <span className={styles.statusText}>
                    {isOverDividend 
                      ? '종합과세 대상 (누진세율 적용)'
                      : '분리과세 적용 중 (세율 15.4%)'
                    }
                  </span>
                  <span className={styles.statusLimit}>연간 2,000만원</span>
                </div>
              </div>

              {/* 현재 수익 통계 */}
              <div className={styles.chartStats} style={{margin: '20px 0'}}>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>현재 배당수익</span>
                  <span className={styles.statValue}>
                    {calculations.dividend.totalCombined.toLocaleString()}원
                  </span>
                </div>
                <div className={styles.statDivider}></div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>한도</span>
                  <span className={`${styles.statValue} ${styles.limit}`}>
                    2,000만원
                  </span>
                </div>
              </div>

              {/* 차트 */}
              <div className={styles.chartWrapper}>
        <Bar data={dividendBarData} options={dividendBarOptions} />
      </div>
              
              {/* 설명 */}
              <p className={styles.infoDescription}>
                배당수익이 연간 2,000만원을 초과하면 <strong>종합과세</strong> 대상이 되어 
                다른 소득과 합산하여 <strong>누진세율(최대 45%)</strong>이 적용됩니다.
              </p>
              
              {/* 과세 방식 설명 */}
              <div className={styles.taxMethods}>
                <div className={styles.taxMethod}>
                  <h5>📊 분리과세 (2,000만원 이하)</h5>
                  <p>배당소득세 15.4% (소득세 14% + 지방소득세 1.4%)</p>
                </div>
                <div className={styles.taxMethod}>
                  <h5>📈 종합과세 (2,000만원 초과)</h5>
                  <p>다른 소득과 합산하여 누진세율 적용 (최대 45%)</p>
                </div>
              </div>
            
              <div className={styles.strategyButtonWrapper}>
                <button className={styles.strategyButton} onClick={() => setShowStrategyModal(true)}>
                  절세 전략 확인하기
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div className={styles.mainLayout}>
          {/* 현황 대시보드 */}
          <div className={styles.statusDashboard}>
            <h2 className={styles.dashboardTitle}>실시간 세금 현황</h2>
            
            <div className={styles.statusCards}>
              <div className={`${styles.statusCard} ${calculations.foreign.totalCombined > 2500000 ? styles.warning : styles.safe}`}>
                <div className={styles.cardLabel}>해외주식 총수익</div>
                <div className={`${styles.cardValue} ${calculations.foreign.totalCombined > 2500000 ? styles.warning : styles.safe}`}>
                  {calculations.foreign.totalCombined.toLocaleString()}원
                </div>
                <div className={styles.cardSubtext}>
                  한도: 250만원 / 세율: 22%
                </div>
              </div>
              
              <div className={`${styles.statusCard} ${calculations.dividend.isComprehensive ? styles.warning : styles.safe}`}>
                <div className={styles.cardLabel}>배당 총수익</div>
                <div className={`${styles.cardValue} ${calculations.dividend.isComprehensive ? styles.danger : styles.safe}`}>
                  {calculations.dividend.totalCombined.toLocaleString()}원
                </div>
                <div className={styles.cardSubtext}>
                  {calculations.dividend.isComprehensive ? '종합과세 대상' : '분리과세 적용'}
                </div>
              </div>
            </div>

            {/* 경고 섹션 */}
            <div className={styles.alertSection}>
              {alerts.map((alert, index) => (
                <div key={index} className={`${styles.alertItem} ${styles[alert.type]}`}>
                  <span className={styles.alertIcon}>{alert.icon}</span>
                  <span className={styles.alertText}>{alert.text}</span>
                </div>
              ))}
            </div>

            {/* 총 세후 수익 */}
            <div className={styles.statusCard}>
              <div className={styles.cardLabel}>총 세후 수익</div>
              <div className={`${styles.cardValue} ${styles.safe}`}>
                {(calculations.foreign.afterTaxProfit + calculations.dividend.afterTaxProfit).toLocaleString()}원
              </div>
              <div className={styles.cardSubtext}>
                세금: {(calculations.foreign.tax + calculations.dividend.tax).toLocaleString()}원
              </div>
            </div>
          </div>

          {/* 입력 섹션 */}
          <div className={styles.inputSection}>
            <h2 className={styles.sectionTitle}>
              📊 종목 관리
            </h2>
            
            <div className={styles.tabButtons}>
              <button 
                className={`${styles.tabButton} ${activeTab === 'foreign' ? styles.active : ''}`}
                onClick={() => setActiveTab('foreign')}
              >
                🌎 해외주식
              </button>
              <button 
                className={`${styles.tabButton} ${activeTab === 'dividend' ? styles.active : ''}`}
                onClick={() => setActiveTab('dividend')}
              >
                💰 배당주
              </button>
            </div>

            <div className={styles.stockForm}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>종목명</label>
                <input
                  type="text"
                  className={styles.formInput}
                  value={newStock.name}
                  onChange={(e) => setNewStock({...newStock, name: e.target.value})}
                  placeholder="삼성전자"
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>티커</label>
                <input
                  type="text"
                  className={styles.formInput}
                  value={newStock.ticker}
                  onChange={(e) => setNewStock({...newStock, ticker: e.target.value})}
                  placeholder="005930"
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>평균단가</label>
                <input
                  type="number"
                  className={styles.formInput}
                  value={newStock.avgPrice}
                  onChange={(e) => setNewStock({...newStock, avgPrice: e.target.value})}
                  placeholder="65000"
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>현재가</label>
                <input
                  type="number"
                  className={styles.formInput}
                  value={newStock.currentPrice}
                  onChange={(e) => setNewStock({...newStock, currentPrice: e.target.value})}
                  placeholder="68000"
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>보유수량</label>
                <input
                  type="number"
                  className={styles.formInput}
                  value={newStock.quantity}
                  onChange={(e) => setNewStock({...newStock, quantity: e.target.value})}
                  placeholder="100"
                />
              </div>
              
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>실현수익</label>
                <input
                  type="number"
                  className={styles.formInput}
                  value={newStock.realizedProfit}
                  onChange={(e) => setNewStock({...newStock, realizedProfit: e.target.value})}
                  placeholder="1000000"
                />
              </div>
              
              {activeTab === 'dividend' && (
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>예상배당</label>
                  <input
                    type="number"
                    className={styles.formInput}
                    value={newStock.expectedDividend}
                    onChange={(e) => setNewStock({...newStock, expectedDividend: e.target.value})}
                    placeholder="500000"
                  />
                </div>
              )}
            </div>

            <div className={styles.formActions}>
              <button className={styles.addButton} onClick={addStock}>
                종목 추가
              </button>
              <button 
                className={styles.clearButton} 
                onClick={() => activeTab === 'foreign' ? setForeignStocks([]) : setDividendStocks([])}
              >
                전체 삭제
              </button>
            </div>
          </div>
      </div>
      
        {/* 보유 종목 테이블 */}
        <div className={styles.holdingsSection}>
          <h2 className={styles.sectionTitle}>
            📈 {activeTab === 'foreign' ? '해외주식' : '배당주'} 보유 현황
          </h2>
          
          <div className={styles.holdingsTable}>
            <table>
              <thead>
                <tr>
                  <th>종목정보</th>
                  <th>평균단가</th>
                  <th>현재가</th>
                  <th>보유수량</th>
                  <th>실현수익</th>
                  <th>평가차익</th>
                  {activeTab === 'dividend' && <th>예상배당</th>}
                  <th>총 수익</th>
                  <th>예상세금</th>
                  <th>관리</th>
                </tr>
              </thead>
              <tbody>
                {currentStocks.map((stock) => {
                  const unrealizedProfit = (stock.currentPrice - stock.avgPrice) * stock.quantity;
                  const totalProfit = stock.realizedProfit + unrealizedProfit + (stock.expectedDividend || 0);
                  const taxRate = activeTab === 'foreign' ? 0.22 : (calculations.dividend.isComprehensive ? 0.35 : 0.154);
                  const estimatedTax = Math.max(0, totalProfit - (activeTab === 'foreign' ? 2500000 : 20000000)) * taxRate;
                  
                  return (
                    <tr key={stock.id}>
                      <td>
                        <div className={styles.stockInfo}>
                          <div className={styles.stockName}>{stock.name}</div>
                          <div className={styles.stockTicker}>{stock.ticker}</div>
                        </div>
                      </td>
                      <td>{stock.avgPrice.toLocaleString()}원</td>
                      <td>{stock.currentPrice.toLocaleString()}원</td>
                      <td>{stock.quantity.toLocaleString()}주</td>
                      <td>
                        <span className={`${styles.profitCell} ${stock.realizedProfit >= 0 ? styles.positive : styles.negative}`}>
                          {stock.realizedProfit.toLocaleString()}원
                        </span>
                      </td>
                      <td>
                        <span className={`${styles.profitCell} ${unrealizedProfit >= 0 ? styles.positive : styles.negative}`}>
                          {unrealizedProfit.toLocaleString()}원
                        </span>
                      </td>
                      {activeTab === 'dividend' && (
                        <td>
                          <span className={`${styles.profitCell} ${styles.positive}`}>
                            {stock.expectedDividend.toLocaleString()}원
                          </span>
                        </td>
                      )}
                      <td>
                        <span className={`${styles.profitCell} ${totalProfit >= 0 ? styles.positive : styles.negative}`}>
                          {totalProfit.toLocaleString()}원
                        </span>
                      </td>
                      <td>
                        <span className={`${styles.taxCell} ${estimatedTax > 0 ? styles.high : styles.normal}`}>
                          {estimatedTax.toLocaleString()}원
                        </span>
                      </td>
                      <td className={styles.actionCell}>
                        <button 
                          className={styles.deleteButton}
                          onClick={() => deleteStock(stock.id)}
                        >
                          삭제
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {currentStocks.length === 0 && (
                  <tr>
                    <td colSpan={activeTab === 'dividend' ? "10" : "9"} style={{textAlign: 'center', padding: '40px', color: '#888'}}>
                      등록된 종목이 없습니다. 위에서 종목을 추가해주세요.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 시뮬레이션 결과 */}
        <div className={styles.simulationSection}>
          <h2 className={styles.sectionTitle}>
            🎯 세금 시뮬레이션 결과
          </h2>
          
          <div className={styles.simulationGrid}>
            <div className={`${styles.simulationCard} ${styles.foreign}`}>
              <h3 className={styles.simulationCardTitle}>
                🌎 해외주식 세금 분석
              </h3>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>실현수익</span>
                <span className={styles.simulationValue}>{calculations.foreign.totalRealized.toLocaleString()}원</span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>평가차익 (보유분)</span>
                <span className={styles.simulationValue}>{calculations.foreign.totalUnrealized.toLocaleString()}원</span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>총 잠정수익</span>
                <span className={styles.simulationValue}>{calculations.foreign.totalCombined.toLocaleString()}원</span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>과세 대상액</span>
                <span className={`${styles.simulationValue} ${calculations.foreign.taxableAmount > 0 ? styles.warning : styles.safe}`}>
                  {calculations.foreign.taxableAmount.toLocaleString()}원
                </span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>예상 세금 (22%)</span>
                <span className={`${styles.simulationValue} ${calculations.foreign.tax > 0 ? styles.warning : styles.safe}`}>
                  {calculations.foreign.tax.toLocaleString()}원
                </span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>세후 수익</span>
                <span className={styles.simulationValue}>{calculations.foreign.afterTaxProfit.toLocaleString()}원</span>
              </div>
            </div>

            <div className={`${styles.simulationCard} ${styles.dividend}`}>
              <h3 className={styles.simulationCardTitle}>
                💰 배당주 세금 분석
              </h3>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>실현 배당수익</span>
                <span className={styles.simulationValue}>{calculations.dividend.totalRealized.toLocaleString()}원</span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>예상 배당수익</span>
                <span className={styles.simulationValue}>{calculations.dividend.totalExpected.toLocaleString()}원</span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>총 배당수익</span>
                <span className={styles.simulationValue}>{calculations.dividend.totalCombined.toLocaleString()}원</span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>과세 방식</span>
                <span className={`${styles.simulationValue} ${calculations.dividend.isComprehensive ? styles.warning : styles.safe}`}>
                  {calculations.dividend.isComprehensive ? '종합과세' : '분리과세'}
                </span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>예상 세금</span>
                <span className={`${styles.simulationValue} ${calculations.dividend.tax > 0 ? styles.warning : styles.safe}`}>
                  {calculations.dividend.tax.toLocaleString()}원
                </span>
              </div>
              <div className={styles.simulationRow}>
                <span className={styles.simulationLabel}>세후 수익</span>
                <span className={styles.simulationValue}>{calculations.dividend.afterTaxProfit.toLocaleString()}원</span>
              </div>
            </div>
          </div>
      </div>
      {/* 절세 전략 모달 */}
      {showStrategyModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'rgba(24,26,32,0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }}
          onClick={() => setShowStrategyModal(false)}
        >
          <div style={{
            background: '#23262f',
            borderRadius: 12,
            padding: '40px 32px',
            minWidth: 320,
            maxWidth: '90vw',
            color: '#fff',
            textAlign: 'center',
            position: 'relative',
            boxShadow: '0 4px 24px rgba(0,0,0,0.18)'
          }}
            onClick={e => e.stopPropagation()}
          >
            <h2 style={{color:'#2ee86c', marginBottom: '18px'}}>절세 전략</h2>
            <div style={{marginBottom: '32px'}}>여기에 절세 전략 내용 작성하기!</div>
            <button style={{
              background: '#2ee86c',
              color: '#181a20',
              border: 'none',
              borderRadius: 6,
              padding: '10px 32px',
              fontSize: '1rem',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'background 0.18s',
            }}
              onClick={() => setShowStrategyModal(false)}
            >
              닫기
            </button>
          </div>
        </div>
      )}
      </div>
    </>
  );
}