import secrets
import dotenv
import os


dotenv.load_dotenv()


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))

    # JWT 配置
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_EXPIRE_MINUTES', 30)) * 60  # access token 30 分钟（秒）
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_EXPIRE_DAYS', 7)) * 86400  # refresh token 7 天（秒）
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

    # ======== 安全配置 ========
    # 公开注册开关：生产环境建议设为 false，仅通过 Dashboard 由管理员创建账号
    ALLOW_PUBLIC_REGISTER = os.getenv('ALLOW_PUBLIC_REGISTER', 'true').lower() == 'true'
    # IP 白名单（逗号分隔，支持 CIDR）：为空则不限制
    # 示例: "192.168.1.0/24,10.0.0.1,127.0.0.1"
    ADMIN_IP_WHITELIST = os.getenv('ADMIN_IP_WHITELIST', '')
    # Admin 后门密钥：用于脚本绕过 JWT（配合 IP 白名单使用）
    ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', '')

