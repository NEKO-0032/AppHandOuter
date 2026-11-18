"""
仪表盘蓝图 — 4 大模块:
  1. 数据看板:   /stats          GET   设备数/活跃/下载
  2. 更新管理:   /updates        GET   安装包列表
                /updates/upload POST  上传新安装包
                /updates/push   POST  手动推送更新
  3. 公告管理:   /announcements       GET    公告列表
                /announcements       POST   新建/编辑公告
                /announcements/<id>  PUT    编辑指定公告
                /announcements/<id>  DELETE 删除公告
                /announcements/push  POST   推送公告到客户端
  4. 账号管理:   /accounts        GET    用户列表（管理员+）
                /accounts        POST   创建/修改账号（管理员+）
                /accounts/<id>   DELETE 删除账号（最高管理员）

  主页面:       /               GET    Dashboard 页面（带 4 个标签页）
"""

from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash
from app.utils import login_required, permission_required
from app.utils.security import ip_whitelist
from app.extentions_reali import mysqlConnector, redisClient
from app.services.analytics import analytics
from app.services.package_service import PackageService
import mysql.connector.errors as mysql_errors
import time

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


# ============================================================
#  主页面
# ============================================================
class PageController:
    def index(self):
        return render_template("dashboard.html")


# ============================================================
#  1. 数据看板
# ============================================================
class StatsController:

    @login_required
    def get(self):
        """
        GET /api/dashboard/stats

        返回仪表盘顶部卡片数据。
        TODO: 对接真实数据源
          - total_devices  → SELECT COUNT(*) FROM devices
          - today_active   → Redis / events 今日活跃
          - total_downloads → download_logs 表
          - online_devices → Redis 在线设备心跳
        """
        stats = {
            "total_devices": 0,
            "today_active": 0,
            "total_downloads": 0,
            "online_devices": 0,
            "latest_version": "1.1.0"
        }
        return jsonify({"code": 0, "msg": "", "data": stats})


# ============================================================
#  2. 更新管理
# ============================================================
class UpdatesController:

    @login_required
    def list_updates(self):
        """
        GET /api/dashboard/updates
        从 Redis 读取所有安装包元数据（最新在前）
        """
        packages = PackageService.get_all_packages()

        # 标记最新版本
        latest = PackageService.get_latest()
        latest_filename = latest["filename"] if latest else None

        for pkg in packages:
            pkg["is_latest"] = (pkg["filename"] == latest_filename)
            # status 由 Redis 决定：在列表中 = active
            pkg["status"] = "active"

        return jsonify({"code": 0, "msg": "", "data": {"packages": packages}})

    @permission_required("管理员")
    def upload(self):
        """
        POST /api/dashboard/updates/upload
        Content-Type: multipart/form-data

        上传新安装包。
        字段: file (APK 文件，必填), changelog (可选)

        校验规则:
          1. 仅允许 .apk 扩展名
          2. 文件名必须符合 落雨X_Y_Z.apk 格式
          3. 文件大小 ≤ 500MB
          4. 版本必须高于当前最新版本
        """
        file = request.files.get('file')
        if not file:
            return jsonify({"code": -16, "msg": "未提供文件", "ErrorDetails": ""}), 400

        uploader = get_jwt_identity()
        changelog = request.form.get('changelog', '')

        success, message, meta = PackageService.upload(file, uploader=uploader, changelog=changelog)

        if not success:
            return jsonify({"code": -17, "msg": message, "ErrorDetails": ""}), 400

        # 上报统计
        analytics.track("package_upload", user=uploader, data={
            "filename": meta["filename"], "version": meta["version"], "size_mb": meta["size_mb"]
        })

        return jsonify({
            "code": 0,
            "msg": f"{meta['filename']} 上传成功",
            "data": meta
        })

    @permission_required("管理员")
    def push_update(self):
        """
        POST /api/dashboard/updates/push
        Content-Type: application/json

        手动推送更新通知到客户端。
        body: {"version": "1.1.0", "target": "all" | ["device_id1", ...]}

        TODO: 通过 WebSocket / 推送服务通知客户端
        """
        data = request.get_json(silent=True) or {}
        version = data.get('version', '')
        target = data.get('target', 'all')

        # 校验版本是否存在
        all_pkgs = PackageService.get_all_packages()
        exists = any(p["version"] == version for p in all_pkgs)
        if not exists:
            return jsonify({"code": -8, "msg": f"版本 {version} 不存在", "ErrorDetails": ""}), 404

        analytics.track("update_push", user=get_jwt_identity(), data={"version": version, "target": str(target)})

        return jsonify({
            "code": 0,
            "msg": f"已发送更新推送 (版本 {version}, 目标 {target})",
            "data": {"version": version, "target": target}
        })


