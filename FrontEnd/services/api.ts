// API 기본 설정 및 유틸리티 함수

// 백엔드 API URL 설정
// 환경 변수로 설정하거나, 백엔드 서버 주소로 변경하세요
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080/api';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
}

// 기본 fetch 래퍼
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
    };
  } catch (error) {
    console.error('API Request Error:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
    };
  }
}

// 학교 정보 인터페이스
export interface SchoolInfo {
  id: string;
  name: string;
  address?: string;
  region?: string;
  type?: string; // 초등학교, 중학교, 고등학교 등
}

// 학교 검색 API
// 실제 백엔드 API를 사용합니다.
// 백엔드에서 다음 엔드포인트를 구현해야 합니다:
// GET /api/schools/search?keyword={검색어}
// 응답 형식: { success: boolean, data: SchoolInfo[] }
export const schoolApi = {
  // 학교 목록 검색
  // 백엔드 API 엔드포인트: GET /api/schools/search?keyword={검색어}
  searchSchools: async (keyword: string): Promise<ApiResponse<SchoolInfo[]>> => {
    return apiRequest<SchoolInfo[]>(`/schools/search?keyword=${encodeURIComponent(keyword)}`, {
      method: 'GET',
    });
  },

  // 학교 상세 정보 조회
  getSchoolDetail: async (schoolId: string): Promise<ApiResponse<SchoolInfo>> => {
    return apiRequest<SchoolInfo>(`/schools/${schoolId}`, {
      method: 'GET',
    });
  },
};

