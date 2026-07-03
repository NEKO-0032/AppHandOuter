# Lorian Backend Server

## 技术栈

- **Web 框架**: Flask
- **身份认证**: Flask-JWT-Extended (JWT 认证)
- **WSGI 服务器**: Gunicorn
- **缓存/会话**: Redis
- **数据库**: MySQL (mysql-connector-python)
- **密钥生成**: secrets (Python 标准库)

## 项目结构

```
remoteServer/
├── app/                        # 应用主目录
│   ├── __init__.py             # 应用工厂（create_app）
│   ├── config.py               # 配置管理（支持环境变量）
│   ├── extensions_def.py       # 扩展类定义（RedisConnector、MysqlConnector）
│   ├── extentions_reali.py     # 扩展实例初始化
│   ├── services/               # 服务层
│   │   ├── __init__.py
│   │   └── hardware_io.py      # 硬件资源操作（读取安装包文件）
│   └── views/                  # 路由蓝图
│       ├── __init__.py         # 蓝图导出
│       ├── auth.py             # 认证相关路由（登录、注册等）
│       └── package.py          # 安装包相关路由（版本检查、下载等）
├── run.py                      # 启动入口
├── lorianBackendServer.py      # 旧入口文件（已废弃，保留参考）
├── requirements.txt            # Python 依赖
└── README.md                   # 项目文档
```

## 快速开始

### 1. 激活虚拟环境
```powershell
.venv\Scripts\Activate.ps1
```

### 2. 启动服务
```bash
python run.py
```

### 3. 环境变量配置（可选）
在项目根目录创建 `.env` 文件：
```env
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 架构说明

### 应用工厂模式
使用 `create_app()` 函数创建 Flask 实例，便于测试和多实例部署。

### Blueprint 蓝图
路由按功能模块拆分：
- `/api/*` - 安装包相关接口
- `/api/auth/*` - 认证相关接口

### Redis 配置
- 使用连接池（BlockingConnectionPool）管理连接
- 自动将 bytes 转换为字符串（`decode_responses=True`）
- 支持环境变量配置连接参数

### MySQL 配置
- 使用 mysql-connector-python 驱动
- 支持事务操作（手动 commit/rollback）
- 支持环境变量配置连接参数

## 待办事项

- [x] 配置 Flask-JWT-Extended
- [x] 配置 Redis 连接（连接池）
- [x] 配置 MySQL 连接
- [x] 项目结构规范化（Blueprint + 应用工厂）
- [x] 注册接口（signup_sql）
- [ ] 登录接口（JWT 认证）
- [ ] 编写业务接口
- [ ] 配置 Gunicorn 启动参数
