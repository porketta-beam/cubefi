export default function DividendStocks() {
  const stocks = [
    {
      name: '삼성전자',
      ticker: '005930',
      quantity: 100,
      dividendYield: 2.5,
      annualDividend: 170000,
      nextDividend: '2024-03-15',
      totalValue: 6800000
    },
    {
      name: 'SK하이닉스',
      ticker: '000660',
      quantity: 50,
      dividendYield: 1.8,
      annualDividend: 112500,
      nextDividend: '2024-03-20',
      totalValue: 6250000
    }
  ];

  const totalValue = stocks.reduce((sum, stock) => sum + stock.totalValue, 0);
  const totalDividend = stocks.reduce((sum, stock) => sum + stock.annualDividend, 0);
  const avgYield = ((totalDividend / totalValue) * 100).toFixed(2);

  return (
    <div className="dividend-stocks">
      <div className="stocks-summary">
        <div className="summary-card">
          <h3>총 보유 금액</h3>
          <div className="amount">{totalValue.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>연간 배당금</h3>
          <div className="amount positive">{totalDividend.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>평균 배당률</h3>
          <div className="amount positive">{avgYield}%</div>
        </div>
      </div>

      <div className="stocks-table">
        <h3>배당 종목</h3>
        <table>
          <thead>
            <tr>
              <th>종목명</th>
              <th>보유수량</th>
              <th>배당률</th>
              <th>연간 배당금</th>
              <th>다음 배당일</th>
              <th>평가금액</th>
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
                <td>{stock.dividendYield}%</td>
                <td>{stock.annualDividend.toLocaleString()}원</td>
                <td>{stock.nextDividend}</td>
                <td>{stock.totalValue.toLocaleString()}원</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="stocks-actions">
        <button className="action-btn primary">배당주 추가</button>
        <button className="action-btn">배당 내역</button>
        <button className="action-btn">세금 계산</button>
        <button className="action-btn">배당 예상</button>
      </div>
    </div>
  );
} 