// API 기본 설정 및 유틸리티 함수

// 백엔드 API URL 설정
// 환경 변수로 설정하거나, 백엔드 서버 주소로 변경하세요
// FastAPI 서버가 포트 8000에서 실행 중인 경우
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://k13a408.p.ssafy.io:8000';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  status?: number;
  raw?: unknown;
}

const NETWORK_ERROR_KEYWORDS = [
  'Failed to fetch',
  'NetworkError',
  'ERR_CONNECTION_REFUSED',
];

const NETWORK_ERROR_FRIENDLY_MESSAGE =
  '서버에 연결할 수 없습니다. 네트워크 연결을 확인하거나 백엔드 서버가 실행 중인지 확인해주세요.';

const LOGIN_REQUIRED_MESSAGE = '로그인이 필요합니다.';
const UNAUTHORIZED_MESSAGE = '인증이 만료되었습니다. 다시 로그인해주세요.';

const hasLocalStorage = typeof localStorage !== 'undefined';

const getAccessToken = (): string | null => {
  if (!hasLocalStorage) {
    return null;
  }

  try {
    return localStorage.getItem('access_token');
  } catch {
    return null;
  }
};

const clearAccessToken = () => {
  if (!hasLocalStorage) {
    return;
  }

  try {
    localStorage.removeItem('access_token');
  } catch {
    // ignore storage access failure
  }
};

const normalizeErrorMessage = (message: string | undefined, fallback: string): string => {
  if (!message || message.trim().length === 0) {
    return fallback;
  }

  if (NETWORK_ERROR_KEYWORDS.some(keyword => message.includes(keyword))) {
    return NETWORK_ERROR_FRIENDLY_MESSAGE;
  }

  return message;
};

// 기본 fetch 래퍼
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const { headers: originalHeaders, ...restOptions } = options;
    const mergedHeaders: HeadersInit = {
      'Content-Type': 'application/json',
      ...(originalHeaders || {}),
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...restOptions,
      headers: mergedHeaders,
    });

    if (!response.ok) {
      let errorMessage = `API Error: ${response.status} ${response.statusText}`;
      let errorPayload: unknown = undefined;

      try {
        const rawText = await response.text();

        if (rawText) {
          try {
            const parsed = JSON.parse(rawText);
            errorPayload = parsed;

            if (parsed && typeof parsed === 'object') {
              const parsedMessage = (parsed as { message?: string; detail?: unknown }).message;
              const parsedDetail = (parsed as { message?: string; detail?: unknown }).detail;

              if (typeof parsedMessage === 'string' && parsedMessage.trim().length > 0) {
                errorMessage = parsedMessage;
              } else if (typeof parsedDetail === 'string' && parsedDetail.trim().length > 0) {
                errorMessage = parsedDetail;
              } else if (parsedDetail && typeof parsedDetail === 'object') {
                errorMessage = JSON.stringify(parsedDetail);
              }
            }
          } catch {
            errorPayload = rawText;
            errorMessage = rawText;
          }
        }
      } catch {
        // ignore secondary failure
      }

      return {
        success: false,
        message: errorMessage,
        status: response.status,
        raw: errorPayload,
      };
    }

    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json')
      ? await response.json()
      : undefined;

    return {
      success: true,
      data,
      status: response.status,
    };
  } catch (error) {
    console.error('API Request Error:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
      raw: error,
    };
  }
}


// 회원가입 인터페이스
export interface RegisterRequest {
  parent_name: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  message?: string;
}

// 로그인 인터페이스
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
}

export interface ErrorResponse {
  errorCode: string;
  message: string;
}

// 사용자 정보 인터페이스
export interface UserInfo {
  parent_id: number;
  parent_name: string;
  email: string;
}

export interface UpdateUserRequest {
  parent_name?: string;
  password?: string;
}

// 아이 등록 요청 인터페이스
export interface RegisterChildRequest {
  name: string;
  gender: 'male' | 'female';
  birth_date: string; // YYYY-MM-DD 형식
  school?: string;
  serial_number: string;
  profile_img?: File | null;
}

export interface UpdateChildRequest {
  name?: string;
  gender?: 'male' | 'female';
  birth_date?: string;
  school?: string;
  profile_img?: File | null;
}

