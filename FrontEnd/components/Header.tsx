import React from 'react';
import './Header.css';

interface HeaderProps {
  onLogoClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onLogoClick }) => {
  const isClickable = typeof onLogoClick === 'function';

  return (
    <div className="app-header">
      <div className="header-content">
        <div className="logo-icon">
          <button
            type="button"
            className={`logo-button${isClickable ? ' clickable' : ''}`}
            onClick={onLogoClick}
            aria-label="헤더 로고"
          >
            <img 
              src="/logos/오키더키 로고.png" 
              alt="오키더키 로고" 
              className="logo-image"
            />
          </button>
        </div>
        <div className="status-icons">

        </div>
      </div>
    </div>
  );
};

export default Header;

