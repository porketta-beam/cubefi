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
import DividendCalendar from '../components/DividendCalendar';

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
      <h1>Stock D-TAX 캘린더</h1>
      

      <DividendCalendar />

      

      
    </div>
  );
} 