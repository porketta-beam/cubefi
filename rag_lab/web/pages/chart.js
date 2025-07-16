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
  // 더미데이터
  const investLabels = ['국내주식', '해외주식', '예적금/채권', '펀드/ETF'];
  const investData = [30000000, 10000000, 15000000, 5000000];
  const profitData = [20500000, 2800000, 450000, 300000];
  const taxData = [3160000, 560000, 69300, 46200];

  const barData = {
    labels: investLabels,
    datasets: [
      {
        label: '투자금액',
        data: investData,
        backgroundColor: '#36a2eb',
      },
      {
        label: '실현수익',
        data: profitData,
        backgroundColor: '#2ee86c',
      },
      {
        label: '예상 세금',
        data: taxData,
        backgroundColor: '#ff6384',
      },
    ],
  };

  const barOptions = {
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
      <h1>투자/수익/세금 차트</h1>
      <div className="dashboard-cards">
        <div className="dashboard-card">
          <div className="card-title">총 투자금액</div>
          <div className="card-value">56,000,000원</div>
        </div>
        <div className="dashboard-card">
          <div className="card-title">총 실현수익</div>
          <div className="card-value">23,030,000원</div>
        </div>
        <div className="dashboard-card">
          <div className="card-title">예상 세금 합계</div>
          <div className="card-value warning">3,982,500원</div>
        </div>
      </div>
      <div className="chart-section">
        <h2>자산별 투자/수익/세금</h2>
        <Bar data={barData} options={barOptions} />
      </div>
      <div className="dashboard-alerts">
        <div className="alert warning">
          <b>국내주식 실현수익 2,000만원 초과!</b> 종합과세 구간 진입, 초과분 누진세율 적용.<br/>
          <span style={{color:'#2ee86c'}}>ISA 계좌 활용, 실현수익 분산 등 절세 전략을 추천드립니다.</span>
        </div>
        <div className="alert warning">
          <b>해외주식 실현수익 250만원 초과!</b> 초과분 20% 세율 적용.<br/>
          <span style={{color:'#2ee86c'}}>손실 종목 매도, 연도별 분산 매도 등 절세 전략을 활용하세요.</span>
        </div>
      </div>
    </div>
  );
} 