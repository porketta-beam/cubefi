const express = require('express');
const router = express.Router();
const yahooFinance = require('yfinance');

// 미국 주식 배당 데이터 가져오기
router.get('/us-dividends', async (req, res) => {
  try {
    // 주요 미국 배당주 목록
    const dividendStocks = [
      'TSLA', 'AAPL', 'MSFT', 'JNJ', 'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD',
      'V', 'MA', 'UNH', 'JPM', 'BAC', 'WFC', 'T', 'VZ', 'XOM', 'CVX' 
    ];

    const dividendData = [];

    for (const symbol of dividendStocks) {
      try {
        const ticker = yahooFinance.Ticker(symbol);
        const info = await ticker.info;
        
        // 배당 정보가 있는 경우만 추가
        if (info.dividendRate && info.dividendYield) {
          dividendData.push({
            code: symbol,
            name: info.longName || info.shortName || symbol,
            logo: getStockLogo(symbol),
            exDate: getNextExDate(symbol), // 실제로는 배당락일 계산 필요
            payMonth: getDividendFrequency(info.dividendRate, info.dividendYield),
            amount: `$${info.dividendRate?.toFixed(2) || '0.00'}`,
            yield: `${(info.dividendYield * 100).toFixed(2)}%`,
            price: info.regularMarketPrice,
            marketCap: info.marketCap,
            sector: info.sector
          });
        }
      } catch (error) {
        console.log(`Error fetching data for ${symbol}:`, error.message);
        // 에러가 발생해도 다른 종목은 계속 처리
        continue;
      }
    }

    // 배당률 기준으로 정렬 (높은 순)
    dividendData.sort((a, b) => {
      const yieldA = parseFloat(a.yield.replace('%', ''));
      const yieldB = parseFloat(b.yield.replace('%', ''));
      return yieldB - yieldA;
    });

    res.json({
      success: true,
      data: dividendData,
      count: dividendData.length
    });

  } catch (error) {
    console.error('Error fetching dividend data:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch dividend data',
      message: error.message
    });
  }
});

// 특정 종목의 배당 정보 가져오기
router.get('/stock/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const ticker = yahooFinance.Ticker(symbol);
    const info = await ticker.info;

    if (!info.dividendRate) {
      return res.status(404).json({
        success: false,
        error: 'No dividend data available for this stock'
      });
    }

    const dividendInfo = {
      code: symbol,
      name: info.longName || info.shortName || symbol,
      logo: getStockLogo(symbol),
      exDate: getNextExDate(symbol),
      payMonth: getDividendFrequency(info.dividendRate, info.dividendYield),
      amount: `$${info.dividendRate.toFixed(2)}`,
      yield: `${(info.dividendYield * 100).toFixed(2)}%`,
      price: info.regularMarketPrice,
      marketCap: info.marketCap,
      sector: info.sector,
      dividendHistory: await getDividendHistory(symbol)
    };

    res.json({
      success: true,
      data: dividendInfo
    });

  } catch (error) {
    console.error(`Error fetching data for ${req.params.symbol}:`, error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch stock data',
      message: error.message
    });
  }
});

// 헬퍼 함수들
function getStockLogo(symbol) {
  const logos = {
    'TSLA': '🚗', 'AAPL': '🍎', 'MSFT': '🪟', 'JNJ': '💊', 'PG': '🧴',
    'KO': '🥤', 'PEP': '🥤', 'WMT': '🛒', 'HD': '🔨', 'MCD': '🍔',
    'V': '💳', 'MA': '💳', 'UNH': '🏥', 'JPM': '🏦', 'BAC': '🏦',
    'WFC': '🏦', 'T': '📞', 'VZ': '📞', 'XOM': '⛽', 'CVX': '⛽'
  };
  return logos[symbol] || '📈';
}

function getDividendFrequency(dividendRate, dividendYield) {
  // 간단한 추정: 배당률이 높으면 월배당, 낮으면 분기배당으로 가정
  if (dividendYield > 0.05) { // 5% 이상
    return '월배당';
  } else if (dividendYield > 0.02) { // 2-5%
    return '분기배당';
  } else {
    return '연배당';
  }
}

function getNextExDate(symbol) {
  // 실제로는 배당 일정 API를 사용해야 하지만, 여기서는 더미 데이터
  const today = new Date();
  const nextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 15);
  return nextMonth.toISOString().split('T')[0];
}

async function getDividendHistory(symbol) {
  try {
    const ticker = yahooFinance.Ticker(symbol);
    const dividends = await ticker.dividends;
    return dividends.slice(0, 10); // 최근 10개 배당 내역
  } catch (error) {
    console.log(`Error fetching dividend history for ${symbol}:`, error.message);
    return [];
  }
}

module.exports = router; 