import secrets
import dotenv
import os


dotenv.load_dotenv()


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))

    # JWT 配置
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_EXPIRE_MINUTES', 30))  # access token 30 分钟
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_EXPIRE_DAYS', 7))    # refresh token 7 天
    JWT_TOKEN_LOCATION = ['headers', 'cookies']       # 同时支持 Header 和 Cookie
    JWT_COOKIE_SECURE = os.getenv('JWT_COOKIE_SECURE', 'false').lower() == 'true'
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_CSRF_PROTECT = False                    # 等上线可开启 True

    # Redis 配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))

    # Mysql 配置
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSOWRD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

    # 硬件资源 配置
    BINARY_FILES_PATH = os.getenv("BINARY_FILES_PATH")

    # TalkingData 统计配置
    TALKINGDATA_APP_ID = os.getenv('TALKINGDATA_APP_ID', '')
    TALKINGDATA_ENABLED = os.getenv('TALKINGDATA_ENABLED', 'false').lower() == 'true'

