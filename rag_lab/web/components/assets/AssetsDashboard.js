import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function AssetsDashboard() {
  // 예시 데이터
  const assetData = {
    labels: ['국내주식', '해외주식', '배당주', 'ISA 계좌', 'IRP 계좌', '연금저축계좌'],
    datasets: [
      {
        data: [30000000, 10000000, 5000000, 7000000, 6000000, 3000000],
        backgroundColor: [
          '#2ee86c',
          '#36A2EB',
          '#FFCE56',
          '#4BC0C0',
          '#9966FF',
          '#FF9F40'
        ],
        borderWidth: 2,
        borderColor: '#181a20'
      }
    ]
  };

  const totalAssets = assetData.datasets[0].data.reduce((sum, value) => sum + value, 0);

  const assetSummary = [
    {
      category: '국내주식',
      amount: 30000000,
      percentage: ((30000000 / totalAssets) * 100).toFixed(1),
      change: '+2.5%',
      color: '#2ee86c'
    },
    {
      category: '해외주식',
      amount: 10000000,
      percentage: ((10000000 / totalAssets) * 100).toFixed(1),
      change: '+1.8%',
      color: '#36A2EB'
    },
    {
      category: '배당주',
      amount: 5000000,
      percentage: ((5000000 / totalAssets) * 100).toFixed(1),
      change: '+0.5%',
      color: '#FFCE56'
    },
    {
      category: 'ISA 계좌',
      amount: 7000000,
      percentage: ((7000000 / totalAssets) * 100).toFixed(1),
      change: '+0.2%',
      color: '#4BC0C0'
    },
    {
      category: 'IRP 계좌',
      amount: 6000000,
      percentage: ((6000000 / totalAssets) * 100).toFixed(1),
      change: '+0.1%',
      color: '#9966FF'
    },
    {
      category: '연금저축계좌',
      amount: 3000000,
      percentage: ((3000000 / totalAssets) * 100).toFixed(1),
      change: '+0.3%',
      color: '#FF9F40'
    }
  ];

  return (
    <div className="assets-dashboard domino-assets-layout">
      <div className="domino-assets-main">
        <div className="domino-assets-cards">
          <div className="domino-assets-card">
            <div className="domino-assets-card-title">총 자산</div>
            <div className="domino-assets-card-value">{totalAssets.toLocaleString()}원</div>
            <div className="domino-assets-card-desc">이번 달 +4.1%</div>
          </div>
          <div className="domino-assets-card">
            <div className="domino-assets-card-title">국내주식</div>
            <div className="domino-assets-card-value">{assetSummary[0].amount.toLocaleString()}원</div>
            <div className="domino-assets-card-desc">{assetSummary[0].percentage}%</div>
          </div>
          <div className="domino-assets-card">
            <div className="domino-assets-card-title">해외주식</div>
            <div className="domino-assets-card-value">{assetSummary[1].amount.toLocaleString()}원</div>
            <div className="domino-assets-card-desc">{assetSummary[1].percentage}%</div>
          </div>
          <div className="domino-assets-card">
            <div className="domino-assets-card-title">배당주</div>
            <div className="domino-assets-card-value">{assetSummary[2].amount.toLocaleString()}원</div>
            <div className="domino-assets-card-desc">{assetSummary[2].percentage}%</div>
          </div>
        </div>
        <div className="domino-assets-summary">
          <h3>자산별 상세</h3>
          <div className="domino-assets-summary-list">
            {assetSummary.map((asset, index) => (
              <div key={index} className="domino-assets-summary-item">
                <span className="domino-assets-dot" style={{background: asset.color}}></span>
                <span className="domino-assets-summary-name">{asset.category}</span>
                <span className="domino-assets-summary-amount">{asset.amount.toLocaleString()}원</span>
                <span className="domino-assets-summary-per">{asset.percentage}%</span>
                <span className={`domino-assets-summary-change ${asset.change.startsWith('+') ? 'positive' : 'negative'}`}>{asset.change}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="domino-assets-chart">
        <h3>자산 분포</h3>
        <div className="domino-assets-chart-inner">
          <Doughnut 
            data={assetData}
            options={{
              responsive: true,
              cutout: '70%',
              plugins: {
                legend: {
                  display: false
                }
              }
            }}
          />
        </div>
      </div>
    </div>
  );
} 