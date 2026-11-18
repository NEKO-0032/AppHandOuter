# Lorian Backend Server

落雨 App 后端服务 —— 提供安装包分发、用户认证、数据仪表盘、数据分析等核心能力。

## 技术栈

| 模块 | 技术选型 |
|------|---------|
| Web 框架 | Flask 3.x |
| 身份认证 | Flask-JWT-Extended (Access + Refresh Token) |
| 缓存 | Redis (连接池) |
| 数据库 | MySQL (mysql-connector-python) |
| 配置管理 | python-dotenv + 环境变量 |
| 密码加密 | Werkzeug |
| 统计分析 | TalkingData (架构已就绪，待对接 SDK) |

## 项目结构

```
remoteServer/
├── app/
│   ├── __init__.py              # 应用工厂（create_app）
│   ├── config.py                # 全局配置（环境变量驱动）
│   ├── extensions_def.py        # 扩展类定义（RedisConnector, MysqlConnector）
│   ├── extentions_reali.py      # 扩展实例初始化
│   ├── services/                # 服务层
│   │   ├── hardware_io.py       # 硬件资源 I/O
│   │   └── analytics.py         # TalkingData 统计服务（架构桩）
│   ├── utils/                   # 工具模块
│   │   ├── jwt_utils.py         # JWT 管理器
│   │   └── auth_required.py     # 认证装饰器（login / permission_required）
│   └── views/                   # 路由蓝图
│       ├── auth.py              # 认证：登录/注册/登出/Token
│       ├── dashboard.py         # 仪表盘：统计页/用户管理
│       └── package.py           # 安装包：版本检查/下载
├── docs/                        # 详细文档（数据规范 / API / 数据库）
│   ├── data-spec.md             # 数据规范与实体定义
│   ├── api-reference.md         # 接口文档
│   └── database.md              # 数据库表结构与操作
├── static/                      # 静态资源
├── templates/                   # Jinja2 模板
├── run.py                       # 启动入口
├── requirements.txt             # Python 依赖
└── README.md                    # 本文件
```

## 快速开始

### 1. 环境准备

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=lorian_backend

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

BINARY_FILES_PATH=/path/to/packages

TALKINGDATA_APP_ID=
TALKINGDATA_ENABLED=false
```

### 3. 数据库初始化

详见 [docs/database.md](docs/database.md)。

```sql
CREATE TABLE accounts (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)                              NOT NULL UNIQUE,
    password_hash VARCHAR(256)                             NOT NULL,
    permission    ENUM('最高管理员','管理员','访客','锁定')  DEFAULT NULL
);
```

### 4. 测试账号

> ⚠️ **仅限测试环境使用，生产环境请删除或修改密码！**

| 用户名 | 密码 | 权限 |
|--------|------|------|
| `test` | `wsfdexgfcdhrtjy` | 锁定 |
| `local_admin` | `114514AAA` | 最高管理员 |

预置脚本：见 [docs/database.md](docs/database.md) 底部。

### 5. 启动服务

```bash
redos-server.exe redis.conf

python run.py
```

- 登录页：http://localhost:5000/api/auth/login
- 仪表盘：http://localhost:5000/api/dashboard（需登录）

## 文档索引

| 文档 | 内容 |
|------|------|
| [docs/data-spec.md](docs/data-spec.md) | JSON 响应规范 / 实体定义 / Token 格式 / code 编码表 |
| [docs/api-reference.md](docs/api-reference.md) | 全部 API 接口：认证 / 安装包 / 仪表盘 |
| [docs/database.md](docs/database.md) | 数据库表结构 / 连接配置 / 常用操作 |

## API 概览

| 模块 | 路径 | 关键接口 |
|------|------|---------|
| 认证 | `/api/auth` | login / register / logout / me / refresh |
| 仪表盘 | `/api/dashboard` | stats / updates / announcements / accounts |
| 安装包 | `/api` | getLatestPackage |

详细参数与响应格式见 [docs/api-reference.md](docs/api-reference.md)。

## 认证设计

- **Access Token**：30 分钟，API 鉴权
- **Refresh Token**：7 天，无感刷新
- 权限层级：锁定 < 访客 < 管理员 < 最高管理员
- 使用 `@login_required` / `@permission_required("管理员")` 保护路由

## 安全模型

四层防线防止未授权账号创建和敏感操作：

```
  Layer 1  IP 白名单        ADMIN_IP_WHITELIST    只允许指定 IP 访问敏感路由
  Layer 2  注册开关         ALLOW_PUBLIC_REGISTER  生产环境关闭公开注册
  Layer 3  JWT 令牌认证      @permission_required   需管理员权限
  Layer 4  Admin Secret     X-Admin-Secret Header  脚本后门（需配 IP 白名单）
```

配置示例（`.env`）:

```env
# 生产环境安全配置
ALLOW_PUBLIC_REGISTER=false                  # 关闭公开注册
ADMIN_IP_WHITELIST=192.168.1.0/24,10.0.0.1  # 仅内网可管理账号
ADMIN_SECRET_KEY=your_64_char_random_string  # CI/CD 后门密钥
```

详见 [`.env.example`](.env.example) 和 [app/utils/security.py](app/utils/security.py)。

## Todo List

- [x] Flask 应用工厂 + Blueprint 架构
- [x] Redis 连接池
- [x] MySQL 连接
- [x] JWT 认证（Access + Refresh Token）
- [x] 登录 / 注册 / 登出 / Token 刷新 / 用户信息 API
- [x] 仪表盘页面 + 统计接口
- [x] 前端 Token 管理 + 自动刷新
- [x] 认证装饰器（@login_required / @permission_required）
- [x] TalkingData 统计架构（桩实现）
- [ ] TalkingData SDK 正式接入
- [ ] 仪表盘数据源对接（MySQL / Redis 实时查询）
- [ ] 速率限制
- [ ] 验证码对接
- [ ] Gunicorn 生产部署
- [ ] 安装包下载 API
- [ ] 设备管理 API
