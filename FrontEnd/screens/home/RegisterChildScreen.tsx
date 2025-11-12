import React, { useEffect, useRef, useState } from 'react';
import DetailHeader from '@/components/DetailHeader';
import Footer from '@/components/Footer';
import { childApi } from '@/services/api';
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
  onSettings,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    gender: '여자' as '여자' | '남자',
    birthYear: '',
    birthMonth: '',
    birthDay: '',
    school: '',
    robotSerial: ''
  });

  // 프로필 이미지 (기본: public/icons/Group 1000004404.png)
  const defaultProfileImage = '/icons/Frame 1000000896.png';
  const [profileImage, setProfileImage] = useState<string | null>(defaultProfileImage);
  const [profileFile, setProfileFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

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
      gender,
    }));
  };

  useEffect(() => {
    return () => {
      if (profileImage && profileImage !== defaultProfileImage) {
        URL.revokeObjectURL(profileImage);
      }
    };
  }, [profileImage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (!formData.birthYear || !formData.birthMonth || !formData.birthDay) {
      setErrorMessage('생년월일을 모두 입력해주세요.');
      return;
    }

    const birthDate = `${formData.birthYear}-${formData.birthMonth.padStart(2, '0')}-${formData.birthDay.padStart(2, '0')}`;
    const genderApi = formData.gender === '여자' ? 'female' : 'male';

    setIsLoading(true);

    try {
      const response = await childApi.register({
        name: formData.name.trim(),
        gender: genderApi,
        birth_date: birthDate,
        school: formData.school.trim() || undefined,
        serial_number: formData.robotSerial.trim(),
        profile_img: profileFile ?? undefined,
      });

      if (response.success) {
        console.log('아이 등록 성공:', response.data);
        onRegisterComplete();
      } else {
        setErrorMessage(response.message || '아이 등록에 실패했습니다.');
      }
    } catch (error) {
      console.error('아이 등록 오류:', error);
      setErrorMessage('아이 등록 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
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
            <img
              src={profileImage || defaultProfileImage}
              alt="프로필"
              style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }}
            />
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
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                if (profileImage && profileImage !== defaultProfileImage) {
                  URL.revokeObjectURL(profileImage);
                }
                const url = URL.createObjectURL(file);
                setProfileImage(url);
                setProfileFile(file);
              }
            }}
          />
        </div>

        <form onSubmit={handleSubmit} className="register-form">
          {/* 에러 메시지 */}
          {errorMessage && (
            <div className="error-message" style={{
              color: '#ff4444',
              fontSize: '14px',
              marginBottom: '16px',
              textAlign: 'center',
              padding: '12px',
              backgroundColor: '#fff5f5',
              borderRadius: '8px',
              border: '1px solid #ffcccc'
            }}>
              {errorMessage}
            </div>
          )}

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
            <input
              type="text"
              name="school"
              value={formData.school}
              onChange={handleInputChange}
              className="form-input"
              placeholder="학교명을 입력해주세요"
            />
          </div>

          {/* 로봇 시리얼 번호 */}
          <div className="form-group">
            <label className="form-label">로봇 시리얼 번호</label>
            <input
              type="text"
              name="robotSerial"
              value={formData.robotSerial}
              onChange={handleInputChange}
              className="form-input"
              placeholder="로봇 시리얼 번호를 입력해주세요"
              required
            />
          </div>

          {/* 등록 버튼 */}
          <button 
            type="submit" 
            className="register-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? '처리 중...' : '등록하기'}
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

