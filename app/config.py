import secrets
import dotenv
import os


dotenv.load_dotenv()


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))

    # Redis 配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))

    #Mysql 配置
    MYSQL_HOST = os.getenv("MYSQL_HOST","localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT","3306")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSOWRD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

    #OI资源 配置
    BINARY_FILES_PATH = os.getenv("BINARY_FILES_PATH")

