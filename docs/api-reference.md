# API 接口文档

Base URL: `http://localhost:5000`

---

## 1. 认证模块 `/api/auth`

### 1.1 登录页面

```
GET /api/auth/login
```

返回登录 HTML 页面（`text/html`）。

---

### 1.2 登录

```
POST /api/auth/login
Content-Type: multipart/form-data
```

**请求体 (FormData)**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | 是 | 用户名 |
| `password` | string | 是 | 密码 |

**成功响应** (200):

```json
{
    "code": 0,
    "msg": "登录成功",
    "access_token": "eyJ0...",
    "refresh_token": "eyJ1...",
    "token_type": "bearer",
    "user": {
        "username": "test",
        "permission": "锁定"
    }
}
```

**失败响应** (400/401):

```json
{"code": -9, "msg": "密码错误", "ErrorDetails": ""}
```

---

### 1.3 注册

```
POST /api/auth/register
Content-Type: application/json
```

**请求体 (JSON)**:

```json
{
    "username": "newuser",
    "password": "password123",
    "permission": "访客"          // 可选，默认 "访客"
}
```

**permission 可选值**: `锁定` | `访客` | `管理员` | `最高管理员`

**成功响应** (200):

```json
{"code": 0, "msg": "注册成功"}
```

**失败响应**:

```json
{"code": -5, "msg": "此用户名已被使用", "ErrorDetails": "IntegrityError"}
```

---

### 1.4 登出

```
POST /api/auth/logout
Authorization: Bearer <access_token>   // 可选
```

**成功响应** (200):

```json
{"code": 0, "msg": "已登出"}
```

> 注意：登出不撤销 Token（无状态），前端 `clearToken()` 丢弃 token 即可。

---

### 1.5 获取当前用户信息

```
GET /api/auth/me
Authorization: Bearer <access_token>   // 必填
```

**成功响应** (200):

```json
{
    "code": 0,
    "msg": "",
    "data": {
        "username": "test",
        "permission": "访客",
        "user_id": 1
    }
}
```

**失败响应** (401):

```json
{"code": -12, "msg": "缺少认证 Token", "ErrorDetails": "..."}
```

---

### 1.6 刷新 Token

```
POST /api/auth/refresh
Authorization: Bearer <refresh_token>  // 必填
```

**成功响应** (200):

```json
{
    "code": 0,
    "msg": "Token 已刷新",
    "access_token": "eyJ2...",
    "token_type": "bearer"
}
```

**失败响应** (401):

```json
{"code": -11, "msg": "Token 无效", "ErrorDetails": "..."}
```

---

## 2. 安装包模块 `/api`

### 2.1 获取最新安装包

```
GET /api/getLatestPackage
```

**成功响应** (200):

```json
{
    "latest_package": "落雨1_1_0.apk",
    "latest_version": "1.1.0"
}
```

### 2.2 下载安装包

```
GET /api/download/<filename>
```

直接返回 APK 文件流（`application/vnd.android.package-archive`），浏览器触发下载。

示例: `GET /api/download/落雨1_0_0.apk`

---

## 3. 仪表盘模块 `/api/dashboard`

仪表盘包含 4 个子模块，通过顶部 Tab 切换。页面本身不强制鉴权（返回 HTML），但所有数据 API 均需 `Authorization` 头。

### 3.1 仪表盘页面

```
GET /api/dashboard
```

返回仪表盘 HTML 页面（前端 JS 检查 token）。

---

### 3.2 数据看板

```
GET /api/dashboard/stats
Authorization: Bearer <access_token>
```

**成功响应** (200):

```json
{
    "code": 0, "msg": "",
    "data": {
        "total_devices": 0,
        "today_active": 0,
        "total_downloads": 0,
        "online_devices": 0,
        "latest_version": "1.1.0"
    }
}
```

---

