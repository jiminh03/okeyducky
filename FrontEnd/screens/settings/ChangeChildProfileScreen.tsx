import React, { useRef, useState, useEffect } from 'react';
import DetailHeader from '@/components/DetailHeader';
import Footer from '@/components/Footer';
import { childApi, ChildInfo } from '@/services/api';
import '../home/RegisterChildScreen.css';

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
    name: '',
    gender: '여자' as '여자' | '남자',
    birthYear: '',
    birthMonth: '',
    birthDay: '',
    school: '',
  });
  const [childInfo, setChildInfo] = useState<ChildInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string>('');

  // 프로필 이미지 (기존 이미지가 있다면 그 URL, 없으면 기본 이미지)
  const defaultProfileImage = '/icons/Frame 1000000896.png';
  const [profileImage, setProfileImage] = useState<string | null>(defaultProfileImage);
  const [profileFile, setProfileFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 컴포넌트 마운트 시 기존 아이 정보 불러오기
  useEffect(() => {
    const fetchChildInfo = async () => {
      setIsLoadingData(true);
      const response = await childApi.getChild();
      
      if (response.success && response.data) {
        setChildInfo(response.data);
        // 생년월일을 YYYY-MM-DD 형식에서 분리
        const [year, month, day] = response.data.birth_date.split('-');
        setFormData({
          name: response.data.name,
          gender: response.data.gender === 'female' ? '여자' : '남자',
          birthYear: year,
          birthMonth: month,
          birthDay: day,
          school: response.data.school || '',
        });
        if (response.data.profile_img_url) {
          setProfileImage(response.data.profile_img_url);
        }
      } else {
        setErrorMessage('아이 정보를 불러오는데 실패했습니다. 다시 시도해주세요.');
      }
      setIsLoadingData(false);
    };

    fetchChildInfo();
  }, []);

  useEffect(() => {
    return () => {
      if (profileFile && profileImage && profileImage.startsWith('blob:')) {
        URL.revokeObjectURL(profileImage);
      }
    };
  }, [profileFile, profileImage]);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    // 생년월일 유효성 검사
    if (!formData.birthYear || !formData.birthMonth || !formData.birthDay) {
      setErrorMessage('생년월일을 모두 입력해주세요.');
      return;
    }

    // 생년월일을 YYYY-MM-DD 형식으로 변환
    const birthDate = `${formData.birthYear}-${formData.birthMonth.padStart(2, '0')}-${formData.birthDay.padStart(2, '0')}`;

    // gender 변환: "여자" -> "female", "남자" -> "male"
    const genderApi = formData.gender === '여자' ? 'female' : 'male';

    setIsLoading(true);

    try {
      const response = await childApi.updateChild({
        name: formData.name.trim(),
        gender: genderApi,
        birth_date: birthDate,
        school: formData.school.trim() || undefined,
        profile_img: profileFile ?? undefined,
      });

      if (response.success) {
        console.log('아이 정보 수정 성공:', response.data);
        onSave?.();
        onBack();
      } else {
        setErrorMessage(response.message || '아이 정보 수정에 실패했습니다.');
      }
    } catch (error) {
      console.error('아이 정보 수정 오류:', error);
      setErrorMessage('아이 정보 수정 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="register-child-container">
      {/* 상단 헤더 */}
      <DetailHeader title="아이 프로필 변경" onBack={onBack} />

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

        {isLoadingData ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div>로딩 중...</div>
          </div>
        ) : (
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

            {/* 로봇 시리얼 번호 (읽기 전용) */}
            {childInfo?.robot && (
              <div className="form-group">
                <label className="form-label">로봇 시리얼 번호</label>
                <input
                  type="text"
                  value={childInfo.robot.serial_number}
                  className="form-input"
                  disabled
                  style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
                />
              </div>
            )}

            {/* 저장 버튼 */}
            <button 
              type="submit" 
              className="register-submit-btn"
              disabled={isLoading}
            >
              {isLoading ? '처리 중...' : '저장하기'}
            </button>
          </form>
        )}
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

