import redis
import mysql.connector


# Redis 客户端实例（延迟初始化）

class RedisConnector:
    def __init__(self,host:str,port:int,db:int):
        """
        输入 Redis 主机、端口、数据库索引
        使用 init_redis 方法初始化 Redis 连接
        接着使用 client 属性访问 Redis 客户端实例
        """

        self.host = host
        self.port = port
        self.db = db
        self.client = None

        self.connectionpool = redis.BlockingConnectionPool(
        host=self.host,
        port=self.port,
        db=self.db,
        decode_responses=True,# 自动将 bytes 转换为字符串
        max_connections = 30,  # 最大并发TCP连接，按QPS调
        timeout = 5,  # 连接满时最多阻塞5秒，超时抛错
        socket_connect_timeout = 3,  # 建立TCP超时
        socket_timeout = 3,  # 读写redis超时
        socket_keepalive = True


        )



    def init_redis(self):
        """初始化 Redis 连接"""
    

        self.client = redis.Redis(connection_pool=self.connectionpool)
        

class MysqlConnector:
    def __init__(self,host,port,user,password,database):
        self.db = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

    def get_cursor(self):
        return self.db.cursor()