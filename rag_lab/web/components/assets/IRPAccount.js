export default function IRPAccount() {
  const irpData = {
    totalBalance: 20000000,
    thisYearContribution: 15000000,
    maxContribution: 18000000,
    remainingContribution: 3000000,
    totalProfit: 800000,
    profitRate: 4.0,
    products: [
      {
        name: '주식형 펀드',
        type: '주식형',
        balance: 12000000,
        profit: 600000,
        profitRate: 5.0
      },
      {
        name: '채권형 펀드',
        type: '채권형',
        balance: 8000000,
        profit: 200000,
        profitRate: 2.5
      }
    ]
  };

  return (
    <div className="irp-account">
      <div className="irp-summary">
        <div className="summary-card">
          <h3>총 잔고</h3>
          <div className="amount">{irpData.totalBalance.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>이번 년도 납입</h3>
          <div className="amount">{irpData.thisYearContribution.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>남은 납입 한도</h3>
          <div className="amount positive">{irpData.remainingContribution.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>총 수익</h3>
          <div className="amount positive">{irpData.totalProfit.toLocaleString()}원</div>
        </div>
      </div>

      <div className="irp-progress">
        <h3>납입 진행률</h3>
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${(irpData.thisYearContribution / irpData.maxContribution) * 100}%` }}
          ></div>
        </div>
        <div className="progress-text">
          {irpData.thisYearContribution.toLocaleString()}원 / {irpData.maxContribution.toLocaleString()}원
        </div>
      </div>

      <div className="irp-products">
        <h3>보유 상품</h3>
        <table>
          <thead>
            <tr>
              <th>상품명</th>
              <th>상품유형</th>
              <th>잔고</th>
              <th>수익</th>
              <th>수익률</th>
            </tr>
          </thead>
          <tbody>
            {irpData.products.map((product, index) => (
              <tr key={index}>
                <td>{product.name}</td>
                <td>{product.type}</td>
                <td>{product.balance.toLocaleString()}원</td>
                <td className="positive">{product.profit.toLocaleString()}원</td>
                <td className="positive">{product.profitRate}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="irp-actions">
        <button className="action-btn primary">상품 추가</button>
        <button className="action-btn">납입하기</button>
        <button className="action-btn">세금 혜택</button>
        <button className="action-btn">상품 변경</button>
      </div>
    </div>
  );
} 