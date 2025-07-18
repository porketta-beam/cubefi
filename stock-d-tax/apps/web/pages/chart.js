import React, { useState } from 'react';
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
  // 배당소득세/양도소득세 더미 데이터
  const dividendProfit = 20000000;
  const dividendTax = 10000000;
  const dividendLabels = ['2,000만원 기준'];

  // 내 예상 세금이 2,000만원 초과 시 막대 전체를 세금 색으로 채움
  const isOverDividend = dividendTax > 20000000;
  const dividendBarData = {
    labels: dividendLabels,
    datasets: isOverDividend
      ? [
          {
            label: '내 예상 세금',
            data: [dividendProfit],
            backgroundColor: '#ff6384',
            borderRadius: 6,
            barThickness: 100,
            stack: 'total',
          },
        ]
      : [
          {
            label: '내 예상 세금',
            data: [dividendTax],
            backgroundColor: '#ff6384',
            borderRadius: 6,
            barThickness: 100,
            stack: 'total',
          },
          {
            label: '2,000만 원',
            data: [dividendProfit - dividendTax],
            backgroundColor: '#2ee86c88',
            borderRadius: 6,
            barThickness: 100,
            stack: 'total',
          },
        ],
  };

  // 양도소득세 더미 데이터
  const transferProfit = 2500000;
  const transferTax = 1800000;
  const transferLabels = ['250만원 기준'];
  const transferBarData = {
    labels: transferLabels,
    datasets: [
      {
        label: '내 예상 세금',
        data: [transferTax],
        backgroundColor: '#ff6384',
        borderRadius: 6,
        barThickness: 100,
        stack: 'total',
      },
      {
        label: '250만 원',
        data: [transferProfit - transferTax],
        backgroundColor: '#2ee86c88',
        borderRadius: 6,
        barThickness: 100,
        stack: 'total',
      },
    ],
  };
  
  const accountBarOptions = {
    responsive: true,
    indexAxis: 'y',
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#fff',
          font: { size: 23 },
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            const value = context.raw?.toLocaleString() ?? '';
            return `₩${value}`;
          },
        },
        bodyFont: {
          size: 20,
        },
      },
    },
    scales: {
      x: {
        ticks: {
          display: true,
          color: '#fff',
          font: { size: 13 },
          callback: function(value) {
            if (value === 0 || value === 20000000) {
              return `₩${value.toLocaleString()}`;
            }
            return '';
          },
        },
        grid: { color: 'rgba(255,255,255,0.08)' },
      },
      y: {
        ticks: {
          display: false,
          color: '#fff',
          callback: function (value) {
            return `₩${value.toLocaleString()}`;
          },
        },
        grid: { color: 'rgba(255,255,255,0.08)' },
      },
    },
  };

  // 배당소득세 차트 옵션 (2,000만원 기준)
  const dividendBarOptions = {
    ...accountBarOptions,
    scales: {
      ...accountBarOptions.scales,
      x: {
        ...accountBarOptions.scales.x,
        stacked: true,
        ticks: {
          ...accountBarOptions.scales.x.ticks,
          callback: function(value) {
            if (value === 0 || value === 20000000) {
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

  // 양도소득세 차트 옵션 (250만원 기준)
  const transferBarOptions = {
    ...accountBarOptions,
    scales: {
      ...accountBarOptions.scales,
      x: {
        ...accountBarOptions.scales.x,
        stacked: true,
        ticks: {
          ...accountBarOptions.scales.x.ticks,
          callback: function(value) {
            if (value === 0 || value === 2500000) {
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
    <div className="dashboard-container">
      <h1>~~~ 세금 계산기 ~~~</h1>
      <div className="chart-section account-chart-section">
        {/* 실현수익이 2,000만원 초과 시 안내문구만 표시 */}
        {isOverDividend ? (
          <div style={{ color: '#fff', background: '#ff6384', padding: 12, borderRadius: 8, marginBottom: 12, fontWeight: 'bold', fontSize: '1.2rem' }}>
            실현수익이 20,000,000원을 초과했습니다.
          </div>
        ) : null}
        <br/>
        <h2>배당소득세 현황</h2>
        <Bar data={dividendBarData} options={dividendBarOptions} />
      </div>
      <div className="alert warning">
          <b>국내주식 실현수익 2,000만원 초과 시, </b> 종합과세 구간 진입, 초과분 누진세율 적용.<br/>
          <span style={{color:'#2ee86c'}}>ISA 계좌 활용, 실현수익 분산 등 절세 전략을 추천드립니다.</span>
        </div>
      <div className="chart-section account-chart-section">
        <br/>
        <h2>양도소득세 현황</h2>
        <Bar data={transferBarData} options={transferBarOptions} />
      </div>
      
        
        <div className="alert warning">
          <b>해외주식 실현수익 250만원 초과 시, </b> 초과분 22% 세율 적용.<br/>
          <span style={{color:'#2ee86c'}}>손실 종목 매도, 연도별 분산 매도 등 절세 전략을 활용하세요.</span>
        </div>
      <div className="dashboard-alerts">
      </div>
    </div>
  );
} 