// 로컬 테스트용 더미 데이터 (백엔드 API가 없을 경우)
const dummySchools: SchoolInfo[] = [
  // 서울 지역 학교
  { id: '1', name: '서울초등학교', address: '서울특별시 강남구', region: '서울', type: '초등학교' },
  { id: '2', name: '서울중학교', address: '서울특별시 강남구', region: '서울', type: '중학교' },
  { id: '3', name: '서울고등학교', address: '서울특별시 강남구', region: '서울', type: '고등학교' },
  { id: '9', name: '서울국제초등학교', address: '서울특별시 송파구', region: '서울', type: '초등학교' },
  { id: '10', name: '강남초등학교', address: '서울특별시 강남구', region: '서울', type: '초등학교' },
  { id: '11', name: '강남중학교', address: '서울특별시 강남구', region: '서울', type: '중학교' },
  { id: '12', name: '서울대학교사범대학부설초등학교', address: '서울특별시 관악구', region: '서울', type: '초등학교' },
  { id: '13', name: '서울대학교사범대학부설중학교', address: '서울특별시 관악구', region: '서울', type: '중학교' },
  { id: '14', name: '서울대학교사범대학부설고등학교', address: '서울특별시 관악구', region: '서울', type: '고등학교' },
  { id: '15', name: '잠실초등학교', address: '서울특별시 송파구', region: '서울', type: '초등학교' },
  { id: '16', name: '잠실중학교', address: '서울특별시 송파구', region: '서울', type: '중학교' },
  { id: '17', name: '잠실고등학교', address: '서울특별시 송파구', region: '서울', type: '고등학교' },
  { id: '18', name: '홍대부속초등학교', address: '서울특별시 마포구', region: '서울', type: '초등학교' },
  { id: '19', name: '홍대부속중학교', address: '서울특별시 마포구', region: '서울', type: '중학교' },
  { id: '20', name: '명덕초등학교', address: '서울특별시 서초구', region: '서울', type: '초등학교' },
  { id: '21', name: '명덕중학교', address: '서울특별시 서초구', region: '서울', type: '중학교' },
  { id: '22', name: '서초초등학교', address: '서울특별시 서초구', region: '서울', type: '초등학교' },
  { id: '23', name: '반포초등학교', address: '서울특별시 서초구', region: '서울', type: '초등학교' },
  { id: '24', name: '신사초등학교', address: '서울특별시 강남구', region: '서울', type: '초등학교' },
  { id: '25', name: '압구정초등학교', address: '서울특별시 강남구', region: '서울', type: '초등학교' },
  { id: '26', name: '압구정중학교', address: '서울특별시 강남구', region: '서울', type: '중학교' },
  { id: '27', name: '청담초등학교', address: '서울특별시 강남구', region: '서울', type: '초등학교' },
  { id: '28', name: '청담중학교', address: '서울특별시 강남구', region: '서울', type: '중학교' },
  { id: '29', name: '한강초등학교', address: '서울특별시 용산구', region: '서울', type: '초등학교' },
  { id: '30', name: '한강중학교', address: '서울특별시 용산구', region: '서울', type: '중학교' },
  { id: '31', name: '이촌초등학교', address: '서울특별시 용산구', region: '서울', type: '초등학교' },
  { id: '32', name: '용산초등학교', address: '서울특별시 용산구', region: '서울', type: '초등학교' },
  { id: '33', name: '용산중학교', address: '서울특별시 용산구', region: '서울', type: '중학교' },
  { id: '34', name: '용산고등학교', address: '서울특별시 용산구', region: '서울', type: '고등학교' },
  { id: '35', name: '영등포초등학교', address: '서울특별시 영등포구', region: '서울', type: '초등학교' },
  { id: '36', name: '영등포중학교', address: '서울특별시 영등포구', region: '서울', type: '중학교' },
  { id: '37', name: '여의도초등학교', address: '서울특별시 영등포구', region: '서울', type: '초등학교' },
  { id: '38', name: '여의도중학교', address: '서울특별시 영등포구', region: '서울', type: '중학교' },
  
  // 부산 지역 학교
  { id: '4', name: '부산초등학교', address: '부산광역시 해운대구', region: '부산', type: '초등학교' },
  { id: '5', name: '부산중학교', address: '부산광역시 해운대구', region: '부산', type: '중학교' },
  { id: '39', name: '부산고등학교', address: '부산광역시 해운대구', region: '부산', type: '고등학교' },
  { id: '40', name: '해운대초등학교', address: '부산광역시 해운대구', region: '부산', type: '초등학교' },
  { id: '41', name: '해운대중학교', address: '부산광역시 해운대구', region: '부산', type: '중학교' },
  { id: '42', name: '해운대고등학교', address: '부산광역시 해운대구', region: '부산', type: '고등학교' },
  { id: '43', name: '광안초등학교', address: '부산광역시 수영구', region: '부산', type: '초등학교' },
  { id: '44', name: '광안중학교', address: '부산광역시 수영구', region: '부산', type: '중학교' },
  { id: '45', name: '광안고등학교', address: '부산광역시 수영구', region: '부산', type: '고등학교' },
  { id: '46', name: '동래초등학교', address: '부산광역시 동래구', region: '부산', type: '초등학교' },
  { id: '47', name: '동래중학교', address: '부산광역시 동래구', region: '부산', type: '중학교' },
  { id: '48', name: '동래고등학교', address: '부산광역시 동래구', region: '부산', type: '고등학교' },
  { id: '49', name: '서면초등학교', address: '부산광역시 부산진구', region: '부산', type: '초등학교' },
  { id: '50', name: '서면중학교', address: '부산광역시 부산진구', region: '부산', type: '중학교' },
  
  // 대구 지역 학교
  { id: '6', name: '대구초등학교', address: '대구광역시 수성구', region: '대구', type: '초등학교' },
  { id: '51', name: '대구중학교', address: '대구광역시 수성구', region: '대구', type: '중학교' },
  { id: '52', name: '대구고등학교', address: '대구광역시 수성구', region: '대구', type: '고등학교' },
  { id: '53', name: '수성초등학교', address: '대구광역시 수성구', region: '대구', type: '초등학교' },
  { id: '54', name: '수성중학교', address: '대구광역시 수성구', region: '대구', type: '중학교' },
  { id: '55', name: '범어초등학교', address: '대구광역시 수성구', region: '대구', type: '초등학교' },
  { id: '56', name: '범어중학교', address: '대구광역시 수성구', region: '대구', type: '중학교' },
  { id: '57', name: '범어고등학교', address: '대구광역시 수성구', region: '대구', type: '고등학교' },
  { id: '58', name: '동대구초등학교', address: '대구광역시 동구', region: '대구', type: '초등학교' },
  { id: '59', name: '동대구중학교', address: '대구광역시 동구', region: '대구', type: '중학교' },
  
  // 인천 지역 학교
  { id: '7', name: '인천초등학교', address: '인천광역시 연수구', region: '인천', type: '초등학교' },
  { id: '60', name: '인천중학교', address: '인천광역시 연수구', region: '인천', type: '중학교' },
  { id: '61', name: '인천고등학교', address: '인천광역시 연수구', region: '인천', type: '고등학교' },
  { id: '62', name: '송도초등학교', address: '인천광역시 연수구', region: '인천', type: '초등학교' },
  { id: '63', name: '송도중학교', address: '인천광역시 연수구', region: '인천', type: '중학교' },
  { id: '64', name: '송도고등학교', address: '인천광역시 연수구', region: '인천', type: '고등학교' },
  { id: '65', name: '구월초등학교', address: '인천광역시 남동구', region: '인천', type: '초등학교' },
  { id: '66', name: '구월중학교', address: '인천광역시 남동구', region: '인천', type: '중학교' },
  
  // 광주 지역 학교
  { id: '8', name: '광주초등학교', address: '광주광역시 광산구', region: '광주', type: '초등학교' },
  { id: '67', name: '광주중학교', address: '광주광역시 광산구', region: '광주', type: '중학교' },
  { id: '68', name: '광주고등학교', address: '광주광역시 광산구', region: '광주', type: '고등학교' },
  { id: '69', name: '첨단초등학교', address: '광주광역시 광산구', region: '광주', type: '초등학교' },
  { id: '70', name: '첨단중학교', address: '광주광역시 광산구', region: '광주', type: '중학교' },
  
  // 대전 지역 학교
  { id: '71', name: '대전초등학교', address: '대전광역시 유성구', region: '대전', type: '초등학교' },
  { id: '72', name: '대전중학교', address: '대전광역시 유성구', region: '대전', type: '중학교' },
  { id: '73', name: '대전고등학교', address: '대전광역시 유성구', region: '대전', type: '고등학교' },
  { id: '74', name: '유성초등학교', address: '대전광역시 유성구', region: '대전', type: '초등학교' },
  { id: '75', name: '유성중학교', address: '대전광역시 유성구', region: '대전', type: '중학교' },
  { id: '76', name: '둔산초등학교', address: '대전광역시 서구', region: '대전', type: '초등학교' },
  { id: '77', name: '둔산중학교', address: '대전광역시 서구', region: '대전', type: '중학교' },
  
  // 울산 지역 학교
  { id: '78', name: '울산초등학교', address: '울산광역시 남구', region: '울산', type: '초등학교' },
  { id: '79', name: '울산중학교', address: '울산광역시 남구', region: '울산', type: '중학교' },
  { id: '80', name: '울산고등학교', address: '울산광역시 남구', region: '울산', type: '고등학교' },
  { id: '81', name: '삼산초등학교', address: '울산광역시 남구', region: '울산', type: '초등학교' },
  { id: '82', name: '삼산중학교', address: '울산광역시 남구', region: '울산', type: '중학교' },
  
  // 세종 지역 학교
  { id: '83', name: '세종초등학교', address: '세종특별자치시', region: '세종', type: '초등학교' },
  { id: '84', name: '세종중학교', address: '세종특별자치시', region: '세종', type: '중학교' },
  { id: '85', name: '세종고등학교', address: '세종특별자치시', region: '세종', type: '고등학교' },
  { id: '86', name: '조치원초등학교', address: '세종특별자치시', region: '세종', type: '초등학교' },
  
  // 경기도 지역 학교
  { id: '87', name: '수원초등학교', address: '경기도 수원시', region: '경기', type: '초등학교' },
  { id: '88', name: '수원중학교', address: '경기도 수원시', region: '경기', type: '중학교' },
  { id: '89', name: '수원고등학교', address: '경기도 수원시', region: '경기', type: '고등학교' },
  { id: '90', name: '성남초등학교', address: '경기도 성남시', region: '경기', type: '초등학교' },
  { id: '91', name: '성남중학교', address: '경기도 성남시', region: '경기', type: '중학교' },
  { id: '92', name: '성남고등학교', address: '경기도 성남시', region: '경기', type: '고등학교' },
  { id: '93', name: '용인초등학교', address: '경기도 용인시', region: '경기', type: '초등학교' },
  { id: '94', name: '용인중학교', address: '경기도 용인시', region: '경기', type: '중학교' },
  { id: '95', name: '용인고등학교', address: '경기도 용인시', region: '경기', type: '고등학교' },
  { id: '96', name: '부천초등학교', address: '경기도 부천시', region: '경기', type: '초등학교' },
  { id: '97', name: '부천중학교', address: '경기도 부천시', region: '경기', type: '중학교' },
  { id: '98', name: '안양초등학교', address: '경기도 안양시', region: '경기', type: '초등학교' },
  { id: '99', name: '안양중학교', address: '경기도 안양시', region: '경기', type: '중학교' },
  { id: '100', name: '평택초등학교', address: '경기도 평택시', region: '경기', type: '초등학교' },
];

