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
import annotationPlugin from 'chartjs-plugin-annotation';


ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  annotationPlugin
);

// 임계점 기준으로 데이터 분할 함수
const splitDataByThreshold = (data, threshold) => {
  const beforeThreshold = [];
  const afterThreshold = [];
  
  data.forEach((value, index) => {
    if (value <= threshold) {
      beforeThreshold.push(value);
      afterThreshold.push(null);
    } else {
      beforeThreshold.push(null);
      afterThreshold.push(value);
    }
  });
  
  return { beforeThreshold, afterThreshold };
};

const domesticData = [500, 1500, 2200, 1900];
const foreignData = [100, 200, 300, 280];

const domesticSplit = splitDataByThreshold(domesticData, 2000);
const foreignSplit = splitDataByThreshold(foreignData, 250);

const data = {
  labels: ['1월', '2월', '3월', '4월'],
  datasets: [
    // 국내주식 - 임계점 이하
    {
      label: '국내주식 실현이익 (임계점 이하)',
      data: domesticSplit.beforeThreshold,
      borderColor: '#4CAF50',
      backgroundColor: 'rgba(76, 175, 80, 0.1)',
      fill: false,
      borderWidth: 3,
      pointRadius: 6,
      pointHoverRadius: 8,
    },
    // 국내주식 - 임계점 초과
    {
      label: '국내주식 실현이익 (임계점 초과)',
      data: domesticSplit.afterThreshold,
      borderColor: '#F44336',
      backgroundColor: 'rgba(244, 67, 54, 0.1)',
      fill: false,
      borderWidth: 3,
      pointRadius: 6,
      pointHoverRadius: 8,
    },
    // 해외주식 - 임계점 이하
    {
      label: '해외주식 실현이익 (임계점 이하)',
      data: foreignSplit.beforeThreshold,
      borderColor: '#2196F3',
      backgroundColor: 'rgba(33, 150, 243, 0.1)',
      fill: false,
      borderWidth: 3,
      borderDash: [5, 5],
      pointRadius: 6,
      pointHoverRadius: 8,
    },
    // 해외주식 - 임계점 초과
    {
      label: '해외주식 실현이익 (임계점 초과)',
      data: foreignSplit.afterThreshold,
      borderColor: '#FF9800',
      backgroundColor: 'rgba(255, 152, 0, 0.1)',
      fill: false,
      borderWidth: 3,
      borderDash: [5, 5],
      pointRadius: 6,
      pointHoverRadius: 8,
    },
  ],
};

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        color: '#fff',
        usePointStyle: true,
        padding: 20,
      },
    },
    title: {
      display: false,
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      borderColor: '#333',
      borderWidth: 1,
      callbacks: {
        label: function(context) {
          const label = context.dataset.label || '';
          const value = context.parsed.y;
          if (value !== null) {
            return `${label}: ${value.toLocaleString()}만원`;
          }
          return null;
        }
      }
    },
    annotation: {
      annotations: {
        // 국내주식 임계점 라인
        domesticThreshold: {
          type: 'line',
          yMin: 2000,
          yMax: 2000,
          borderColor: '#F44336',
          borderWidth: 2,
          borderDash: [10, 5],
          label: {
            content: '국내주식 임계점 (2,000만원)',
            enabled: true,
            position: 'start',
            backgroundColor: '#F44336',
            color: '#fff',
            font: {
              size: 12,
              weight: 'bold'
            },
            padding: 4,
            borderRadius: 4,
          }
        },
        // 해외주식 임계점 라인
        foreignThreshold: {
          type: 'line',
          yMin: 250,
          yMax: 250,
          borderColor: '#FF9800',
          borderWidth: 2,
          borderDash: [10, 5],
          label: {
            content: '해외주식 임계점 (250만원)',
            enabled: true,
            position: 'start',
            backgroundColor: '#FF9800',
            color: '#fff',
            font: {
              size: 12,
              weight: 'bold'
            },
            padding: 4,
            borderRadius: 4,
          }
        }
      }
    }
  },
  scales: {
    x: {
      ticks: {
        color: '#fff',
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)',
      },
    },
    y: {
      ticks: {
        color: '#fff',
        callback: function(value) {
          return value.toLocaleString() + '만원';
        }
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)',
      },
    },
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false,
  },
};

export default function PortfolioChart() {

  return (
    <div className="chart-section">
      <h2>포트폴리오 실현이익 추이</h2>
      <div className="chart-container" style={{ height: '400px', position: 'relative' }}>
        <Line data={data} options={options} />
      </div>
      <div className="threshold-info">
        <div className="threshold-item">
          <span className="threshold-label">국내주식 분리과세 임계점:</span>
          <span className="threshold-value">2,000만원</span>
        </div>
        <div className="threshold-item">
          <span className="threshold-label">해외주식 분리과세 임계점:</span>
          <span className="threshold-value">250만원</span>
        </div>
      </div>
      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-color" style={{backgroundColor: '#4CAF50'}}></span>
          <span>임계점 이하 (과세율 15.4%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{backgroundColor: '#F44336'}}></span>
          <span>임계점 초과 (과세율 25.4%)</span>
        </div>
      </div>

    </div>
  );
} 