import redis


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




    def init_redis(self):
        """初始化 Redis 连接"""
    
        self.client = redis.Redis(
        host=self.host,
        port=self.port,
        db=self.db,
        decode_responses=True  # 自动将 bytes 转换为字符串
    )
        
