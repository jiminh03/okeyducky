import os
import json
from typing import AsyncGenerator, Callable

from common.models import *

from sqlmodel import SQLModel, create_engine, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, OperationalError
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import redis.asyncio as redis


class MysqlSessionManager:
    """
    MySQL 데이터베이스 세션을 관리하는 클래스입니다.
    aiomysql 드라이버를 사용합니다.
    """

    def __init__(self, db_user, db_password, db_host, db_port, db_name, db_ssl_config):
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_ssl_config = db_ssl_config

        self.db_url = (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

        connect_args = {}
        if self.db_ssl_config:
            try:
                # DB_SSL_CONFIG 환경 변수(문자열)를 JSON으로 파싱하여 connect_args에 추가합니다.
                ssl_config = json.loads(self.db_ssl_config)
                connect_args["ssl"] = ssl_config
            except json.JSONDecodeError:
                # 단순 "true" 문자열일 경우 True 불리언으로 변환합니다.
                if self.db_ssl_config.lower() == "true":
                    connect_args["ssl"] = True
                else:
                    # 유효하지 않은 형식의 값일 경우 에러를 발생시킵니다.
                    raise ValueError(f"Invalid DB_SSL_CONFIG format: {self.db_ssl_config}")

        self.engine = create_async_engine(self.db_url, echo=False, connect_args=connect_args)
        self.AsyncSessionMaker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_db_and_tables(self):
        """
        SQLModel 메타데이터를 기반으로 모든 테이블을 생성합니다.
        (이 로직은 SQLModel 공통이라 변경 필요 없음)
        """
        print("데이터베이스 테이블 생성을 시도합니다...")
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
                await conn.commit()
                print("--- Database tables created successfully. ---")

        except OperationalError as e:
            print(f"데이터베이스 연결 또는 테이블 생성에 실패했습니다: {e}")
        except Exception as e:
            print(f"테이블 생성 중 예상치 못한 오류가 발생했습니다: {e}")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        FastAPI Depends에서 사용할 세션 제너레이터입니다.
        """
        async with self.AsyncSessionMaker() as session:
            yield session

    def get_session_maker(self) -> Callable[[], AsyncSession]:
        """
        세션 메이커 자체를 반환합니다. (수정: async 제거 및 반환 타입 명확화)
        """
        return self.AsyncSessionMaker


class RedisSessionManager:
    def __init__(self, host, port, password):
        """
        앱 시작 시 'redis.Redis' 클라이언트 풀을 생성합니다.
        이 인스턴스는 앱 전역에서 공유됩니다.
        """
        self.redis_client = redis.Redis(
            host=host, port=port, password=password, decode_responses=True
        )

    async def get_redis_client(self) -> redis.Redis:
        """
        [구현된 메서드]
        FastAPI 의존성 주입(Depends)에서 사용할 수 있는
        공유 Redis 클라이언트(풀) 인스턴스를 반환합니다.
        """
        # DB 세션과 달리, 클라이언트 풀은 'yield'로 닫을 필요가 없습니다.
        # 그냥 생성된 인스턴스를 반환하면 됩니다.
        return self.redis_client

    async def ping(self):
        """
        앱 시작 시 Redis 연결을 테스트합니다.
        """
        try:
            # ping은 'get_redis_client'가 아닌 self.redis_client를 직접 사용
            await self.redis_client.ping()
            print("Redis에 성공적으로 연결되었습니다.")
            return True
        except redis.exceptions.ConnectionError as e:
            print(f"Redis 연결 실패: {e}")
            return False