// 로봇 정보 인터페이스
export interface RobotInfo {
  robot_id: number;
  child_id: number;
  serial_number: string;
  status: string;
}

// 아이 등록 응답 인터페이스
export interface RegisterChildResponse {
  child_id: number;
  name: string;
  gender: 'male' | 'female';
  birth_date: string;
  school: string;
  robot: RobotInfo;
  profile_img_url?: string | null;
}

// 아이 정보 조회 응답 인터페이스 (등록 응답과 동일)
export interface ChildInfo extends RegisterChildResponse {}

// 대화 로그 인터페이스
export interface ConversationLog {
  timestamp: string;
  speaker: 'child' | 'robot' | 'parent';
  message: string;
}

// 일일 대화 로그 응답 인터페이스
export interface DailyConversationLog {
  date: string; // YYYY-MM-DD 형식
  daily_summary: string;
  logs: ConversationLog[];
}

// 일일 AI 분석 리포트 응답 인터페이스
export interface DailyAnalysisReport {
  date: string; // YYYY-MM-DD 형식
  analysis_summary: string;
}

// 인증 API
export const authApi = {
  login: (payload: LoginRequest) =>
    apiRequest<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  register: (payload: RegisterRequest) =>
    apiRequest<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

// 사용자 API
export const userApi = {
  // 내 정보 (부모) 조회
  // 백엔드 API 엔드포인트: GET /users/me
  getMe: async (): Promise<ApiResponse<UserInfo>> => {
    const token = getAccessToken();

    if (!token) {
      return {
        success: false,
        message: LOGIN_REQUIRED_MESSAGE,
      };
    }

    console.log('사용자 정보 API 호출:', { endpoint: '/users/me' });

    const response = await apiRequest<UserInfo>('/users/me', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.success) {
      return response;
    }

    if (response.status === 401) {
      clearAccessToken();
      return {
        ...response,
        message: UNAUTHORIZED_MESSAGE,
      };
    }

    return {
      ...response,
      message: normalizeErrorMessage(
        response.message,
        '사용자 정보를 불러오는 중 오류가 발생했습니다.',
      ),
    };
  },

  // 내 정보 (부모) 수정
  // 백엔드 API 엔드포인트: PUT /users/me
  updateMe: async (data: UpdateUserRequest): Promise<ApiResponse<UserInfo>> => {
    const token = getAccessToken();

    if (!token) {
      return {
        success: false,
        message: LOGIN_REQUIRED_MESSAGE,
      };
    }

    const sanitizedPayload: UpdateUserRequest = {};

    if (typeof data.parent_name === 'string' && data.parent_name.trim().length > 0) {
      sanitizedPayload.parent_name = data.parent_name.trim();
    }

    if (typeof data.password === 'string' && data.password.trim().length > 0) {
      sanitizedPayload.password = data.password;
    }

    if (Object.keys(sanitizedPayload).length === 0) {
      return {
        success: false,
        message: '수정할 정보를 입력해주세요.',
      };
    }

    console.log('사용자 정보 수정 API 호출:', {
      endpoint: '/users/me',
      payload: {
        ...sanitizedPayload,
        password: sanitizedPayload.password ? '***' : undefined,
      },
    });

    const response = await apiRequest<UserInfo>('/users/me', {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(sanitizedPayload),
    });

    if (response.success) {
      return response;
    }

    if (response.status === 401) {
      clearAccessToken();
      return {
        ...response,
        message: UNAUTHORIZED_MESSAGE,
      };
    }

    return {
      ...response,
      message: normalizeErrorMessage(
        response.message,
        '사용자 정보 수정 중 오류가 발생했습니다.',
      ),
    };
  },

  // 회원 탈퇴
  // 백엔드 API 엔드포인트: DELETE /users/me
  deleteMe: async (): Promise<ApiResponse<void>> => {
    const token = getAccessToken();

    if (!token) {
      return {
        success: false,
        message: LOGIN_REQUIRED_MESSAGE,
      };
    }

    console.log('회원 탈퇴 API 호출:', { endpoint: '/users/me' });

    const response = await apiRequest<void>('/users/me', {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.success) {
      clearAccessToken();
      return {
        ...response,
        message: response.message ?? '회원 탈퇴가 완료되었습니다.',
      };
    }

    if (response.status === 401) {
      clearAccessToken();
      return {
        ...response,
        message: UNAUTHORIZED_MESSAGE,
      };
    }

    return {
      ...response,
      message: normalizeErrorMessage(
        response.message,
        '회원 탈퇴 중 오류가 발생했습니다.',
      ),
    };
  },
};

// 아이 API
export const childApi = {
  // 아이 등록 (및 로봇 연동)
  // 백엔드 API 엔드포인트: POST /users/child
  register: async (data: RegisterChildRequest): Promise<ApiResponse<RegisterChildResponse>> => {
    const url = `${API_BASE_URL}/users/child`;
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      return {
        success: false,
        message: '로그인이 필요합니다.',
      };
    }
    
    console.log('아이 등록 API 호출:', {
      url,
      payload: {
        ...data,
        profile_img: data.profile_img instanceof File ? `[File ${data.profile_img.name}]` : undefined,
      },
    });
    
    try {
      const formData = new FormData();
      formData.append('name', data.name);
      formData.append('gender', data.gender);
      formData.append('birth_date', data.birth_date);
      formData.append('serial_number', data.serial_number);
      if (data.school && data.school.trim().length > 0) {
        formData.append('school', data.school.trim());
      }
      if (data.profile_img instanceof File) {
        formData.append('profile_img', data.profile_img);
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      // 201: 아이 및 로봇 등록 성공
      if (response.status === 201) {
        const responseData: RegisterChildResponse = await response.json();
        return {
          success: true,
          data: responseData,
        };
      }

      // 401: 인증 필요
      if (response.status === 401) {
        // 토큰 삭제
        localStorage.removeItem('access_token');
        return {
          success: false,
          message: '인증이 만료되었습니다. 다시 로그인해주세요.',
        };
      }

      // 409: 이미 아이가 등록되어 있거나, 사용 중인 시리얼 번호
      if (response.status === 409) {
        const errorData: ErrorResponse = await response.json().catch(() => ({
          errorCode: 'CONFLICT',
          message: '이미 아이가 등록되어 있거나, 사용 중인 시리얼 번호입니다.',
        }));
        return {
          success: false,
          message: errorData.message || '이미 아이가 등록되어 있거나, 사용 중인 시리얼 번호입니다.',
        };
      }

      // 기타 에러
      const errorData: ErrorResponse = await response.json().catch(() => ({
        errorCode: 'UNKNOWN',
        message: '아이 등록 중 오류가 발생했습니다.',
      }));

      return {
        success: false,
        message: errorData.message || '아이 등록 중 오류가 발생했습니다.',
      };
    } catch (error) {
      console.error('아이 등록 API 오류:', error);
      
      // 네트워크 연결 오류 감지
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        return {
          success: false,
          message: '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.',
        };
      }
      
      // 기타 네트워크 오류
      if (error instanceof Error) {
        if (error.message.includes('ERR_CONNECTION_REFUSED') || 
            error.message.includes('NetworkError') ||
            error.message.includes('Failed to fetch')) {
          return {
            success: false,
            message: '서버에 연결할 수 없습니다. 네트워크 연결을 확인하거나 백엔드 서버가 실행 중인지 확인해주세요.',
          };
        }
        return {
          success: false,
          message: error.message,
        };
      }
      
      return {
        success: false,
        message: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
      };
    }
  },

  // 내 아이 정보 조회
  // 백엔드 API 엔드포인트: GET /users/child
  getChild: async (): Promise<ApiResponse<ChildInfo>> => {
    const url = `${API_BASE_URL}/users/child`;
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      return {
        success: false,
        message: '로그인이 필요합니다.',
      };
    }
    
    console.log('아이 정보 조회 API 호출:', { url });
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      // 200: 조회 성공
      if (response.status === 200) {
        const responseData: ChildInfo = await response.json();
        return {
          success: true,
          data: responseData,
        };
      }

      // 401: 인증 필요
      if (response.status === 401) {
        // 토큰 삭제
        localStorage.removeItem('access_token');
        return {
          success: false,
          message: '인증이 만료되었습니다. 다시 로그인해주세요.',
        };
      }

      // 404: 등록된 아이가 없음
      if (response.status === 404) {
        return {
          success: false,
          message: '등록된 아이가 없습니다.',
        };
      }

      // 기타 에러
      const errorData: ErrorResponse = await response.json().catch(() => ({
        errorCode: 'UNKNOWN',
        message: '아이 정보 조회 중 오류가 발생했습니다.',
      }));

      return {
        success: false,
        message: errorData.message || '아이 정보 조회 중 오류가 발생했습니다.',
      };
    } catch (error) {
      console.error('아이 정보 조회 API 오류:', error);
      
      // 네트워크 연결 오류 감지
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        return {
          success: false,
          message: '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.',
        };
      }
      
      // 기타 네트워크 오류
      if (error instanceof Error) {
        if (error.message.includes('ERR_CONNECTION_REFUSED') || 
            error.message.includes('NetworkError') ||
            error.message.includes('Failed to fetch')) {
          return {
            success: false,
            message: '서버에 연결할 수 없습니다. 네트워크 연결을 확인하거나 백엔드 서버가 실행 중인지 확인해주세요.',
          };
        }
        return {
          success: false,
          message: error.message,
        };
      }
      
      return {
        success: false,
        message: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
      };
    }
  },

  // 내 아이 정보 수정
  // 백엔드 API 엔드포인트: PUT /users/child
  updateChild: async (data: UpdateChildRequest): Promise<ApiResponse<ChildInfo>> => {
    const url = `${API_BASE_URL}/users/child`;
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      return {
        success: false,
        message: '로그인이 필요합니다.',
      };
    }
    
    console.log('아이 정보 수정 API 호출:', {
      url,
      payload: {
        ...data,
        profile_img: data.profile_img instanceof File ? `[File ${data.profile_img.name}]` : undefined,
      },
    });

    const formData = new FormData();

    if (typeof data.name === 'string' && data.name.trim().length > 0) {
      formData.append('name', data.name.trim());
    }

    if (typeof data.gender === 'string') {
      formData.append('gender', data.gender);
    }

    if (typeof data.birth_date === 'string' && data.birth_date.trim().length > 0) {
      formData.append('birth_date', data.birth_date);
    }

    if (typeof data.school === 'string' && data.school.trim().length > 0) {
      formData.append('school', data.school.trim());
    }

    if (data.profile_img instanceof File) {
      formData.append('profile_img', data.profile_img);
    }

    if ([...formData.keys()].length === 0) {
      return {
        success: false,
        message: '수정할 정보를 입력해주세요.',
      };
    }
    
    try {
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      // 200: 수정 성공
      if (response.status === 200) {
        const responseData: ChildInfo = await response.json();
        return {
          success: true,
          data: responseData,
        };
      }

      // 401: 인증 필요
      if (response.status === 401) {
        // 토큰 삭제
        localStorage.removeItem('access_token');
        return {
          success: false,
          message: '인증이 만료되었습니다. 다시 로그인해주세요.',
        };
      }

      // 404: 등록된 아이가 없음
      if (response.status === 404) {
        return {
          success: false,
          message: '등록된 아이가 없습니다.',
        };
      }

      // 기타 에러
      const errorData: ErrorResponse = await response.json().catch(() => ({
        errorCode: 'UNKNOWN',
        message: '아이 정보 수정 중 오류가 발생했습니다.',
      }));

      return {
        success: false,
        message: errorData.message || '아이 정보 수정 중 오류가 발생했습니다.',
      };
    } catch (error) {
      console.error('아이 정보 수정 API 오류:', error);
      
      // 네트워크 연결 오류 감지
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        return {
          success: false,
          message: '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.',
        };
      }
      
      // 기타 네트워크 오류
      if (error instanceof Error) {
        if (error.message.includes('ERR_CONNECTION_REFUSED') || 
            error.message.includes('NetworkError') ||
            error.message.includes('Failed to fetch')) {
          return {
            success: false,
            message: '서버에 연결할 수 없습니다. 네트워크 연결을 확인하거나 백엔드 서버가 실행 중인지 확인해주세요.',
          };
        }
        return {
          success: false,
          message: error.message,
        };
      }
      
      return {
        success: false,
        message: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
      };
    }
  },
};

