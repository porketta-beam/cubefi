export default function PensionAccount() {
  const pensionData = {
    totalBalance: 10000000,
    thisYearContribution: 6000000,
    maxContribution: 9000000,
    remainingContribution: 3000000,
    totalProfit: 400000,
    profitRate: 4.0,
    products: [
      {
        name: '연금저축펀드',
        type: '펀드형',
        balance: 6000000,
        profit: 240000,
        profitRate: 4.0
      },
      {
        name: '연금저축보험',
        type: '보험형',
        balance: 4000000,
        profit: 160000,
        profitRate: 4.0
      }
    ]
  };

  return (
    <div className="pension-account">
      <div className="pension-summary">
        <div className="summary-card">
          <h3>총 잔고</h3>
          <div className="amount">{pensionData.totalBalance.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>이번 년도 납입</h3>
          <div className="amount">{pensionData.thisYearContribution.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>남은 납입 한도</h3>
          <div className="amount positive">{pensionData.remainingContribution.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>총 수익</h3>
          <div className="amount positive">{pensionData.totalProfit.toLocaleString()}원</div>
        </div>
      </div>

      <div className="pension-progress">
        <h3>납입 진행률</h3>
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${(pensionData.thisYearContribution / pensionData.maxContribution) * 100}%` }}
          ></div>
        </div>
        <div className="progress-text">
          {pensionData.thisYearContribution.toLocaleString()}원 / {pensionData.maxContribution.toLocaleString()}원
        </div>
      </div>

      <div className="pension-products">
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
            {pensionData.products.map((product, index) => (
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

      <div className="pension-actions">
        <button className="action-btn primary">상품 추가</button>
        <button className="action-btn">납입하기</button>
        <button className="action-btn">세금 혜택</button>
        <button className="action-btn">상품 변경</button>
      </div>
    </div>
  );
} 