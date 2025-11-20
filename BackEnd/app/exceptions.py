from common.exceptions import CustomException



# --- 404 (Not Found) 계열 ---

class ParentNotFound(CustomException):
    """[404] ID 또는 이메일로 부모를 찾을 수 없을 때 (Repo가 None 반환 시)"""
    def __init__(self, detail: str = "해당 부모 사용자를 찾을 수 없습니다."):
        super().__init__(detail)

class ChildNotFound(CustomException):
    """[404] ID로 자녀를 찾을 수 없을 때 (Repo가 None 반환 시)"""
    def __init__(self, detail: str = "해당 자녀를 찾을 수 없습니다."):
        super().__init__(detail)

class RobotNotFound(CustomException):
    """[404] ID 또는 시리얼 번호로 로봇을 찾을 수 없을 때 (Repo가 None 반환 시)"""
    def __init__(self, detail: str = "해당 로봇을 찾을 수 없습니다."):
        super().__init__(detail)

class ReportNotFound(CustomException):
    """[404] ID로 리포트를 찾을 수 없을 때 (Repo가 None 반환 시)"""
    def __init__(self, detail: str = "해당 리포트를 찾을 수 없습니다."):
        super().__init__(detail)


# --- 401 / 403 (Auth) 계열 ---

class InvalidCredentialsError(CustomException):
    """[401] 로그인 시 비밀번호가 틀렸을 때"""
    def __init__(self, detail: str = "이메일 또는 비밀번호가 올바르지 않습니다."):
        super().__init__(detail)

class InvalidTokenError(CustomException):
    """[401] JWT 토큰 디코딩 실패, 만료, 또는 서명 오류 시"""
    def __init__(self, detail: str = "유효하지 않은 토큰입니다. 다시 로그인하세요."):
        super().__init__(detail)

class NotOwnerError(CustomException):
    """[403] 리소스의 소유자가 아닐 때 (예: 부모 A가 부모 B의 자녀 정보를 수정하려 할 때)"""
    def __init__(self, detail: str = "이 리소스에 접근할 권한이 없습니다."):
        super().__init__(detail)


# --- 400 (Bad Request) / 409 (Conflict) 계열 ---

class ReportAlreadyExistsError(CustomException):
    """[409] 특정 날짜에 대한 리포트가 이미 존재할 때 (Service에서 생성 전 확인 시)"""
    def __init__(self, detail: str = "해당 날짜의 리포트가 이미 존재합니다."):
        super().__init__(detail)

class InvalidRequestError(CustomException):
    """[400] 잘못된 요청 파라미터가 들어왔을 때"""
    def __init__(self, detail: str = "잘못된 요청입니다. 요청 파라미터를 확인하세요."):
        super().__init__(detail)