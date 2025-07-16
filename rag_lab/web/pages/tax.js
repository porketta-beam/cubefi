import { useState } from 'react';

export default function TaxPage() {
  // 더미데이터 시나리오
  const [form, setForm] = useState({
    realizedProfit: 20500000,
    incomeType: 'domestic',
    totalIncome: 42000000,
  });
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // 더미 계산 로직
    let tax = 0;
    let desc = '';
    if (form.incomeType === 'domestic') {
      if (form.realizedProfit <= 20000000) {
        tax = form.realizedProfit * 0.154;
        desc = '분리과세 15.4% 적용';
      } else {
        const basic = 20000000 * 0.154;
        const add = (form.realizedProfit - 20000000) * 0.066;
        tax = basic + add;
        desc = '2,000만원 초과분 종합과세(6.6%) 적용';
      }
    } else if (form.incomeType === 'foreign') {
      if (form.realizedProfit <= 2500000) {
        tax = 0;
        desc = '비과세';
      } else {
        tax = (form.realizedProfit - 2500000) * 0.2;
        desc = '250만원 초과분 20% 과세';
      }
    } else if (form.incomeType === 'dividend') {
      tax = form.realizedProfit * 0.154;
      desc = '배당소득 15.4% 원천징수';
    }
    setResult({ tax: Math.round(tax), desc });
  };

  return (
    <div className="dashboard-container">
      <h1>세금 계산 시뮬레이션</h1>
      <form className="tax-form" onSubmit={handleSubmit}>
        <div className="tax-form-row">
          <label>소득 구분</label>
          <select name="incomeType" value={form.incomeType} onChange={handleChange}>
            <option value="domestic">국내주식</option>
            <option value="foreign">해외주식</option>
            <option value="dividend">배당소득</option>
          </select>
        </div>
        <div className="tax-form-row">
          <label>실현수익(원)</label>
          <input type="number" name="realizedProfit" value={form.realizedProfit} onChange={handleChange} />
        </div>
        <div className="tax-form-row">
          <label>총소득(원, 종합과세용)</label>
          <input type="number" name="totalIncome" value={form.totalIncome} onChange={handleChange} />
        </div>
        <button className="action-btn primary" type="submit">세금 계산</button>
      </form>
      {result && (
        <div className="dashboard-cards" style={{marginTop:32}}>
          <div className="dashboard-card">
            <div className="card-title">예상 세금</div>
            <div className="card-value warning">{result.tax.toLocaleString()}원</div>
            <div className="card-desc">{result.desc}</div>
          </div>
        </div>
      )}
      <div className="dashboard-alerts">
        <div className="alert warning">
          <b>임계점 안내:</b> 국내주식 2,000만원, 해외주식 250만원 초과 시 추가 과세가 적용됩니다.<br/>
          <span style={{color:'#2ee86c'}}>실현수익 분산, ISA 계좌 활용 등 절세 전략을 챗봇에 문의해보세요.</span>
        </div>
      </div>
    </div>
  );
} 