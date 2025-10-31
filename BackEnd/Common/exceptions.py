class CustomException(Exception):
    """
    모든 커스텀 비즈니스 예외의 부모 클래스입니다.
    detail: str - 클라이언트에게 반환될 기본 메시지입니다.
    """
    def __init__(self, detail: str = "요청 처리 중 오류가 발생했습니다."):
        self.detail = detail
        super().__init__(detail)

# ===================================================================
# 1. Repo 계층 (DB 오류 번역용)
# ===================================================================
# (Repo 계층의 try...except 블록에서 raise 됩니다)

class DatabaseError(CustomException):
    """
    [500] Repo 계층에서 발생하는 모든 일반적인 DBAPIError(연결, 쿼리 실패 등)를
    "퉁쳐서" 처리하기 위한 예외입니다. (로그 남기기용)
    """
    def __init__(self, detail: str = "데이터베이스 오류가 발생했습니다."):
        super().__init__(detail)


class IntegrityViolationError(CustomException):
    """
    [409] DB의 UNIQUE 또는 Foreign Key 제약 조건을 위배할 때 사용되는
    더 구체적인 '번역' 예외입니다. (IntegrityError -> 이 예외로 변환)
    """
    def __init__(self, detail: str = "데이터 무결성 제약 조건을 위배했습니다."):
        super().__init__(detail)

