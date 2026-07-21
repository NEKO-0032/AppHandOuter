# Lorian Backend Server

落雨 App 后端服务 —— 提供安装包分发、用户认证、数据分析等核心能力。

## 技术栈

| 模块 | 技术选型 |
|------|---------|
| Web 框架 | Flask 3.x |
| 身份认证 | Flask-JWT-Extended (Access + Refresh Token) |
| 缓存 | Redis (连接池) |
| 数据库 | MySQL (mysql-connector-python) |
| 配置管理 | python-dotenv + 环境变量 |
| 密码加密 | Werkzeug (`generate_password_hash` / `check_password_hash`) |
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
│   │   ├── __init__.py
│   │   ├── hardware_io.py       # 硬件资源 I/O（读取安装包文件）
│   │   └── analytics.py         # TalkingData 统计服务（架构桩）
│   ├── utils/                   # 工具模块
│   │   ├── __init__.py
│   │   ├── jwt_utils.py         # JWT 管理器（生成/验证/刷新/异常处理）
│   │   └── auth_required.py     # 认证装饰器（login_required / optional_login）
│   └── views/                   # 路由蓝图
│       ├── __init__.py          # 蓝图导出
│       ├── auth.py              # 认证蓝图（登录/注册/登出/Token刷新/用户信息）
│       └── package.py           # 安装包蓝图（版本检查/下载）
├── static/                      # 静态资源
│   ├── css/login.css            # 登录页样式
│   ├── js/login.js              # 登录页逻辑（Token 管理/自动刷新）
│   ├── fonts/                   # 自定义字体
│   └── photos/                  # 图片资源
├── templates/
│   └── login.html               # 登录页面模板
├── run.py                       # 启动入口
├── requirements.txt             # Python 依赖
└── README.md                    # 项目文档
```

## 快速开始

### 1. 环境准备

```powershell
# 创建虚拟环境
python -m venv .venv

# 激活
.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# 密钥（不设置则自动生成随机密钥）
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# MySQL 数据库
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=lorian

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 安装包存储路径
BINARY_FILES_PATH=/path/to/packages

# TalkingData（暂不启用）
TALKINGDATA_APP_ID=
TALKINGDATA_ENABLED=false
```

### 3. 数据库初始化

```sql
CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    permission VARCHAR(20) DEFAULT '访客',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. 启动服务

```bash
python run.py
```

访问 http://localhost:5000/api/auth/login 进入登录页。

## API 文档

### 认证模块 (`/api/auth`)

所有接口统一返回格式：

```json
// 成功
{"code": 0, "msg": "...", "...": "..."}

// 失败
{"code": <负数>, "msg": "错误提示", "ErrorDetails": "..."}
```

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/auth/login` | 无 | 登录页面 |
| POST | `/api/auth/login` | 无 | 登录 (FormData: username, password) |
| POST | `/api/auth/register` | 无 | 注册 (JSON: {username, password, permission?}) |
| POST | `/api/auth/logout` | 可选 | 登出（前端丢弃 token） |
| GET | `/api/auth/me` | Bearer Token | 获取当前用户信息 |
| POST | `/api/auth/refresh` | Refresh Token | 刷新 Access Token |

### 安装包模块 (`/api`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/getLatestPackage` | 获取最新安装包信息 |

---

## JWT 认证流程

```
  ┌─────────┐                            ┌──────────┐
  │ 前端     │                            │ 后端      │
  │ (JS)    │                            │ (Flask)  │
  └────┬────┘                            └────┬─────┘
       │  POST /api/auth/login                 │
       │  {username, password}                 │
       │─────────────────────────────────────▶ │
       │                                       │ 验证密码
       │                                       │ 生成 token pair
       │  {access_token, refresh_token, user}  │
       │◀───────────────────────────────────── │
       │                                       │
       │  存储到 localStorage                  │
       │                                       │
       │  后续请求                              │
       │  Authorization: Bearer <access_token> │
       │─────────────────────────────────────▶ │
       │                                       │ JWT 验证
       │  {code:0, data:...}                   │
       │◀───────────────────────────────────── │
       │                                       │
       │  401 时自动用 refresh_token 换新      │
       │  POST /api/auth/refresh               │
       │  Authorization: Bearer <refresh_token>│
       │─────────────────────────────────────▶ │
       │  {access_token}                       │
       │◀───────────────────────────────────── │
```

- **Access Token**: 30 分钟有效期，用于 API 鉴权
- **Refresh Token**: 7 天有效期，用于无感刷新 Access Token
- 前端在 401 响应时自动尝试刷新，失败则跳回登录页

### 保护 API 路由示例

```python
from app.utils import login_required

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_user_info():
    from flask import g
    return jsonify({"username": g.current_user})
```

---

## code 编码表

| code | 含义 |
|------|------|
| 0 | 成功 |
| -1 | 密码长度不合法 |
| -2 | 用户名过长 |
| -3 | 用户名含非法字符 |
| -4 | 密码格式不合法 |
| -5 | 用户名已存在 |
| -6 | 请求数据为空 |
| -7 | 用户名或密码为空 |
| -8 | 用户不存在 |
| -9 | 密码错误 |
| -10 | Token 过期 |
| -11 | Token 无效 |
| -12 | 缺少 Token |
| -13 | 无效的权限值 |

## TalkingData 统计架构

统计模块采用事件驱动 + 批量上报的设计，当前为**桩实现**（仅打日志），后续接入 SDK 时只需修改 `app/services/analytics.py` 中的 `_send()` 方法。

**事件类型**:

| 事件名 | 触发时机 |
|--------|---------|
| `auth_login` | 登录成功 |
| `auth_login_failed` | 登录失败 |
| `auth_register` | 注册成功 |
| `auth_logout` | 登出 |
| `package_download` | 安装包下载 |
| `package_check` | 版本检查 |

**启用方式**:

```env
TALKINGDATA_ENABLED=true
TALKINGDATA_APP_ID=your_td_app_id
```

**后续对接步骤**:

1. `pip install talkingdata-sdk` (或其他官方 SDK)
2. 修改 `AnalyticsService._send()` 批量上报逻辑
3. 前端集成 TalkingData JS SDK，采集页面浏览、点击流

## Todo List

- [x] Flask 应用工厂 + Blueprint 架构
- [x] Redis 连接池
- [x] MySQL 连接
- [x] JWT 认证（Access + Refresh Token）
- [x] 登录 / 注册 / 登出 / Token 刷新 / 用户信息 API
- [x] 前端 Token 管理 + 自动刷新 + 错误提示
- [x] 认证装饰器（@login_required / @optional_login）
- [x] TalkingData 统计架构（桩实现）
- [ ] TalkingData SDK 正式接入
- [ ] 速率限制（登录/注册接口）
- [ ] 验证码对接
- [ ] Gunicorn 生产部署配置
- [ ] 安装包下载 API
- [ ] 设备管理 API
- [ ] 用户权限管理后台
