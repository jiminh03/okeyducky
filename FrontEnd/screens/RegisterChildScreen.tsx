import React, { useState } from 'react';
import DetailHeader from '@/components/DetailHeader';
import Footer from '@/components/Footer';
import './RegisterChildScreen.css';

interface RegisterChildScreenProps {
  onBack: () => void;
  onRegisterComplete: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
}

const RegisterChildScreen: React.FC<RegisterChildScreenProps> = ({
  onBack,
  onRegisterComplete,
  onVideo,
  onCalendar,
  onGuide,
  onSettings
}) => {
  const [formData, setFormData] = useState({
    name: '',
    gender: '여자' as '여자' | '남자',
    birthYear: '',
    birthMonth: '',
    birthDay: '',
    school: ''
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleGenderSelect = (gender: '여자' | '남자') => {
    setFormData(prev => ({
      ...prev,
      gender
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('아이 등록 데이터:', formData);
    // 아이 등록 로직 구현
    onRegisterComplete();
  };

  return (
    <div className="register-child-container">
      {/* 상단 헤더 */}
      <DetailHeader title="아이 등록" onBack={onBack} />

      {/* 메인 콘텐츠 */}
      <div className="register-child-content">
        {/* 프로필 사진 */}
        <div className="profile-picture-section">
          <div className="profile-picture-placeholder">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" fill="#999"/>
              <path d="M12 14C8.67 14 6 15.34 6 17V20H18V17C18 15.34 15.33 14 12 14Z" fill="#999"/>
            </svg>
          </div>
          <div className="camera-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" fill="white"/>
              <path d="M20 4H16.83L15.59 2.65C15.22 2.24 14.68 2 14.12 2H9.88C9.32 2 8.78 2.24 8.41 2.65L7.17 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4ZM12 17C9.24 17 7 14.76 7 12C7 9.24 9.24 7 12 7C14.76 7 17 9.24 17 12C17 14.76 14.76 17 12 17Z" fill="#2563EB"/>
            </svg>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="register-form">
          {/* 아이 이름 */}
          <div className="form-group">
            <label className="form-label">아이 이름</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              className="form-input"
              placeholder="이름을 입력해주세요"
              required
            />
          </div>

          {/* 아이 성별 */}
          <div className="form-group">
            <div className="form-label-row">
              <label className="form-label">아이 성별</label>
            </div>
            <div className="gender-buttons">
              <button
                type="button"
                className={`gender-btn ${formData.gender === '여자' ? 'active female' : ''}`}
                onClick={() => handleGenderSelect('여자')}
              >
                <span className="gender-symbol">♀</span>
                <span className="gender-text">여자</span>
              </button>
              <button
                type="button"
                className={`gender-btn ${formData.gender === '남자' ? 'active male' : ''}`}
                onClick={() => handleGenderSelect('남자')}
              >
                <span className="gender-symbol">♂</span>
                <span className="gender-text">남자</span>
              </button>
            </div>
          </div>

          {/* 아이 생년월일 */}
          <div className="form-group">
            <label className="form-label">아이 생년월일</label>
            <div className="birth-inputs">
              <input
                type="text"
                name="birthYear"
                value={formData.birthYear}
                onChange={handleInputChange}
                className="birth-input year"
                placeholder=""
                maxLength={4}
                required
              />
              <span className="birth-label">년</span>
              <input
                type="text"
                name="birthMonth"
                value={formData.birthMonth}
                onChange={handleInputChange}
                className="birth-input month"
                placeholder=""
                maxLength={2}
                required
              />
              <span className="birth-label">월</span>
              <input
                type="text"
                name="birthDay"
                value={formData.birthDay}
                onChange={handleInputChange}
                className="birth-input day"
                placeholder=""
                maxLength={2}
                required
              />
              <span className="birth-label">일</span>
            </div>
          </div>

          {/* 아이 학교 */}
          <div className="form-group">
            <label className="form-label">아이 학교</label>
            <div className="school-input-wrapper">
              <input
                type="text"
                name="school"
                value={formData.school}
                onChange={handleInputChange}
                className="form-input school-input"
                placeholder="학교를 검색해주세요"
              />
              <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 19C15.4183 19 19 15.4183 19 11C19 6.58172 15.4183 3 11 3C6.58172 3 3 6.58172 3 11C3 15.4183 6.58172 19 11 19Z" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M21 21L16.65 16.65" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>

          {/* 등록 버튼 */}
          <button type="submit" className="register-submit-btn">
            등록하기
          </button>
        </form>
      </div>

      {/* 하단 네비게이션 */}
      <Footer 
        activeTab="home"
        onHome={onBack}
        onVideo={onVideo}
        onCalendar={onCalendar}
        onGuide={onGuide}
        onSettings={onSettings}
      />
    </div>
  );
};

export default RegisterChildScreen;

