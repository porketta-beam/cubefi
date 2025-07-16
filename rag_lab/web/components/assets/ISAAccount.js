export default function ISAAccount() {
  const isaData = {
    totalBalance: 30000000,
    thisYearContribution: 20000000,
    maxContribution: 25000000,
    remainingContribution: 5000000,
    totalProfit: 1500000,
    profitRate: 5.0,
    products: [
      {
        name: '삼성전자',
        type: '주식형',
        balance: 15000000,
        profit: 750000,
        profitRate: 5.0
      },
      {
        name: '글로벌 ETF',
        type: 'ETF형',
        balance: 10000000,
        profit: 500000,
        profitRate: 5.0
      },
      {
        name: '채권형 펀드',
        type: '채권형',
        balance: 5000000,
        profit: 250000,
        profitRate: 5.0
      }
    ]
  };

  return (
    <div className="isa-account">
      <div className="isa-summary">
        <div className="summary-card">
          <h3>총 잔고</h3>
          <div className="amount">{isaData.totalBalance.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>이번 년도 납입</h3>
          <div className="amount">{isaData.thisYearContribution.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>남은 납입 한도</h3>
          <div className="amount positive">{isaData.remainingContribution.toLocaleString()}원</div>
        </div>
        <div className="summary-card">
          <h3>총 수익</h3>
          <div className="amount positive">{isaData.totalProfit.toLocaleString()}원</div>
        </div>
      </div>

      <div className="isa-progress">
        <h3>납입 진행률</h3>
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${(isaData.thisYearContribution / isaData.maxContribution) * 100}%` }}
          ></div>
        </div>
        <div className="progress-text">
          {isaData.thisYearContribution.toLocaleString()}원 / {isaData.maxContribution.toLocaleString()}원
        </div>
      </div>

      <div className="isa-products">
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
            {isaData.products.map((product, index) => (
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

      <div className="isa-actions">
        <button className="action-btn primary">상품 추가</button>
        <button className="action-btn">납입하기</button>
        <button className="action-btn">세금 혜택</button>
        <button className="action-btn">상품 변경</button>
      </div>
    </div>
  );
} 