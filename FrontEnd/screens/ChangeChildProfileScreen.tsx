import React, { useRef, useState } from 'react';
import DetailHeader from '@/components/DetailHeader';
import Footer from '@/components/Footer';
import './ChangeChildProfileScreen.css';

interface ChangeChildProfileScreenProps {
  onBack: () => void;
  onHome?: () => void;
  onVideo?: () => void;
  onCalendar?: () => void;
  onGuide?: () => void;
  onSettings?: () => void;
  onSave?: () => void;
}

const ChangeChildProfileScreen: React.FC<ChangeChildProfileScreenProps> = ({
  onBack,
  onHome,
  onVideo,
  onCalendar,
  onGuide,
  onSettings,
  onSave
}) => {
  // 기존 데이터 (실제로는 props나 API에서 받아올 데이터)
  const [formData, setFormData] = useState({
    name: '이원희',
    gender: '여자' as '여자' | '남자',
    birthYear: '2017',
    birthMonth: '03',
    birthDay: '13',
    school: '명덕초등학교',
    robotSerial: ''
  });

  const defaultProfileImage = '/icons/Frame 1000000896.png';
  const [profileImage, setProfileImage] = useState<string | null>(defaultProfileImage);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setProfileImage(url);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('프로필 변경 데이터:', formData);
    onSave?.();
    onBack();
  };

  return (
    <div className="change-child-profile-container">
      {/* 상단 헤더 */}
      <DetailHeader title="아이 프로필 변경" onBack={onBack} />

      {/* 메인 콘텐츠 */}
      <div className="change-child-profile-content">
        <form className="change-child-profile-form" onSubmit={handleSubmit}>
          {/* 프로필 사진 */}
          <div className="profile-picture-section">
            <div className="profile-picture-placeholder">
              {profileImage ? (
                <img
                  src={profileImage}
                  alt="프로필"
                  style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }}
                />
              ) : (
                <img
                  src={defaultProfileImage}
                  alt="프로필 기본 이미지"
                  style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }}
                />
              )}
            </div>
            <div
              className="camera-icon"
              onClick={() => fileInputRef.current?.click()}
              role="button"
              aria-label="프로필 사진 변경"
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M23 19C23 19.5304 22.7893 20.0391 22.4142 20.4142C22.0391 20.7893 21.5304 21 21 21H3C2.46957 21 1.96086 20.7893 1.58579 20.4142C1.21071 20.0391 1 19.5304 1 19V8C1 7.46957 1.21071 6.96086 1.58579 6.58579C1.96086 6.21071 2.46957 6 3 6H7L9 4H15L17 6H21C21.5304 6 22.0391 6.21071 22.4142 6.58579C22.7893 6.96086 23 7.46957 23 8V19Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <circle cx="12" cy="13" r="4" stroke="white" strokeWidth="2" fill="none"/>
              </svg>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              onChange={handleImageChange}
            />
          </div>

          {/* 이름 */}
          <div className="form-group">
            <label className="form-label">이름</label>
            <input
              type="text"
              name="name"
              className="form-input"
              placeholder="이름을 입력해주세요"
              value={formData.name}
              onChange={handleInputChange}
              required
            />
          </div>

          {/* 성별 */}
          <div className="form-group">
            <label className="form-label">성별</label>
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

          {/* 생년월일 */}
          <div className="form-group">
            <label className="form-label">생년월일</label>
            <div className="birth-input-group">
              <input
                type="text"
                name="birthYear"
                className="birth-input"
                placeholder="년"
                value={formData.birthYear}
                onChange={handleInputChange}
                maxLength={4}
                required
              />
              <span className="birth-separator">.</span>
              <input
                type="text"
                name="birthMonth"
                className="birth-input"
                placeholder="월"
                value={formData.birthMonth}
                onChange={handleInputChange}
                maxLength={2}
                required
              />
              <span className="birth-separator">.</span>
              <input
                type="text"
                name="birthDay"
                className="birth-input"
                placeholder="일"
                value={formData.birthDay}
                onChange={handleInputChange}
                maxLength={2}
                required
              />
            </div>
          </div>

          {/* 학교 */}
          <div className="form-group">
            <label className="form-label">학교</label>
            <input
              type="text"
              name="school"
              className="form-input"
              placeholder="학교명을 입력해주세요"
              value={formData.school}
              onChange={handleInputChange}
              required
            />
          </div>

          {/* 저장 버튼 */}
          <button type="submit" className="save-profile-btn">
            저장하기
          </button>
        </form>
      </div>

      {/* 하단 네비게이션 */}
      <Footer 
        activeTab="settings"
        onHome={onHome}
        onVideo={onVideo}
        onCalendar={onCalendar}
        onGuide={onGuide}
        onSettings={onSettings}
      />
    </div>
  );
};

export default ChangeChildProfileScreen;