# ============================================================
#  3. 公告管理
# ============================================================
class AnnouncementsController:

    @login_required
    def list_announcements(self):
        """
        GET /api/dashboard/announcements
        返回公告列表
        TODO: 从 MySQL 查询 announcements 表
        """
        try:
            with mysqlConnector.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, title, content, created_at, is_active "
                    "FROM announcements ORDER BY created_at DESC LIMIT 50"
                )
                rows = cursor.fetchall()
        except Exception:
            rows = []

        items = [
            {
                "id": r[0], "title": r[1], "content": r[2],
                "created_at": str(r[3]) if r[3] else None,
                "is_active": bool(r[4]) if len(r) > 4 else True
            }
            for r in rows
        ]
        return jsonify({"code": 0, "msg": "", "data": {"announcements": items}})

    @permission_required("管理员")
    def create_announcement(self):
        """
        POST /api/dashboard/announcements
        Content-Type: application/json

        新建公告.
        body: {"title": "...", "content": "..."}
        """
        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title or not content:
            return jsonify({"code": -7, "msg": "标题和内容不能为空", "ErrorDetails": ""}), 400

        try:
            with mysqlConnector.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO announcements (title, content, is_active) VALUES (%s, %s, 1)",
                    (title, content)
                )
                mysqlConnector.db.commit()
                ann_id = cursor.lastrowid
        except Exception as e:
            return jsonify({"code": 1, "msg": f"数据库错误: {e}", "ErrorDetails": str(e)}), 500

        return jsonify({
            "code": 0, "msg": "公告已创建",
            "data": {"id": ann_id, "title": title}
        })

    @permission_required("管理员")
    def update_announcement(self, ann_id):
        """
        PUT /api/dashboard/announcements/<id>
        body: {"title": "...", "content": "...", "is_active": true/false}
        """
        data = request.get_json(silent=True) or {}
        title = data.get('title')
        content = data.get('content')
        is_active = data.get('is_active')

        sets = []
        values = []
        if title is not None:
            sets.append("title = %s")
            values.append(title)
        if content is not None:
            sets.append("content = %s")
            values.append(content)
        if is_active is not None:
            sets.append("is_active = %s")
            values.append(1 if is_active else 0)

        if not sets:
            return jsonify({"code": -7, "msg": "无更新内容", "ErrorDetails": ""}), 400

        values.append(ann_id)
        try:
            with mysqlConnector.get_cursor() as cursor:
                cursor.execute(
                    f"UPDATE announcements SET {', '.join(sets)} WHERE id = %s",
                    values
                )
                mysqlConnector.db.commit()
        except Exception as e:
            return jsonify({"code": 1, "msg": f"更新失败: {e}", "ErrorDetails": str(e)}), 500

        return jsonify({"code": 0, "msg": "公告已更新"})

    @permission_required("管理员")
    def delete_announcement(self, ann_id):
        """DELETE /api/dashboard/announcements/<id>"""
        try:
            with mysqlConnector.get_cursor() as cursor:
                cursor.execute("DELETE FROM announcements WHERE id = %s", (ann_id,))
                mysqlConnector.db.commit()
        except Exception as e:
            return jsonify({"code": 1, "msg": f"删除失败: {e}", "ErrorDetails": str(e)}), 500

        return jsonify({"code": 0, "msg": "公告已删除"})

    @permission_required("管理员")
    def push_announcement(self):
        """
        POST /api/dashboard/announcements/push
        推送公告到客户端
        body: {"id": 1} 或 {"ids": [1,2,3]}

        TODO: 通过推送服务发送给客户端
        """
        data = request.get_json(silent=True) or {}
        ann_id = data.get('id') or (data.get('ids', [None])[0] if data.get('ids') else None)

        if not ann_id:
            return jsonify({"code": -7, "msg": "请指定公告 ID", "ErrorDetails": ""}), 400

        # TODO: 实际推送
        return jsonify({"code": 0, "msg": f"公告 #{ann_id} 已推送到客户端"})


