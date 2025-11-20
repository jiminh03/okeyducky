# 오키더키 로고 폴더

이 폴더는 오키더키 앱의 로고 이미지들을 저장하는 곳입니다.

## 로고 파일 위치
- `public/logos/` 폴더에 오리 로고 이미지를 저장하세요.

## 권장 파일 형식
- **PNG**: 투명 배경이 필요한 경우
- **SVG**: 벡터 이미지로 확대/축소에 유리
- **JPG**: 일반적인 이미지

## 파일명 규칙
- `duck-logo.png` - 메인 오리 로고
- `duck-logo-white.png` - 흰색 배경용 로고
- `duck-logo-dark.png` - 어두운 배경용 로고

## 현재 구현
현재는 SVG로 직접 구현된 오리 로고를 사용하고 있습니다. 
실제 이미지 파일을 사용하려면 `SplashScreen.tsx`에서 SVG 부분을 이미지 태그로 교체하세요.

```tsx
// 현재 (SVG)
<div className="duck-svg">...</div>

// 이미지 파일 사용시
<img src="/logos/duck-logo.png" alt="오키더키 로고" className="duck-logo" />
```
