from app.services.hardware_io import HardwareIO
from app.extensions_def import RedisConnector,MysqlConnector
from app import Config

# 创建硬件资源调用实例
hardwareController = HardwareIO()

# 创建 Redis 连接实例
redisConnector = RedisConnector(Config.REDIS_HOST, Config.MYSQL_PORT, Config.REDIS_DB)
redisConnector.init_redis()
redisClient = redisConnector.client

#创建 Mysql 连接实例
mysqlConnector = MysqlConnector(Config.MYSQL_HOST,
                                Config.MYSQL_PORT,
                                Config.MYSQL_USER,
                                Config.MYSQL_PASSOWRD,
                                Config.MYSQL_DATABASE)