# ============================================================
#  4. 账号管理
# ============================================================
class AccountsController:

    @permission_required("管理员")
    def list_accounts(self):
        """
        GET /api/dashboard/accounts
        返回后台用户列表（管理员及以上可访问）
        """
        with mysqlConnector.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, username, permission FROM accounts ORDER BY id"
            )
            rows = cursor.fetchall()

        users = [
            {"id": r[0], "username": r[1], "permission": r[2]}
            for r in rows
        ]
        return jsonify({"code": 0, "msg": "", "data": {"users": users, "total": len(users)}})

    @ip_whitelist
    @permission_required("管理员")
    def create_or_update(self):
        """
        POST /api/dashboard/accounts
        Content-Type: application/json

        创建或修改账号.
        - 传 id → 修改指定账号
        - 不传 id → 新建账号

        body: {"id": 1, "username": "...", "password": "...", "permission": "访客"}
        修改时 password 可选（不传则不改密码）
        """
        data = request.get_json(silent=True) or {}
        user_id = data.get('id')
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        permission = data.get('permission', '访客')

        valid_perms = {'锁定', '访客', '管理员', '最高管理员'}
        if permission not in valid_perms:
            return jsonify({
                "code": -13, "msg": f"无效的权限值，应为: {', '.join(valid_perms)}",
                "ErrorDetails": ""
            }), 400

        try:
            with mysqlConnector.get_cursor() as cursor:
                if user_id:
                    # 修改
                    if password:
                        cursor.execute(
                            "UPDATE accounts SET username=%s, password_hash=%s, permission=%s WHERE id=%s",
                            (username, generate_password_hash(password), permission, user_id)
                        )
                    else:
                        cursor.execute(
                            "UPDATE accounts SET username=%s, permission=%s WHERE id=%s",
                            (username, permission, user_id)
                        )
                    mysqlConnector.db.commit()
                    return jsonify({"code": 0, "msg": "账号已更新"})
                else:
                    # 新建
                    if not username or not password:
                        return jsonify({
                            "code": -7, "msg": "用户名和密码不能为空", "ErrorDetails": ""
                        }), 400
                    cursor.execute(
                        "INSERT INTO accounts (username, password_hash, permission) VALUES (%s, %s, %s)",
                        (username, generate_password_hash(password), permission)
                    )
                    mysqlConnector.db.commit()
                    return jsonify({
                        "code": 0, "msg": "账号已创建",
                        "data": {"id": cursor.lastrowid, "username": username}
                    })
        except mysql_errors.IntegrityError:
            return jsonify({"code": -5, "msg": "用户名已存在", "ErrorDetails": ""}), 409
        except Exception as e:
            return jsonify({"code": 1, "msg": f"操作失败: {e}", "ErrorDetails": str(e)}), 500

    @ip_whitelist
    @permission_required("最高管理员")
    def delete_account(self, user_id):
        """
        DELETE /api/dashboard/accounts/<id>
        仅最高管理员可删除账号
        """
        try:
            with mysqlConnector.get_cursor() as cursor:
                cursor.execute("DELETE FROM accounts WHERE id = %s", (user_id,))
                mysqlConnector.db.commit()
        except Exception as e:
            return jsonify({"code": 1, "msg": f"删除失败: {e}", "ErrorDetails": str(e)}), 500

        return jsonify({"code": 0, "msg": "账号已删除"})


# ============================================================
#  路由注册
# ============================================================
page  = PageController()
stat  = StatsController()
upd   = UpdatesController()
ann   = AnnouncementsController()
acct  = AccountsController()

# 主页面
dashboard_bp.route('/',                          methods=['GET'])(page.index)
# 数据看板
dashboard_bp.route('/stats',                     methods=['GET'])(stat.get)
# 更新管理
dashboard_bp.route('/updates',                   methods=['GET'])(upd.list_updates)
dashboard_bp.route('/updates/upload',            methods=['POST'])(upd.upload)
dashboard_bp.route('/updates/push',              methods=['POST'])(upd.push_update)
# 公告管理
dashboard_bp.route('/announcements',             methods=['GET'])(ann.list_announcements)
dashboard_bp.route('/announcements',             methods=['POST'])(ann.create_announcement)
dashboard_bp.route('/announcements/<int:ann_id>', methods=['PUT'])(ann.update_announcement)
dashboard_bp.route('/announcements/<int:ann_id>', methods=['DELETE'])(ann.delete_announcement)
dashboard_bp.route('/announcements/push',        methods=['POST'])(ann.push_announcement)
# 账号管理
dashboard_bp.route('/accounts',                  methods=['GET'])(acct.list_accounts)
dashboard_bp.route('/accounts',                  methods=['POST'])(acct.create_or_update)
dashboard_bp.route('/accounts/<int:user_id>',     methods=['DELETE'])(acct.delete_account)
