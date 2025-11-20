import React from 'react';
import './DetailHeader.css';

interface DetailHeaderProps {
  title: string;
  onBack: () => void;
}

const DetailHeader: React.FC<DetailHeaderProps> = ({ title, onBack }) => {
  return (
    <div className="detail-header">
      <div className="detail-header-bottom">
        <button className="detail-back-button" onClick={onBack}>
          <svg 
            width="36" 
            height="36" 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              d="M15 18L9 12L15 6" 
              stroke="currentColor" 
              strokeWidth="3" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </svg>
        </button>
        <h1 className="detail-page-title">{title}</h1>
        <div className="detail-header-spacer"></div>
      </div>
    </div>
  );
};

export default DetailHeader;