### 3.3 更新管理

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/dashboard/updates` | Bearer Token | 安装包列表 |
| POST | `/api/dashboard/updates/upload` | 管理员 | 上传新安装包（multipart: file + changelog） |
| POST | `/api/dashboard/updates/push` | 管理员 | 手动推送更新 (`{"version":"1.1.0","target":"all"}`) |

**上传校验规则**:
1. 仅 `.apk` 扩展名
2. 文件名格式: `落雨X_Y_Z.apk`
3. 单文件 ≤ 500MB
4. 版本必须高于当前最新版本

**上传成功响应**:
```json
{
    "code": 0,
    "msg": "落雨1_1_0.apk 上传成功",
    "data": {
        "filename": "落雨1_1_0.apk",
        "version": "1.1.0",
        "version_tuple": [1, 1, 0],
        "size_mb": 45.3,
        "uploaded_at": "2025-01-15 14:30:00",
        "uploader": "admin",
        "path": "./binaryFiles/落雨1_1_0.apk"
    }
}
```

---

### 3.4 公告管理

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/dashboard/announcements` | Bearer Token | 公告列表 |
| POST | `/api/dashboard/announcements` | 管理员 | 新建公告 (`{"title":"...","content":"..."}`) |
| PUT | `/api/dashboard/announcements/<id>` | 管理员 | 编辑公告 |
| DELETE | `/api/dashboard/announcements/<id>` | 管理员 | 删除公告 |
| POST | `/api/dashboard/announcements/push` | 管理员 | 推送公告 (`{"id":1}`) |

---

### 3.5 账号管理

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/dashboard/accounts` | 管理员 | 用户列表 |
| POST | `/api/dashboard/accounts` | 管理员 | 创建/修改账号 (传 `id` 则修改) |
| DELETE | `/api/dashboard/accounts/<id>` | 最高管理员 | 删除账号 |

---

## 4. 事件采集模块 `/api/events`（TalkingData 通道）

> 无需登录。设计理念与 TalkingData 一致：前端匿名推送用户行为事件，
> 后端异步入队批量上报。轻量、无状态、低延迟。

### 4.1 上报事件

```
POST /api/events/track
Content-Type: application/json
```

**请求体 — 单条模式**:

```json
{
    "event": "page_view",
    "data": {
        "page": "/dashboard",
        "duration_ms": 3200,
        "device": "android"
    },
    "user_id": "optional_device_or_user_id"
}
```

**请求体 — 批量模式**:

```json
{
    "events": [
        {"event": "page_view",  "data": {"page": "/login"}},
        {"event": "button_click","data": {"button": "login_btn"}},
        {"event": "app_launch",  "data": {"version": "1.1.0"}}
    ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | 是 | 事件名，仅允许 `[a-z0-9_:]` |
| `data` | object | 否 | 事件附加数据（任意 key-value） |
| `user_id` | string | 否 | 设备或用户标识（不传则记为 anonymous） |
| `events` | array | 否 | 批量事件列表（与单条二选一，最多 100 条） |

**成功响应** (200):

```json
{"code": 0, "msg": "ok", "accepted": 1}
```

**失败响应** (400):

```json
{"code": -15, "msg": "事件格式错误", "ErrorDetails": ""}
```

**前端调用示例**:

```js
// 单条 — 上报页面浏览
fetch("/api/events/track", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        event: "page_view",
        data: { page: "/dashboard", referrer: document.referrer }
    })
});

// 批量 — 一次性上报多个事件
fetch("/api/events/track", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        events: [
            {event: "page_view",  data: {page: "/login"}},
            {event: "button_click", data: {button: "login_btn"}}
        ]
    })
});
```

### 4.2 预定义事件名

| 事件名 | 含义 | 建议 data 字段 |
|--------|------|--------------|
| `page_view` | 页面浏览 | `{page, referrer, duration_ms}` |
| `button_click` | 按钮点击 | `{button, context}` |
| `app_launch` | 应用启动 | `{version, platform}` |
| `app_exit` | 应用退出 | `{session_duration_ms}` |
| `download_start` | 开始下载 | `{package_name, version}` |
| `download_complete` | 下载完成 | `{package_name, duration_ms}` |

前端团队可自由扩展事件名，只要符合 `[a-z0-9_:]` 正则即可。

---

## 通用约定

1. **请求头**: 受保护接口需携带 `Authorization: Bearer <access_token>`
2. **响应码**: HTTP 状态码 + `code` 字段双重判断
3. **幂等性**: 所有 GET 接口幂等；POST 登录/注册非幂等
4. **编码**: 所有请求/响应均为 UTF-8
