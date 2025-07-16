export default function ForeignStocks() {
  const stocks = [
    {
      name: 'Apple Inc.',
      ticker: 'AAPL',
      quantity: 20,
      avgPrice: 150,
      currentPrice: 165,
      totalValue: 3300,
      profit: 300,
      profitRate: 10.0,
      currency: 'USD'
    },
    {
      name: 'Tesla Inc.',
      ticker: 'TSLA',
      quantity: 15,
      avgPrice: 200,
      currentPrice: 180,
      totalValue: 2700,
      profit: -300,
      profitRate: -10.0,
      currency: 'USD'
    },
    {
      name: 'Microsoft Corp.',
      ticker: 'MSFT',
      quantity: 25,
      avgPrice: 300,
      currentPrice: 320,
      totalValue: 8000,
      profit: 500,
      profitRate: 6.7,
      currency: 'USD'
    }
  ];

  const totalValue = stocks.reduce((sum, stock) => sum + stock.totalValue, 0);
  const totalProfit = stocks.reduce((sum, stock) => sum + stock.profit, 0);
  const totalProfitRate = ((totalProfit / (totalValue - totalProfit)) * 100).toFixed(2);

  return (
    <div className="foreign-stocks">
      <div className="stocks-summary">
        <div className="summary-card">
          <h3>총 보유 금액</h3>
          <div className="amount">${totalValue.toLocaleString()}</div>
        </div>
        <div className="summary-card">
          <h3>총 수익</h3>
          <div className={`amount ${totalProfit >= 0 ? 'positive' : 'negative'}`}>
            {totalProfit >= 0 ? '+' : ''}${totalProfit.toLocaleString()}
          </div>
        </div>
        <div className="summary-card">
          <h3>수익률</h3>
          <div className={`amount ${totalProfitRate >= 0 ? 'positive' : 'negative'}`}>
            {totalProfitRate >= 0 ? '+' : ''}{totalProfitRate}%
          </div>
        </div>
      </div>

      <div className="stocks-table">
        <h3>보유 종목</h3>
        <table>
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
                <td>${stock.avgPrice.toLocaleString()}</td>
                <td>${stock.currentPrice.toLocaleString()}</td>
                <td>${stock.totalValue.toLocaleString()}</td>
                <td className={stock.profit >= 0 ? 'positive' : 'negative'}>
                  {stock.profit >= 0 ? '+' : ''}${stock.profit.toLocaleString()}
                </td>
                <td className={stock.profitRate >= 0 ? 'positive' : 'negative'}>
                  {stock.profitRate >= 0 ? '+' : ''}{stock.profitRate}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="stocks-actions">
        <button className="action-btn primary">종목 추가</button>
        <button className="action-btn">매수/매도</button>
        <button className="action-btn">세금 계산</button>
        <button className="action-btn">환율 정보</button>
      </div>
    </div>
  );
} 