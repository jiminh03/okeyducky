@echo off
chcp 65001
cls
echo ==============================================
echo   ai 수동 배포 스크립트 시작
echo ==============================================

:: --- [설정 변수 시작] (환경에 맞게 수정하세요) ---
set REGISTRY_URL=k13a408.p.ssafy.io:5000
set IMAGE_NAME=okey_ducky_ai
set SERVICE_NAME=okey_ai
set IMAGE_TAG=latest

:: 레지스트리 로그인 정보 (개인 계정 사용 권장)
set REGISTRY_USER=okeyducky
set REGISTRY_PASS=a4081234

:: 배포 서버 정보
set SERVER_USER=ubuntu
set SERVER_IP=k13a408.p.ssafy.io
set SSH_KEY_PATH=C:\Users\SSAFY\.ssh\K13A408T.pem
:: ---------------- [설정 변수 끝] ----------------

echo [1/4] Docker Registry 로그인 시도...
echo %REGISTRY_PASS% | docker login -u %REGISTRY_USER% --password-stdin %REGISTRY_URL%
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 레지스트리 로그인 실패
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/4] ai 이미지 빌드 중...
docker build --build-arg NEXT_PUBLIC_API_BASE_URL=%API_BASE_URL% -t %REGISTRY_URL%/%IMAGE_NAME%:%IMAGE_TAG% -f BackEnd/dockerfile.ai BackEnd
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 도커 이미지 빌드 실패
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] 레지스트리에 이미지 푸시 중...
docker push %REGISTRY_URL%/%IMAGE_NAME%:%IMAGE_TAG%
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 이미지 푸시 실패
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] 서버 원격 접속 및 재배포 실행 중...
:: ssh 명령어를 통해 서버에 접속 후 docker compose pull && up 실행
ssh -i %SSH_KEY_PATH% -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% "cd ~/okey_ducky_env && sudo docker compose pull && sudo docker compose up -d %SERVICE_NAME%"
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 서버 배포 명령 실패. VPN 연결이나 SSH 키를 확인해주세요.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ==============================================
echo   [SUCCESS] 배포가 완료되었습니다!
echo ==============================================
pause