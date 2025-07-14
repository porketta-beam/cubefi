exports.calculateTax = (req, res) => {
  try {
    const { realizedProfit, incomeType, totalIncome } = req.body;
    
    if (!realizedProfit || !incomeType) {
      return res.status(400).json({ 
        error: 'realizedProfit과 incomeType은 필수입니다.' 
      });
    }
    
    let tax = 0;
    let breakdown = {};
    
    if (incomeType === 'domestic') {
      // 국내주식 양도소득세 계산
      if (realizedProfit <= 20000000) {
        // 2,000만원 이하: 분리과세 15.4%
        tax = realizedProfit * 0.154;
        breakdown = {
          type: '분리과세',
          rate: '15.4%',
          amount: realizedProfit,
          tax: tax
        };
      } else {
        // 2,000만원 초과: 종합소득세율 적용
        const progressiveRate = getProgressiveRate(totalIncome || 0);
        const basicTax = 20000000 * 0.154;
        const additionalTax = (realizedProfit - 20000000) * progressiveRate;
        tax = basicTax + additionalTax;
        
        breakdown = {
          type: '종합과세',
          basicAmount: 20000000,
          basicRate: '15.4%',
          basicTax: basicTax,
          additionalAmount: realizedProfit - 20000000,
          additionalRate: `${(progressiveRate * 100).toFixed(1)}%`,
          additionalTax: additionalTax,
          totalTax: tax
        };
      }
    } else if (incomeType === 'foreign') {
      // 해외주식 양도소득세 계산
      tax = realizedProfit * 0.22;
      breakdown = {
        type: '해외주식',
        rate: '22%',
        amount: realizedProfit,
        tax: tax
      };
    } else if (incomeType === 'dividend') {
      // 배당소득세 계산
      tax = realizedProfit * 0.154;
      breakdown = {
        type: '배당소득',
        rate: '15.4%',
        amount: realizedProfit,
        tax: tax
      };
    }
    
    res.json({
      success: true,
      data: {
        realizedProfit: realizedProfit,
        incomeType: incomeType,
        calculatedTax: Math.round(tax),
        breakdown: breakdown
      }
    });
    
  } catch (error) {
    console.error('Tax calculation error:', error);
    res.status(500).json({ 
      error: '세금 계산 중 오류가 발생했습니다.' 
    });
  }
};

function getProgressiveRate(totalIncome) {
  if (totalIncome < 46000000) return 0.066;  // 6.6%
  if (totalIncome < 88000000) return 0.165;  // 16.5%
  if (totalIncome < 150000000) return 0.264; // 26.4%
  if (totalIncome < 300000000) return 0.385; // 38.5%
  if (totalIncome < 500000000) return 0.418; // 41.8%
  return 0.495; // 49.5%
} 