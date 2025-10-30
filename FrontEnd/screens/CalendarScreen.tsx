import React, { useMemo, useState } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import './CalendarScreen.css';

interface CalendarScreenProps {
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
}

const WEEK_DAYS = ['월', '화', '수', '목', '금', '토', '일'];

function getMonthMatrix(baseDate: Date) {
  const year = baseDate.getFullYear();
  const month = baseDate.getMonth();
  const firstDay = new Date(year, month, 1);
  // In JS: 0=Sun..6=Sat → convert to Mon..Sun index
  const firstWeekday = (firstDay.getDay() + 6) % 7; // 0 => Mon
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const cells: Array<{ date: Date; inCurrentMonth: boolean }> = [];

  // Leading empty cells from previous month
  for (let i = 0; i < firstWeekday; i++) {
    const d = new Date(year, month, -firstWeekday + i + 1);
    cells.push({ date: d, inCurrentMonth: false });
  }

  // Current month days
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ date: new Date(year, month, d), inCurrentMonth: true });
  }

  // Trailing cells up to 6 rows x 7 cols
  while (cells.length % 7 !== 0) {
    const last = cells[cells.length - 1].date;
    const d = new Date(last);
    d.setDate(d.getDate() + 1);
    cells.push({ date: d, inCurrentMonth: false });
  }

  // Ensure 6 rows for stable layout
  while (cells.length < 42) {
    const last = cells[cells.length - 1].date;
    const d = new Date(last);
    d.setDate(d.getDate() + 1);
    cells.push({ date: d, inCurrentMonth: false });
  }

  return cells;
}

const CalendarScreen: React.FC<CalendarScreenProps> = ({ onHome, onVideo, onCalendar, onGuide, onSettings }) => {
  const [current, setCurrent] = useState(new Date());
  const [selected, setSelected] = useState<Date | null>(new Date());
  const [activeTab, setActiveTab] = useState<'conversation' | 'report'>('conversation');
  const today = useMemo(() => new Date(), []);
  const [isPanelExpanded, setIsPanelExpanded] = useState(false);
  const [dragStartY, setDragStartY] = useState<number | null>(null);
  const [dragDelta, setDragDelta] = useState(0);

  // mock 저장 데이터 (키: YYYY-MM-DD)
  const savedData: Record<string, { conversation?: string; report?: string }> = {
    '2025-10-18': {
      conversation:
        '응! 오늘 음악 시간에 노래 불렀는데, 선생님이 목소리 예쁘대!\n친구들도 박수 쳐줬어! 그래서 진짜 신났어! 그때 생각했어. 아, 나 진짜 노래가 좋구나!\n그래서… 나 커서 가수가 될래! 무대에서 노래 부르고, 엄마 아빠랑 무키도 보러 오면 진짜 좋겠다!',
      report:
        '음악 시간의 긍정적 경험으로 자신감 향상. 친구들과의 상호작용 양호. 미래 꿈(가수)에 대한 구체적 표현 관찰됨.'
    },
    '2025-10-22': {
      conversation:
        '오늘은 체육 시간에 축구했어! 내가 골 넣었어. 친구들이랑 하이파이브 했지!',
      report:
        '활동적 참여도 높음. 팀워크 향상. 긍정적 정서 표현 다수.'
    }
  };

  const toKey = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

  const matrix = useMemo(() => getMonthMatrix(current), [current]);

  const isSameDate = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

  const handlePrev = () => {
    setCurrent((d) => new Date(d.getFullYear(), d.getMonth() - 1, 1));
  };

  const handleNext = () => {
    setCurrent((d) => new Date(d.getFullYear(), d.getMonth() + 1, 1));
  };

  const year = current.getFullYear();
  const month = current.getMonth() + 1;

  return (
    <div className="calendar-screen">
      <Header />

      <div className="calendar-content">
        <div className="calendar-card">
          <div className="calendar-header-row">
            <button className="month-nav" onClick={handlePrev} aria-label="previous-month">◀</button>
            <div className="month-title">{`${year}년 ${month.toString().padStart(2, '0')}월`}</div>
            <button className="month-nav" onClick={handleNext} aria-label="next-month">▶</button>
          </div>

          <div className="weekday-row">
            {WEEK_DAYS.map((d, idx) => (
              <div className={`weekday ${idx === 5 ? 'sat' : ''} ${idx === 6 ? 'sun' : ''}`} key={d}>{d}</div>
            ))}
          </div>

          <div className="day-grid">
            {matrix.map((cell, i) => {
              const isToday = isSameDate(cell.date, today);
              const isSelected = selected && isSameDate(cell.date, selected);
              const weekIdx = i % 7;
              const label = cell.date.getDate();
              return (
                <div
                  key={i}
                  className={
                    `day-cell ${cell.inCurrentMonth ? '' : 'dim'} ${isToday ? 'today' : ''} ${isSelected && !isToday ? 'selected' : ''} ${weekIdx === 5 ? 'sat' : ''} ${weekIdx === 6 ? 'sun' : ''}`
                  }
                  onClick={() => {
                    if (!cell.inCurrentMonth) return;
                    setSelected(cell.date);
                  }}
                >
                  <span className="day-label">{label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      {/* 하단 패널 */}
      <div 
        className={`calendar-bottom-panel ${isPanelExpanded ? 'expanded' : ''} ${dragDelta !== 0 ? 'dragging' : ''}`}
        onTouchStart={(e) => {
          setDragStartY(e.touches[0].clientY);
          setDragDelta(0);
        }}
        onTouchMove={(e) => {
          if (dragStartY === null) return;
          const dy = e.touches[0].clientY - dragStartY;
          // invert direction: dragging up => negative
          setDragDelta(dy);
        }}
        onTouchEnd={() => {
          if (dragDelta < -50) setIsPanelExpanded(true);
          else if (dragDelta > 50) setIsPanelExpanded(false);
          setDragStartY(null);
          setDragDelta(0);
        }}
        style={dragDelta !== 0 ? { transform: `translateY(${Math.max(Math.min(dragDelta, 200), -200)}px)` } as React.CSSProperties : undefined}
      >
        <div className="panel-handle" onClick={() => setIsPanelExpanded(v => !v)} />
        <div className="panel-tabs">
          <button
            className={`panel-tab ${activeTab === 'conversation' ? 'active' : ''}`}
            onClick={() => setActiveTab('conversation')}
          >
            대화
          </button>
          <button
            className={`panel-tab ${activeTab === 'report' ? 'active' : ''}`}
            onClick={() => setActiveTab('report')}
          >
            리포트
          </button>
        </div>
        <div className="panel-content panel-content-scroll">
          <h3 className="panel-title">{selected ? `${selected.getMonth() + 1}월 ${selected.getDate()}일 ${activeTab === 'conversation' ? '대화' : '리포트'}` : ''}</h3>
          <div className="panel-text">
            {(() => {
              const key = selected ? toKey(selected) : '';
              const data = key ? savedData[key] : undefined;
              const text = activeTab === 'conversation' ? data?.conversation : data?.report;
              if (text) {
                return text.split('\n').map((line, idx) => <p key={idx}>{line}</p>);
              }
              return <p>저장된 내용이 없습니다.</p>;
            })()}
          </div>
        </div>
      </div>

      <Footer 
        activeTab="calendar"
        onHome={onHome}
        onVideo={onVideo}
        onCalendar={onCalendar}
        onGuide={onGuide}
        onSettings={onSettings}
      />
    </div>
  );
};

export default CalendarScreen;


