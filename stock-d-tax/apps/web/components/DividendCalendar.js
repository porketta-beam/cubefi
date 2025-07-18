import { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const dummyEvents = [
  { date: '2024-06-10', stock: '삼성전자', title: '배당 지급일', type: 'dividend', amount: 1200, desc: '삼성전자 1분기 배당금 지급일입니다.' },
  { date: '2024-06-25', stock: '전체', title: '양도소득세 신고 마감', type: 'tax', amount: null, desc: '국내주식 양도소득세 신고·납부 마감일입니다.' },
  { date: '2024-07-01', stock: 'ISA', title: '비과세 한도 만기', type: 'alert', amount: null, desc: 'ISA 계좌 비과세 한도 만기 도래! 추가 납입 필요.' },
  { date: '2024-07-15', stock: '삼성전자', title: '종합과세 진입 경고', type: 'alert', amount: null, desc: '실현수익 2,000만원 초과! 종합과세 구간 진입.' },
  { date: '2024-07-20', stock: 'LG에너지솔루션', title: '배당 지급일', type: 'dividend', amount: 800, desc: 'LG에너지솔루션 2분기 배당금 지급일입니다.' },
  { date: '2024-07-25', stock: '네이버', title: '배당 지급일', type: 'dividend', amount: 500, desc: '네이버 2분기 배당금 지급일입니다.' },
];

function getMonthDays(year, month) {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const days = [];
  for (let i = 1; i <= lastDay.getDate(); i++) {
    days.push(new Date(year, month, i));
  }
  return days;
}

function getMonthEvents(year, month) {
  const ym = `${year}-${String(month + 1).padStart(2, '0')}`;
  return dummyEvents.filter(e => e.date.startsWith(ym));
}

export default function DividendCalendar() {
  const today = new Date();
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [selectedMarket, setSelectedMarket] = useState('korea'); // 추가: 선택된 시장 상태
  const [usDividends, setUsDividends] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 미국 주식 배당 데이터 가져오기
  const fetchUSDividends = async () => {
    if (selectedMarket === 'us') {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('http://localhost:8001/api/dividend/us-dividends');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        if (result.success) {
          setUsDividends(result.data);
        } else {
          throw new Error(result.error || 'Failed to fetch dividend data');
        }
      } catch (err) {
        setError(err.message);
        console.error("Error fetching US dividends:", err);
        // 에러 시 더미 데이터 사용
        setUsDividends([
          {
            code: "TSLA",
            name: "Tesla Inc",
            logo: "🚗",
            exDate: "2025-07-11",
            payMonth: "분기배당",
            amount: "$0.24",
            yield: "0.85%",
          },
          {
            code: "AAPL",
            name: "Apple Inc",
            logo: "🍎",
            exDate: "2025-07-10",
            payMonth: "분기배당",
            amount: "$0.24",
            yield: "0.52%",
          },
        ]);
      } finally {
        setLoading(false);
      }
    }
  };

  // 시장 선택이 변경될 때마다 데이터 가져오기
  useEffect(() => {
    if (selectedMarket === 'us') {
      fetchUSDividends();
    }
  }, [selectedMarket]);

  const days = getMonthDays(currentYear, currentMonth);
  const firstDayOfWeek = new Date(currentYear, currentMonth, 1).getDay();
  const monthEvents = getMonthEvents(currentYear, currentMonth);

  const prevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };
  const nextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  const getEventsForDay = (date) => {
    const d = date.toISOString().slice(0, 10);
    return dummyEvents.filter(e => e.date === d);
  };

  // 미국주식/한국주식 더미 데이터
  const krDividends = [
    {
      code: "498400",
      name: "KODEX 200타겟위클리커버드콜",
      logo: "KODEX",
      exDate: "2025-07-14",
      payMonth: "월배당",
      amount: "161원",
      yield: "17.20%",
    },
    {
      code: "480040",
      name: "ACE 미국반도체네일리타겟커버드콜(합성)",
      logo: "ACE",
      exDate: "2025-07-14",
      payMonth: "월배당",
      amount: "124원",
      yield: "15.03%",
    },
    {
      code: "498500",
      name: "TIGER 200타겟위클리커버드콜",
      logo: "TIGER",
      exDate: "2025-07-14",
      payMonth: "월배당",
      amount: "98원",
      yield: "12.45%",
    },
    {
      code: "498600",
      name: "PLUS 200타겟위클리커버드콜",
      logo: "PLUS",
      exDate: "2025-07-14",
      payMonth: "월배당",
      amount: "87원",
      yield: "10.23%",
    },
    {
      code: "005930",
      name: "삼성전자",
      logo: "삼성",
      exDate: "2025-07-15",
      payMonth: "분기배당",
      amount: "1,200원",
      yield: "2.5%",
    },
    {
      code: "000660",
      name: "SK하이닉스",
      logo: "SK",
      exDate: "2025-07-20",
      payMonth: "분기배당",
      amount: "800원",
      yield: "1.8%",
    },
  ];

  // 월별 예상 배당금 더미 데이터
  const monthlyDividends = [2000000, 5000000, 800000, 6500000, 9000000, 750000, 1300000, 3000000, 2400000, 0, 2005000, 7000000];
  const totalDividend = monthlyDividends.reduce((sum, v) => sum + v, 0);
  const barData = {
    labels: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
    datasets: [
      {
        label: '월별 예상 배당금',
        data: monthlyDividends,
        backgroundColor: monthlyDividends.map(v => v > 0 ? '#2ee86c' : '#2a2d36'),
        borderRadius: 8,
        barThickness: 24,
      },
    ],
  };
  const barOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `${context.parsed.y.toLocaleString()}원`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#b0b8c1', font: { size: 15 } },
        grid: { display: false },
      },
      y: {
        display: false,
        grid: { display: false },
      },
    },
  };

  return (
    <>
      <div className="dividend-calendar-pro">
        <div className="calendar-left">
          <div className="calendar-header">
            <button onClick={prevMonth}>&lt;</button>
            <span>{currentYear}년 {currentMonth + 1}월</span>
            <button onClick={nextMonth}>&gt;</button>
          </div>
          <div className="calendar-grid">
            {["일", "월", "화", "수", "목", "금", "토"].map((d) => (
              <div key={d} className="calendar-day-label">{d}</div>
            ))}
            {Array(firstDayOfWeek).fill(null).map((_, i) => (
              <div key={"empty-" + i} className="calendar-day empty"></div>
            ))}
            {days.map((date) => {
              const events = getEventsForDay(date);
              const isToday = date.toDateString() === today.toDateString();
              return (
                <div key={date.toISOString()} className={`calendar-day${isToday ? ' today' : ''}`}> 
                  <span>{date.getDate()}</span>
                  {events.map((event, idx) => (
                    <div
                      key={event.title + idx}
                      className={`calendar-event ${event.type}`}
                      onClick={() => setSelectedEvent(event)}
                      title={event.title}
                    >
                      ●
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
        <div className="calendar-right">
          <div className="calendar-alert-title">이번 주 주요 일정 및 알림</div>
          {monthEvents.length === 0 && (
            <div className="calendar-alert-empty">이번 주 등록된 일정이 없습니다.</div>
          )}
          {monthEvents.map((event, idx) => (
            <div
              key={event.date + event.title + idx}
              className={`calendar-alert-card ${event.type}`}
              onClick={() => setSelectedEvent(event)}
            >
              <div className="alert-row">
                <span className="alert-date">{event.date}</span>
                <span className="alert-type">{event.type === 'dividend' ? '배당' : event.type === 'tax' ? '과세' : '알림'}</span>
              </div>
              <div className="alert-title">{event.stock} {event.title}</div>
              {event.amount && (
                <div className="alert-amount">배당금: <b>{event.amount.toLocaleString()}원</b></div>
              )}
              <div className="alert-desc">{event.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{
        maxWidth:'1200px',
        margin:'32px auto',
        padding:'16px 12px',
        background:'#23262f',
        borderRadius:12,
        boxShadow:'0 4px 16px rgba(46,232,108,0.08)'
      }}>
        <div style={{display:'flex',alignItems:'flex-end',padding:'0'}}>
          <div style={{textAlign:'left', flex:1, marginLeft:'20px'}}>
            <div style={{fontSize:'1.08rem',fontWeight:600,color:'#fff',marginBottom:2,display:'flex',alignItems:'center',gap:4}}>
              전체 계좌 합산
            </div>
            <div style={{fontSize:'2rem',fontWeight:800,color:'#fff',marginBottom:2,lineHeight:1.1}}>
              {totalDividend.toLocaleString()}원
            </div>
          </div>
        </div>
        <div style={{padding:'0 6px 6px 6px',marginTop:2}}>
          <Bar data={barData} options={barOptions} height={60} />
        </div>
      </div>

      <div className="dividend-schedule-section" style={{maxWidth:'1200px',margin:'32px auto',background:'#23262f',borderRadius:12,padding:'32px 24px',boxShadow:'0 4px 16px rgba(46,232,108,0.08)'}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'24px'}}>
          <h3 style={{color:'#2ee86c', fontSize:'1.25rem', margin:0}}>배당 일정</h3>
          <div style={{display:'flex',gap:'12px',alignItems:'center'}}>
            <select 
              value={selectedMarket}
              onChange={(e) => setSelectedMarket(e.target.value)}
              style={{background:'#20232a',color:'#fff',border:'1px solid #2ee86c',borderRadius:6,padding:'6px 12px',fontSize:'0.9rem'}}
            >
              <option value="korea">한국 배당</option>
              <option value="us">미국 배당</option>
            </select>
            <span style={{color:'#b0b8c1',fontSize:'0.9rem'}}>시가배당률 높은 순 ↑</span>
          </div>
        </div>
        
        {selectedMarket === 'korea' && (
          <>
            <h4 style={{color:'#fff', fontSize:'1.08rem', margin:'10px 0 16px'}}>한국주식</h4>
            <div style={{display:'flex',flexDirection:'column',gap:'8px'}}>
              {krDividends.map((d, i) => (
                <div key={d.code + i} style={{
                  display:'flex',
                  alignItems:'center',
                  background:'#20232a',
                  borderRadius:8,
                  padding:'16px',
                  gap:'16px',
                  border:'1px solid #2a2d36',
                  transition:'all 0.2s ease'
                }}>
                  {/* 로고 섹션 */}
                  <div style={{
                    width:'48px',
                    height:'48px',
                    borderRadius:'50%',
                    background:'#2ee86c',
                    display:'flex',
                    alignItems:'center',
                    justifyContent:'center',
                    fontSize:'12px',
                    fontWeight:'bold',
                    color:'#181a20',
                    flexShrink:0
                  }}>
                    {d.logo}
                  </div>
                  
                  {/* 상품 정보 섹션 */}
                  <div style={{flex:1,minWidth:0}}>
                    <div style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'4px'}}>
                      <span style={{color:'#fff',fontWeight:'bold',fontSize:'1rem'}}>{d.code}</span>
                      <span style={{color:'#b0b8c1',fontSize:'0.9rem'}}>{d.name}</span>
                    </div>
                    <div style={{display:'flex',gap:'16px',fontSize:'0.85rem',color:'#888'}}>
                      <span>배당락원: {d.exDate}</span>
                      <span>배당 지급일: {d.payMonth}</span>
                    </div>
                  </div>
                  
                  {/* 배당금 섹션 */}
                  <div style={{
                    textAlign:'right',
                    minWidth:'80px',
                    color:'#fff',
                    fontWeight:'bold',
                    fontSize:'1.1rem'
                  }}>
                    ₩{d.amount}
                  </div>
                  
                  {/* 배당률 섹션 */}
                  <div style={{
                    textAlign:'right',
                    minWidth:'100px',
                    color:'#2ee86c',
                    fontWeight:'bold',
                    fontSize:'1.1rem'
                  }}>
                    연 {d.yield}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
        
        {selectedMarket === 'us' && (
          <>
            <h4 style={{color:'#fff', fontSize:'1.08rem', margin:'10px 0 16px'}}>미국주식</h4>
            <div style={{display:'flex',flexDirection:'column',gap:'8px'}}>
              {loading ? (
                <div style={{
                  display:'flex',
                  alignItems:'center',
                  justifyContent:'center',
                  background:'#20232a',
                  borderRadius:8,
                  padding:'40px 16px',
                  color:'#2ee86c',
                  fontSize:'1.1rem',
                  fontWeight:'bold'
                }}>
                  <div style={{
                    width:'24px',
                    height:'24px',
                    border:'3px solid #2ee86c',
                    borderTop:'3px solid transparent',
                    borderRadius:'50%',
                    animation:'spin 1s linear infinite',
                    marginRight:'12px'
                  }}></div>
                  배당 데이터를 가져오는 중...
                </div>
              ) : error ? (
                <div style={{
                  display:'flex',
                  alignItems:'center',
                  justifyContent:'center',
                  background:'#2a1f1f',
                  borderRadius:8,
                  padding:'24px 16px',
                  color:'#ff6384',
                  fontSize:'1rem',
                  border:'1px solid #ff6384'
                }}>
                  ⚠️ {error} (더미 데이터로 표시)
                </div>
              ) : (
                usDividends.map((d, i) => (
                  <div key={d.code + i} style={{
                    display:'flex',
                    alignItems:'center',
                    background:'#20232a',
                    borderRadius:8,
                    padding:'16px',
                    gap:'16px',
                    border:'1px solid #2a2d36',
                    transition:'all 0.2s ease'
                  }}>
                    {/* 로고 섹션 */}
                    <div style={{
                      width:'48px',
                      height:'48px',
                      borderRadius:'50%',
                      background:'#36a2eb',
                      display:'flex',
                      alignItems:'center',
                      justifyContent:'center',
                      fontSize:'16px',
                      flexShrink:0
                    }}>
                      {d.logo}
                    </div>
                    
                    {/* 상품 정보 섹션 */}
                    <div style={{flex:1,minWidth:0}}>
                      <div style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'4px'}}>
                        <span style={{color:'#fff',fontWeight:'bold',fontSize:'1rem'}}>{d.code}</span>
                        <span style={{color:'#b0b8c1',fontSize:'0.9rem'}}>{d.name}</span>
                      </div>
                      <div style={{display:'flex',gap:'16px',fontSize:'0.85rem',color:'#888'}}>
                        <span>배당락원: {d.exDate}</span>
                        <span>배당 지급일: {d.payMonth}</span>
                      </div>
                    </div>
                    
                    {/* 배당금 섹션 */}
                    <div style={{
                      textAlign:'right',
                      minWidth:'80px',
                      color:'#fff',
                      fontWeight:'bold',
                      fontSize:'1.1rem'
                    }}>
                      {d.amount}
                    </div>
                    
                    {/* 배당률 섹션 */}
                    <div style={{
                      textAlign:'right',
                      minWidth:'100px',
                      color:'#2ee86c',
                      fontWeight:'bold',
                      fontSize:'1.1rem'
                    }}>
                      연 {d.yield}
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </div>
      {selectedEvent && (
        <div className="calendar-popup" onClick={() => setSelectedEvent(null)}>
          <div className="calendar-popup-content" onClick={e => e.stopPropagation()}>
            <h4>{selectedEvent.stock} {selectedEvent.title}</h4>
            <p>{selectedEvent.date}</p>
            {selectedEvent.amount && <p>배당금: <b>{selectedEvent.amount.toLocaleString()}원</b></p>}
            <p>{selectedEvent.desc}</p>
            <button onClick={() => setSelectedEvent(null)}>닫기</button>
          </div>
        </div>
      )}
    </>
  );
} 