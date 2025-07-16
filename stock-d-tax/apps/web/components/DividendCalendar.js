import { useState } from 'react';

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

  return (
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
        <div className="calendar-alert-title">이번 달 주요 일정 및 알림</div>
        {monthEvents.length === 0 && (
          <div className="calendar-alert-empty">이번 달 등록된 일정이 없습니다.</div>
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
    </div>
  );
} 