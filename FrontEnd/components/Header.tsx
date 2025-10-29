import React from 'react';
import './Header.css';

const Header: React.FC = () => {
  return (
    <div className="app-header">
      <div className="header-content">
        <div className="logo-icon">
          <img 
            src="/logos/오키더키 로고.png" 
            alt="오키더키 로고" 
            className="logo-image"
          />
        </div>
        <div className="status-icons">

        </div>
      </div>
    </div>
  );
};

export default Header;

