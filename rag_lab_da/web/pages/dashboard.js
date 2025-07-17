import { useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function Home() {
  // 더미데이터 (이주현)
  const realizedProfit = 20500000; // 국내주식 실현수익
  const realizedProfitLimit = 20000000;
  const foreignProfit = 2800000; // 해외주식 실현수익
  const foreignLimit = 2500000;
  const warning = realizedProfit > realizedProfitLimit;
  const foreignWarning = foreignProfit > foreignLimit;

  const chartData = {
    labels: ['2025-01', '2025-03', '2025-06', '2025-09', '2025-12'],
    datasets: [
      {
        label: '국내주식 실현수익',
        data: [0, 11000000, 11000000, 20500000, 20500000],
        borderColor: warning ? '#ff6384' : '#2ee86c',
        backgroundColor: 'rgba(255,99,132,0.1)',
        fill: false,
        tension: 0.3,
      },
      {
        label: '해외주식 실현수익',
        data: [0, 0, 2000000, 2800000, 2800000],
        borderColor: foreignWarning ? '#ffce56' : '#36a2eb',
        backgroundColor: 'rgba(54,162,235,0.1)',
        borderDash: [5, 5],
        fill: false,
        tension: 0.3,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#fff' },
      },
      title: { display: false },
    },
    scales: {
      x: {
        ticks: { color: '#fff' },
        grid: { color: 'rgba(255,255,255,0.08)' },
      },
      y: {
        ticks: { color: '#fff' },
        grid: { color: 'rgba(255,255,255,0.08)' },
      },
    },
  };

  return (
    <div className="dashboard-container">
      <h1>Stock D-TAX 대시보드</h1>
      <div className="dashboard-cards">
        <div className="dashboard-card">
          <div className="card-title">국내주식 실현수익</div>
          <div className={`card-value ${warning ? 'warning' : ''}`}>{realizedProfit.toLocaleString()}원</div>
          <div className="card-desc">분리과세 한도: 20,000,000원</div>
        </div>
        <div className="dashboard-card">
          <div className="card-title">해외주식 실현수익</div>
          <div className={`card-value ${foreignWarning ? 'warning' : ''}`}>{foreignProfit.toLocaleString()}원</div>
          <div className="card-desc">비과세 한도: 2,500,000원</div>
        </div>
        <div className="dashboard-card">
          <div className="card-title">근로소득(연)</div>
          <div className="card-value">42,000,000원</div>
          <div className="card-desc">월급(세전): 3,500,000원</div>
        </div>
        <div className="dashboard-card">
          <div className="card-title">투자 목표</div>
          <div className="card-value">아파트 구매</div>
          <div className="card-desc">세금 부담 최소화, 실질 수익 극대화</div>
        </div>
      </div>

      <div className="chart-section">
        <h2>실현수익 추이</h2>
        <Line data={chartData} options={chartOptions} />
        <div className="tax-threshold">
          {warning && (
            <span style={{color:'#ff6384',fontWeight:'bold'}}>분리과세 임계점 초과! 종합과세 구간 진입</span>
          )}
          {!warning && (
            <span>분리과세 임계점: 20,000,000원</span>
          )}
        </div>
        {foreignWarning && (
          <div className="tax-threshold" style={{color:'#ffce56',marginTop:8}}>
            해외주식 비과세 한도 초과! 20% 세율 적용
          </div>
        )}
      </div>

      <div className="dashboard-alerts">
        {warning && (
          <div className="alert warning">
            <b>종합과세 구간 진입!</b> 초과분은 근로소득과 합산해 누진세율(6.6~49.5%)이 적용됩니다.<br/>
            <span style={{color:'#2ee86c'}}>ISA 계좌 활용, 실현수익 분산 등 절세 전략을 추천드립니다.</span>
          </div>
        )}
        {foreignWarning && (
          <div className="alert warning">
            <b>해외주식 실현수익 250만원 초과!</b> 초과분은 20% 세율이 적용됩니다.<br/>
            <span style={{color:'#2ee86c'}}>손실 종목 매도, 연도별 분산 매도 등 절세 전략을 활용하세요.</span>
          </div>
        )}
      </div>
    </div>
  );
} 