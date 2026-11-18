# 数据库文档

## 数据库信息

| 项目 | 值 |
|------|---|
| 数据库名 | `lorian_backend` |
| 引擎 | MySQL |
| 驱动 | mysql-connector-python |
| 字符集 | UTF-8（默认） |

---

## 表结构

### accounts — 用户账号表

```sql
CREATE TABLE accounts (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)                              NOT NULL UNIQUE,
    password_hash VARCHAR(256)                             NOT NULL,
    permission    ENUM('最高管理员','管理员','访客','锁定')  DEFAULT NULL
);
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 自增主键 |
| `username` | VARCHAR(50) | NOT NULL, UNIQUE | 用户名，正则 `^\w{1,50}$` |
| `password_hash` | VARCHAR(256) | NOT NULL | Werkzeug `generate_password_hash` 哈希 |
| `permission` | ENUM | DEFAULT NULL | 权限等级 |

---

### announcements — 公告表

```sql
CREATE TABLE announcements (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    title      VARCHAR(200)  NOT NULL,
    content    TEXT          NOT NULL,
    is_active  TINYINT(1)    DEFAULT 1,
    created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK, AUTO_INCREMENT | 公告 ID |
| `title` | VARCHAR(200) | NOT NULL | 公告标题 |
| `content` | TEXT | NOT NULL | 公告正文 |
| `is_active` | TINYINT(1) | DEFAULT 1 | 是否生效（1=生效中，0=已停用） |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 创建时间 |

### devices — 设备表（待创建）

```sql
CREATE TABLE devices (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    device_id    VARCHAR(100) NOT NULL UNIQUE,
    platform     VARCHAR(20)  DEFAULT 'android',
    app_version  VARCHAR(20),
    last_seen    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    first_seen   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INT | PK | 自增主键 |
| `device_id` | VARCHAR(100) | UNIQUE, NOT NULL | 设备唯一标识 |
| `platform` | VARCHAR(20) | DEFAULT 'android' | 平台 |
| `app_version` | VARCHAR(20) | NULL | 当前 App 版本 |
| `last_seen` | TIMESTAMP | 自动更新 | 最近活跃时间 |
| `first_seen` | TIMESTAMP | DEFAULT NOW() | 首次注册时间 |

### download_logs — 下载日志表（待创建）

```sql
CREATE TABLE download_logs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    device_id     VARCHAR(100),
    package_name  VARCHAR(200),
    version       VARCHAR(20),
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 连接配置

在 `.env` 中配置：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=lorian_backend
```

### 连接池行为

- 每次 `mysqlConnector.get_cursor()` 返回原始连接 cursor
- **不自动 commit**，需手动 `mysqlConnector.db.commit()`
- 事务由 `with` 上下文管理自动 close cursor

---

## 常用操作

### 插入用户

```python
with mysqlConnector.get_cursor() as cursor:
    cursor.execute(
        "INSERT INTO accounts (username, password_hash, permission) VALUES (%s, %s, %s)",
        (username, generate_password_hash(password), permission)
    )
    mysqlConnector.db.commit()
```

### 查询用户

```python
with mysqlConnector.get_cursor() as cursor:
    cursor.execute(
        "SELECT id, password_hash, permission FROM accounts WHERE username = %s",
        (username,)
    )
    row = cursor.fetchone()  # None 或 (id, hash, permission)
```

### 预置测试账号

> ⚠️ **仅限测试环境！**

```python
# test 账号
cursor.execute(
    "INSERT IGNORE INTO accounts (username, password_hash, permission) VALUES (%s, %s, %s)",
    ("test", generate_password_hash("wsfdexgfcdhrtjy"), "锁定")
)
# local_admin 账号
cursor.execute(
    "INSERT IGNORE INTO accounts (username, password_hash, permission) VALUES (%s, %s, %s)",
    ("local_admin", generate_password_hash("114514AAA"), "最高管理员")
)
```

| 用户名 | 密码 | 权限 |
|--------|------|------|
| `test` | `wsfdexgfcdhrtjy` | 锁定 |
| `local_admin` | `114514AAA` | 最高管理员 |

---

## 后续扩展

- [ ] 设备管理表 `devices`
- [ ] 下载日志表 `download_logs`
- [ ] 操作日志表 `audit_logs`
- [ ] 连接池改为 `mysql-connector-python` 内置 pool
