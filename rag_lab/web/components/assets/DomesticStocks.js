export default function DomesticStocks() {
  const stocks = [
    {
      name: '삼성전자',
      ticker: '005930',
      quantity: 100,
      avgPrice: 65000,
      currentPrice: 68000,
      totalValue: 6800000,
      profit: 300000,
      profitRate: 4.6
    },
    {
      name: 'SK하이닉스',
      ticker: '000660',
      quantity: 50,
      avgPrice: 120000,
      currentPrice: 125000,
      totalValue: 6250000,
      profit: 250000,
      profitRate: 4.2
    },
    {
      name: 'NAVER',
      ticker: '035420',
      quantity: 30,
      avgPrice: 180000,
      currentPrice: 175000,
      totalValue: 5250000,
      profit: -150000,
      profitRate: -2.8
    },
    {
      name: '카카오',
      ticker: '035720',
      quantity: 80,
      avgPrice: 45000,
      currentPrice: 48000,
      totalValue: 3840000,
      profit: 240000,
      profitRate: 6.7
    }
  ];

  const totalValue = stocks.reduce((sum, stock) => sum + stock.totalValue, 0);
  const totalProfit = stocks.reduce((sum, stock) => sum + stock.profit, 0);
  const totalProfitRate = ((totalProfit / (totalValue - totalProfit)) * 100).toFixed(2);

  return (
    <div className="domino-tab-section">
      <div className="domino-tab-summary-cards">
        <div className="domino-tab-card">
          <div className="domino-tab-card-label">총 평가금액</div>
          <div className="domino-tab-card-value">{totalValue.toLocaleString()}원</div>
        </div>
        <div className="domino-tab-card">
          <div className="domino-tab-card-label">총 수익</div>
          <div className={`domino-tab-card-value ${totalProfit >= 0 ? 'positive' : 'negative'}`}>{totalProfit >= 0 ? '+' : ''}{totalProfit.toLocaleString()}원</div>
        </div>
        <div className="domino-tab-card">
          <div className="domino-tab-card-label">수익률</div>
          <div className={`domino-tab-card-value ${totalProfitRate >= 0 ? 'positive' : 'negative'}`}>{totalProfitRate >= 0 ? '+' : ''}{totalProfitRate}%</div>
        </div>
      </div>
      <div className="domino-tab-table-section">
        <div className="domino-tab-table-header">
          <h3>보유 종목</h3>
          <div className="domino-tab-actions">
            <button className="action-btn primary">종목 추가</button>
            <button className="action-btn">매수/매도</button>
            <button className="action-btn">세금 계산</button>
            <button className="action-btn">차트 보기</button>
          </div>
        </div>
        <div className="domino-tab-table-wrap">
          <table className="domino-tab-table">
            <thead>
              <tr>
                <th>종목명</th>
                <th>보유수량</th>
                <th>평균단가</th>
                <th>현재가</th>
                <th>평가금액</th>
                <th>평가손익</th>
                <th>수익률</th>
              </tr>
            </thead>
            <tbody>
              {stocks.map((stock, index) => (
                <tr key={index}>
                  <td>
                    <div className="stock-info">
                      <div className="stock-name">{stock.name}</div>
                      <div className="stock-ticker">{stock.ticker}</div>
                    </div>
                  </td>
                  <td>{stock.quantity.toLocaleString()}주</td>
                  <td>{stock.avgPrice.toLocaleString()}원</td>
                  <td>{stock.currentPrice.toLocaleString()}원</td>
                  <td>{stock.totalValue.toLocaleString()}원</td>
                  <td className={stock.profit >= 0 ? 'positive' : 'negative'}>
                    {stock.profit >= 0 ? '+' : ''}{stock.profit.toLocaleString()}원
                  </td>
                  <td className={stock.profitRate >= 0 ? 'positive' : 'negative'}>
                    {stock.profitRate >= 0 ? '+' : ''}{stock.profitRate}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 