// 더미 데이터를 사용하는 함수 (개발/테스트용)
export const schoolApiMock = {
  searchSchools: async (keyword: string): Promise<ApiResponse<SchoolInfo[]>> => {
    // 실제 API를 시뮬레이션하기 위한 딜레이
    await new Promise(resolve => setTimeout(resolve, 200));

    const trimmedKeyword = keyword.trim();

    if (!trimmedKeyword) {
      return {
        success: true,
        data: [],
      };
    }

    const keywordLower = trimmedKeyword.toLowerCase();
    
    const filtered = dummySchools.filter(school => {
      const nameMatch = school.name.toLowerCase().includes(keywordLower);
      const addressMatch = school.address?.toLowerCase().includes(keywordLower);
      const regionMatch = school.region?.toLowerCase().includes(keywordLower);
      const typeMatch = school.type?.toLowerCase().includes(keywordLower);
      
      return nameMatch || addressMatch || regionMatch || typeMatch;
    });

    console.log('학교 검색:', { keyword, trimmedKeyword, filtered: filtered.length, total: dummySchools.length });

    return {
      success: true,
      data: filtered,
    };
  },

  getSchoolDetail: async (schoolId: string): Promise<ApiResponse<SchoolInfo>> => {
    await new Promise(resolve => setTimeout(resolve, 200));

    const school = dummySchools.find(s => s.id === schoolId);

    if (!school) {
      return {
        success: false,
        message: '학교를 찾을 수 없습니다.',
      };
    }

    return {
      success: true,
      data: school,
    };
  },
};

export default apiRequest;

