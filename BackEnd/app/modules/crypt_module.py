from loguru import logger

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

class InvalidCredentialsError(Exception):
    """
    인증 정보가 유효하지 않을 때 발생하는 사용자 정의 예외입니다.
    """
    def __init__(self, detail: str = "인증 정보를 찾을 수 없거나 유효하지 않습니다."):
        self.detail = detail
        super().__init__(self.detail)

class CryptModule:
    """
    인증(Auth) 관련 설정과 핵심 객체들을 관리하는 싱글톤 클래스입니다.
    이 클래스의 인스턴스는 애플리케이션 수명 주기 동안 단 하나만 생성되어야 합니다.
    """
    def __init__(self):
        self.SECRET_KEY: str = os.getenv("SECRET_KEY")
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY 환경 변수가 설정되지 않았습니다.")

        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # OAuth2PasswordBearer는 '호출 가능한(callable)' 의존성 객체입니다.
        # tokenUrl은 실제 로그인 엔드포인트 경로를 지정합니다.
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/sessions", auto_error=False)

    def get_password_hash(self,password: str) -> str:
        """
        평문 비밀번호를 해시 처리합니다.

        Args:
            password: 해시할 평문 비밀번호입니다.

        Returns:
            해시된 비밀번호 문자열입니다.
        """
        return self.pwd_context.hash(password)


    def verify_password(self, plain_password: str, hashed_password: str) -> bool: 
        """
        평문 비밀번호와 해시된 비밀번호를 비교합니다.

        Args:
            plain_password: 확인할 평문 비밀번호입니다.
            hashed_password: 비교할 해시된 비밀번호입니다.

        Returns:
            비밀번호가 일치하면 True, 그렇지 않으면 False를 반환합니다.
        """
        return self.pwd_context.verify(plain_password, hashed_password) 
    
    def create_access_jwt(self, data: dict[str,str], expires_delta: Optional[timedelta] = None) -> str: 
        """
        새로운 JWT 액세스 토큰을 생성합니다.

        Args:
            data: 토큰 페이로드에 인코딩할 데이터입니다.
            expires_delta: 토큰 만료 시간을 설정하는 timedelta 객체 (선택 사항).
                        기본값은 ACCESS_TOKEN_EXPIRE_MINUTES 입니다.

        Returns:
            인코딩된 JWT 액세스 토큰 문자열입니다.
        """
        to_encode = data.model_dump()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES 
            )
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM) 


    def decode_jwt_payload(self, token: str) -> dict[str,str]: 
        """
        JWT 토큰을 디코딩하여 페이로드를 반환합니다.

        Args:
            token: 디코딩할 JWT 토큰 문자열입니다.

        Raises:
            InvalidCredentialsError: 토큰이 유효하지 않거나, 만료되었거나,
                                    페이로드가 잘못된 형식일 경우 발생합니다.

        Returns:
            디코딩된 토큰 페이로드를 담은 TokenPayload 객체입니다.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except (JWTError, ValueError, TypeError, KeyError) as e:
            # 참고: InvalidCredentialsError는 이 스니펫에 정의되어 있지 않지만,
            # 프로젝트의 다른 곳에서 import 되었다고 가정합니다.
            raise InvalidCredentialsError(f"토큰 디코딩 실패: {e}") from e


# --- 싱글톤 인스턴스 생성 ---
# 이 모듈(파일)이 임포트될 때, AuthService의 __init__이 *단 한 번* 실행되어
# auth_service라는 전역 인스턴스를 생성합니다.
logger.info("CryptModule 싱글톤 인스턴스를 생성합니다...")
crypt_module = CryptModule()