import React, { useMemo, useState, useEffect } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { reportApi, MonthlyReportItem } from '@/services/api';
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
  const [monthlyReports, setMonthlyReports] = useState<MonthlyReportItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // 월별 리포트 데이터를 날짜별로 매핑 (키: YYYY-MM-DD)
  const reportsByDate = useMemo(() => {
    const map: Record<string, MonthlyReportItem> = {};
    monthlyReports.forEach(report => {
      map[report.date] = report;
    });
    return map;
  }, [monthlyReports]);

  // 현재 표시 중인 월의 리포트 조회
  useEffect(() => {
    const fetchMonthlyReports = async () => {
      const year = current.getFullYear();
      const month = current.getMonth() + 1; // getMonth()는 0-11이므로 +1
      
      setIsLoading(true);
      setErrorMessage(null);
      
      const result = await reportApi.getMonthlyReports(year, month);
      
      if (result.success && result.data) {
        setMonthlyReports(result.data);
      } else {
        setErrorMessage(result.message || '리포트를 불러오는데 실패했습니다.');
        setMonthlyReports([]);
      }
      
      setIsLoading(false);
    };

    fetchMonthlyReports();
  }, [current]);

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
              const cellKey = toKey(cell.date);
              const report = reportsByDate[cellKey];
              const hasData = report !== undefined;
              return (
                <div
                  key={i}
                  className={
                    `day-cell ${cell.inCurrentMonth ? '' : 'dim'} ${isToday ? 'today' : ''} ${isSelected && !isToday ? 'selected' : ''} ${weekIdx === 5 ? 'sat' : ''} ${weekIdx === 6 ? 'sun' : ''} ${hasData ? 'has-data' : ''}`
                  }
                  onClick={() => {
                    if (!cell.inCurrentMonth) return;
                    setSelected(cell.date);
                  }}
                >
                  <span className="day-label">{label}</span>
                  {hasData && <span className="data-indicator"></span>}
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
              if (isLoading) {
                return <p>로딩 중...</p>;
              }
              
              if (errorMessage) {
                return <p style={{ color: '#ff4444' }}>{errorMessage}</p>;
              }
              
              const key = selected ? toKey(selected) : '';
              const report = key ? reportsByDate[key] : undefined;
              
              if (activeTab === 'conversation') {
                if (!report) {
                  return <p>저장된 대화가 없습니다.</p>;
                }
                
                // 대화 로그를 시간순으로 정렬하여 표시
                const sortedLogs = [...(report.dialogue_logs || [])].sort((a, b) => 
                  new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
                );
                
                if (sortedLogs.length === 0) {
                  return <p>저장된 대화가 없습니다.</p>;
                }
                
                // 대화 로그를 메시지 형식으로 변환
                const conversationText = sortedLogs
                  .map(log => {
                    const speakerName = log.speaker === 'child' ? '아이' : log.speaker === 'parent' ? '부모' : '로봇';
                    return `${speakerName}: ${log.message}`;
                  })
                  .join('\n');
                
                if (report.daily_summary) {
                  return (
                    <>
                      <div style={{ marginBottom: '16px' }}>
                        <strong>일일 요약:</strong>
                        <p>{report.daily_summary}</p>
                      </div>
                      <div>
                        <strong>대화 내용:</strong>
                        {conversationText.split('\n').map((line, idx) => <p key={idx}>{line}</p>)}
                      </div>
                    </>
                  );
                }
                
                return conversationText.split('\n').map((line, idx) => <p key={idx}>{line}</p>);
              } else {
                // 리포트 탭
                if (!report) {
                  return <p>저장된 리포트가 없습니다.</p>;
                }
                
                if (!report.analysis_summary) {
                  return <p>저장된 리포트가 없습니다.</p>;
                }
                
                return report.analysis_summary.split('\n').map((line, idx) => <p key={idx}>{line}</p>);
              }
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