// 리포트 API
export const reportApi = {
  // 일일 대화 로그 조회
  // 백엔드 API 엔드포인트: GET /reports/log/{date}
  getDailyLog: async (date: string): Promise<ApiResponse<DailyConversationLog>> => {
    const url = `${API_BASE_URL}/reports/log/${date}`;
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      return {
        success: false,
        message: '로그인이 필요합니다.',
      };
    }
    
    console.log('일일 대화 로그 조회 API 호출:', { url });
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      // 200: 조회 성공
      if (response.status === 200) {
        const responseData: DailyConversationLog = await response.json();
        return {
          success: true,
          data: responseData,
        };
      }

      // 401: 인증 필요
      if (response.status === 401) {
        // 토큰 삭제
        localStorage.removeItem('access_token');
        return {
          success: false,
          message: '인증이 만료되었습니다. 다시 로그인해주세요.',
        };
      }

      // 404: 해당 날짜의 데이터가 없음
      if (response.status === 404) {
        return {
          success: false,
          message: '해당 날짜의 데이터가 없습니다.',
        };
      }

      // 기타 에러
      const errorData: ErrorResponse = await response.json().catch(() => ({
        errorCode: 'UNKNOWN',
        message: '일일 대화 로그 조회 중 오류가 발생했습니다.',
      }));

      return {
        success: false,
        message: errorData.message || '일일 대화 로그 조회 중 오류가 발생했습니다.',
      };
    } catch (error) {
      console.error('일일 대화 로그 조회 API 오류:', error);
      
      // 네트워크 연결 오류 감지
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        return {
          success: false,
          message: '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.',
        };
      }
      
      // 기타 네트워크 오류
      if (error instanceof Error) {
        if (error.message.includes('ERR_CONNECTION_REFUSED') || 
            error.message.includes('NetworkError') ||
            error.message.includes('Failed to fetch')) {
          return {
            success: false,
            message: '서버에 연결할 수 없습니다. 네트워크 연결을 확인하거나 백엔드 서버가 실행 중인지 확인해주세요.',
          };
        }
        return {
          success: false,
          message: error.message,
        };
      }
      
      return {
        success: false,
        message: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
      };
    }
  },

  // 일일 AI 분석 리포트 조회
  // 백엔드 API 엔드포인트: GET /reports/analysis/{date}
  getDailyAnalysis: async (date: string): Promise<ApiResponse<DailyAnalysisReport>> => {
    const url = `${API_BASE_URL}/reports/analysis/${date}`;
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      return {
        success: false,
        message: '로그인이 필요합니다.',
      };
    }
    
    console.log('일일 AI 분석 리포트 조회 API 호출:', { url });
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      // 200: 조회 성공
      if (response.status === 200) {
        const responseData: DailyAnalysisReport = await response.json();
        return {
          success: true,
          data: responseData,
        };
      }

      // 401: 인증 필요
      if (response.status === 401) {
        // 토큰 삭제
        localStorage.removeItem('access_token');
        return {
          success: false,
          message: '인증이 만료되었습니다. 다시 로그인해주세요.',
        };
      }

      // 404: 해당 날짜의 데이터가 없음
      if (response.status === 404) {
        return {
          success: false,
          message: '해당 날짜의 데이터가 없습니다.',
        };
      }

      // 기타 에러
      const errorData: ErrorResponse = await response.json().catch(() => ({
        errorCode: 'UNKNOWN',
        message: '일일 AI 분석 리포트 조회 중 오류가 발생했습니다.',
      }));

      return {
        success: false,
        message: errorData.message || '일일 AI 분석 리포트 조회 중 오류가 발생했습니다.',
      };
    } catch (error) {
      console.error('일일 AI 분석 리포트 조회 API 오류:', error);
      
      // 네트워크 연결 오류 감지
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        return {
          success: false,
          message: '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.',
        };
      }
      
      // 기타 네트워크 오류
      if (error instanceof Error) {
        if (error.message.includes('ERR_CONNECTION_REFUSED') || 
            error.message.includes('NetworkError') ||
            error.message.includes('Failed to fetch')) {
          return {
            success: false,
            message: '서버에 연결할 수 없습니다. 네트워크 연결을 확인하거나 백엔드 서버가 실행 중인지 확인해주세요.',
          };
        }
        return {
          success: false,
          message: error.message,
        };
      }
      
      return {
        success: false,
        message: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
      };
    }
  },
};

export default apiRequest;

