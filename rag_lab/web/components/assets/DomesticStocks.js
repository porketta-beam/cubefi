<<<<<<< HEAD:ai/web/components/assets/DomesticStocks.js
import { useState } from 'react';

export default function DomesticStocks() {
  const [stocks, setStocks] = useState([
=======
export default function DomesticStocks() {
  const stocks = [
>>>>>>> origin/cbo:rag_lab/web/components/assets/DomesticStocks.js
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
<<<<<<< HEAD:ai/web/components/assets/DomesticStocks.js
  ]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newStock, setNewStock] = useState({
    name: '',
    ticker: '',
    quantity: '',
    avgPrice: '',
    currentPrice: '',
  });
=======
  ];
>>>>>>> origin/cbo:rag_lab/web/components/assets/DomesticStocks.js

  const totalValue = stocks.reduce((sum, stock) => sum + stock.totalValue, 0);
  const totalProfit = stocks.reduce((sum, stock) => sum + stock.profit, 0);
  const totalProfitRate = ((totalProfit / (totalValue - totalProfit)) * 100).toFixed(2);

<<<<<<< HEAD:ai/web/components/assets/DomesticStocks.js
  const handleAddStock = () => {
    if (!newStock.name || !newStock.ticker || !newStock.quantity || !newStock.avgPrice || !newStock.currentPrice) return;
    const quantity = Number(newStock.quantity);
    const avgPrice = Number(newStock.avgPrice);
    const currentPrice = Number(newStock.currentPrice);
    const totalValue = quantity * currentPrice;
    const profit = (currentPrice - avgPrice) * quantity;
    const profitRate = avgPrice !== 0 ? (((currentPrice - avgPrice) / avgPrice) * 100).toFixed(2) : 0;
    setStocks([
      ...stocks,
      {
        name: newStock.name,
        ticker: newStock.ticker,
        quantity,
        avgPrice,
        currentPrice,
        totalValue,
        profit,
        profitRate
      }
    ]);
    setShowAddForm(false);
    setNewStock({ name: '', ticker: '', quantity: '', avgPrice: '', currentPrice: '' });
  };

=======
>>>>>>> origin/cbo:rag_lab/web/components/assets/DomesticStocks.js
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
<<<<<<< HEAD:ai/web/components/assets/DomesticStocks.js
        <div className="stocks-table">
          <h3>보유 종목</h3>
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
      <div className="stocks-actions">
        <button className="action-btn primary" onClick={() => setShowAddForm(true)}>종목 추가</button>
        <button className="action-btn">매수/매도</button>
        <button className="action-btn">세금 계산</button>
        <button className="action-btn">차트 보기</button>
      </div>
      {showAddForm && (
        <div className="add-stock-form" style={{marginTop: '18px', background: '#23262f', borderRadius: '12px', padding: '18px', boxShadow: '0 2px 8px rgba(46,232,108,0.07)', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap'}}>
          <input placeholder="종목명" value={newStock.name} onChange={e => setNewStock({ ...newStock, name: e.target.value })} style={{padding:'8px', borderRadius:'6px', border:'1px solid #3a3d46', background:'#23262f', color:'#fff', minWidth:'100px'}} />
          <input placeholder="티커" value={newStock.ticker} onChange={e => setNewStock({ ...newStock, ticker: e.target.value })} style={{padding:'8px', borderRadius:'6px', border:'1px solid #3a3d46', background:'#23262f', color:'#fff', minWidth:'80px'}} />
          <input placeholder="수량" type="number" value={newStock.quantity} onChange={e => setNewStock({ ...newStock, quantity: e.target.value })} style={{padding:'8px', borderRadius:'6px', border:'1px solid #3a3d46', background:'#23262f', color:'#fff', minWidth:'60px'}} />
          <input placeholder="평균단가" type="number" value={newStock.avgPrice} onChange={e => setNewStock({ ...newStock, avgPrice: e.target.value })} style={{padding:'8px', borderRadius:'6px', border:'1px solid #3a3d46', background:'#23262f', color:'#fff', minWidth:'80px'}} />
          <input placeholder="현재가" type="number" value={newStock.currentPrice} onChange={e => setNewStock({ ...newStock, currentPrice: e.target.value })} style={{padding:'8px', borderRadius:'6px', border:'1px solid #3a3d46', background:'#23262f', color:'#fff', minWidth:'80px'}} />
          <button className="action-btn primary" style={{minWidth:'60px'}} onClick={handleAddStock}>추가</button>
          <button className="action-btn" style={{minWidth:'60px'}} onClick={() => setShowAddForm(false)}>취소</button>
        </div>
      )}
=======
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
>>>>>>> origin/cbo:rag_lab/web/components/assets/DomesticStocks.js
    </div>
  );
} 