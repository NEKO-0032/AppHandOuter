# 数据规范

## 一、JSON 响应规范（全项目统一）

所有 API 接口统一使用以下 JSON 格式：

```json
// 成功
{
    "code": 0,
    "msg": "操作成功",
    "data": { ... },        // 业务数据（可选）
    "access_token": "...",  // JWT 令牌（仅登录/刷新接口）
    "refresh_token": "..."  // JWT 刷新令牌（仅登录接口）
}

// 业务失败
{
    "code": <负数>,
    "msg": "人类可读的错误提示",
    "ErrorDetails": "调试用详细信息（可选）"
}
```

### code 编码表

| code | 含义 | 触发场景 |
|------|------|---------|
| 0 | 成功 | 一切正常 |
| -1 | 密码长度不合法 | > 70 字符 |
| -2 | 用户名过长 | > 50 字符 |
| -3 | 用户名含非法字符 | 非 `\w` 字符 |
| -4 | 密码格式不合法 | 非 `[a-zA-Z0-9!@#$%&_-]` |
| -5 | 用户名已存在 | 注册时数据库 UNIQUE 冲突 |
| -6 | 请求数据为空 | form 或 JSON body 为空 |
| -7 | 用户名或密码为空 | 必填项缺失 |
| -8 | 用户不存在 | 数据库查无此人 |
| -9 | 密码错误 | 密码哈希不匹配 |
| -10 | Token 过期 | JWT 过期（access 30min / refresh 7day） |
| -11 | Token 无效 | 格式错误或签名不匹配 |
| -12 | 缺少 Token | 请求头无 Authorization |
| -13 | 无效的权限值 | 注册时传入不存在的 permission |
| -14 | 权限不足 | `@permission_required` 拦截 |
| -15 | 事件格式错误 | `/api/events/track` 校验失败 |
| -16 | 未提供文件 | 上传接口缺少 file |
| -17 | 上传校验失败 | 命名/版本/大小不符合规范 |
| -403 | IP 白名单拒绝 / 注册已关闭 | 安全模块拦截 |

---

## 二、数据实体定义

### 用户 (User)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 用户唯一 ID |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | 用户名，仅允许 `\w` |
| `password_hash` | VARCHAR(256) | NOT NULL | Werkzeug 哈希 |
| `permission` | ENUM | 默认 NULL | 权限等级 |

### 权限等级（由低到高）

| 等级 | 值 | 说明 |
|------|---|------|
| 0 | `锁定` | 被封禁用户，不可登录 |
| 1 | `访客` | 默认角色 |
| 2 | `管理员` | 管理权限 |
| 3 | `最高管理员` | 超级管理员 |

---

## 三、JWT Token 数据格式

### Access Token Payload

```json
{
    "sub": "test",           // 用户名（identity）
    "user_id": 1,            // 数据库 ID
    "permission": "访客",     // 权限等级
    "iat": 1700000000,       // 签发时间
    "exp": 1700001800,       // 过期时间（+30min）
    "type": "access"
}
```

### Refresh Token Payload

```json
{
    "sub": "test",
    "user_id": 1,
    "permission": "访客",
    "iat": 1700000000,
    "exp": 1700604800,       // +7 天
    "type": "refresh"
}
```

---

## 四、前端 Token 存储规范

| Key | 值 | 用途 |
|-----|---|------|
| `lorian_access_token` | JWT Access Token | API 鉴权 |
| `lorian_refresh_token` | JWT Refresh Token | 无感刷新 |
| `lorian_user` | `{"username":"...","permission":"..."}` | 用户信息展示 |

全部存储在 `localStorage`，登出时清除。
