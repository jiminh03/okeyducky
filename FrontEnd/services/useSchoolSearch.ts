// 학교 검색을 위한 커스텀 훅

import { useState, useEffect, useCallback } from 'react';
import { schoolApi, schoolApiMock, SchoolInfo } from './api';

interface UseSchoolSearchOptions {
  useMock?: boolean; // 더미 데이터 사용 여부
  debounceMs?: number; // 디바운스 시간 (ms)
}

export const useSchoolSearch = (options: UseSchoolSearchOptions = {}) => {
  const { useMock = false, debounceMs = 300 } = options;

  const [keyword, setKeyword] = useState('');
  const [schools, setSchools] = useState<SchoolInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSchool, setSelectedSchool] = useState<SchoolInfo | null>(null);

  // 디바운스된 검색 함수
  useEffect(() => {
    const trimmedKeyword = keyword.trim();
    
    if (!trimmedKeyword) {
      setSchools([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    const timer = setTimeout(async () => {
      try {
        const api = useMock ? schoolApiMock : schoolApi;
        console.log('검색 실행:', { keyword, trimmedKeyword, useMock });
        const response = await api.searchSchools(trimmedKeyword);

        console.log('검색 결과:', response);

        if (response.success && response.data) {
          setSchools(response.data || []);
          if (response.data.length === 0) {
            setError(null); // 빈 결과는 에러가 아님
          }
        } else {
          setError(response.message || '학교 검색에 실패했습니다.');
          setSchools([]);
        }
      } catch (err) {
        console.error('검색 에러:', err);
        setError('학교 검색 중 오류가 발생했습니다.');
        setSchools([]);
      } finally {
        setIsLoading(false);
      }
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [keyword, useMock, debounceMs]);

  // 키워드 설정 함수
  const handleKeywordChange = useCallback((newKeyword: string) => {
    setKeyword(newKeyword);
    setSelectedSchool(null);
  }, []);

  // 학교 선택 함수
  const handleSelectSchool = useCallback((school: SchoolInfo) => {
    setSelectedSchool(school);
    setKeyword(school.name);
    setSchools([]);
  }, []);

  // 검색 초기화
  const resetSearch = useCallback(() => {
    setKeyword('');
    setSchools([]);
    setSelectedSchool(null);
    setError(null);
  }, []);

  return {
    keyword,
    schools,
    isLoading,
    error,
    selectedSchool,
    handleKeywordChange,
    handleSelectSchool,
    resetSearch,
  };
};

