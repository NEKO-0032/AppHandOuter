"""
认证蓝图 - 登录 / 注册 / 登出 / Token 刷新 / 用户信息

JSON 响应规范（统一）：
    成功: {"code": 0,   "msg": "...", "token": "...", "data": {...}}
    失败: {"code": <0,  "msg": "错误提示", "ErrorDetails": "..."}

code 编码表:
    0    成功
    ...
    -403  IP 不在白名单 / 公开注册已关闭
"""

from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
import re
import time

from app.extentions_reali import mysqlConnector
from app.utils import JWTManager, login_required
from app.utils.security import disable_public_register, ip_whitelist
from app.services.analytics import analytics
import mysql.connector.errors as mysql_errors

# ---- 蓝图 ----
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ---- 预编译正则 ----
PATTERN_USERNAME = re.compile(r"^\w{1,50}$")
PATTERN_PASSWORD = re.compile(r"^[a-zA-Z0-9!@#$%&_-]{8,70}$")


# ============================================================
#  认证控制器
# ============================================================
class AuthController:

    # ========================
    #  公开路由
    # ========================

    def login(self):
        """
        POST /api/auth/login
        请求体 (FormData): username, password
        响应:
          成功 → {"code":0, "msg":"登录成功", "access_token":"...", "refresh_token":"...", "token_type":"bearer", "user":{...}}
          失败 → {"code":-8/-9/..., "msg":"..."}
        """
        form = request.form

        if not form:
            return jsonify({"code": -6, "msg": "请求数据不能为空", "ErrorDetails": ""}), 400

        username = form.get('username', '').strip()
        password = form.get('password', '')

        if not username or not password:
            return jsonify({"code": -7, "msg": "用户名和密码不能为空", "ErrorDetails": ""}), 400

        # 格式校验
        check = _check_credentials(username, password)
        if check["code"] != 0:
            analytics.track_auth_login(username, success=False, reason=check["msg"])
            return jsonify(check), 400

        # 数据库验证
        with mysqlConnector.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, password_hash, permission FROM accounts WHERE username = %s",
                (username,)
            )
            row = cursor.fetchone()

        if row is None:
            analytics.track_auth_login(username, success=False, reason="用户不存在")
            return jsonify({"code": -8, "msg": "用户不存在", "ErrorDetails": ""}), 400

        user_id, pwd_hash, permission = row

        if not check_password_hash(pwd_hash, password):
            analytics.track_auth_login(username, success=False, reason="密码错误")
            return jsonify({"code": -9, "msg": "密码错误", "ErrorDetails": ""}), 400

        # 生成 JWT token pair
        tokens = JWTManager.create_token_pair(
            identity=username,
            additional_claims={"user_id": user_id, "permission": permission}
        )

        analytics.track_auth_login(username, success=True)

        return jsonify({
            "code": 0,
            "msg": "登录成功",
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "user": {
                "username": username,
                "permission": permission
            }
        })

    def login_page(self):
        """GET /api/auth/login - 登录页面"""
        from flask import render_template
        return render_template("login.html")

    def register(self):
        """
        POST /api/auth/register
        Content-Type: application/json

        = 安全策略 =
        1. 生产环境通过 ALLOW_PUBLIC_REGISTER=false 关闭公开注册
        2. 关闭后账号只能由管理员通过 Dashboard 创建
        3. 开发环境默认开放

        请求体: {"username":"...", "password":"...", "permission":"访客"}
        """
        # 检查公开注册是否开启
        blocked = disable_public_register()
        if blocked:
            return blocked

        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        permission = data.get('permission', '访客')

        if not username or not password:
            return jsonify({"code": -7, "msg": "用户名和密码不能为空", "ErrorDetails": ""}), 400

        # 权限值校验
        valid_perms = {'锁定', '访客', '管理员', '最高管理员'}
        if permission not in valid_perms:
            return jsonify({"code": -13, "msg": f"无效的权限值，应为: {', '.join(valid_perms)}", "ErrorDetails": ""}), 400

        # 格式校验
        check = _check_credentials(username, password)
        if check["code"] != 0:
            return jsonify(check), 400

        with mysqlConnector.get_cursor() as cursor:
            sql = "INSERT INTO accounts (username, password_hash, permission) VALUES (%s, %s, %s)"
            try:
                cursor.execute(sql, (username, generate_password_hash(password), permission))
                mysqlConnector.db.commit()
            except mysql_errors.IntegrityError:
                analytics.track_auth_register(username, success=False, reason="用户名已存在")
                return jsonify({"code": -5, "msg": "此用户名已被使用", "ErrorDetails": "IntegrityError"}), 409
            except mysql_errors.Error as e:
                analytics.track_auth_register(username, success=False, reason=str(e))
                return jsonify({"code": 1, "msg": f"数据库错误: {e}", "ErrorDetails": str(e)}), 500

        analytics.track_auth_register(username, success=True)
        return jsonify({"code": 0, "msg": "注册成功"})

    def logout(self):
        """
        POST /api/auth/logout
        无需请求体，只需携带有效 access_token（后端不维护 token 黑名单，登出由前端丢弃 token 实现）
        """
        @jwt_required(optional=True)
        def _do_logout():
            identity = get_jwt_identity()
            if identity:
                analytics.track_auth_logout(identity)
            return jsonify({"code": 0, "msg": "已登出"})
        return _do_logout()

    # ========================
    #  需认证路由
    # ========================

    @login_required
    def me(self):
        """
        GET /api/auth/me
        获取当前登录用户信息
        Header: Authorization: Bearer <access_token>
        响应: {"code":0, "msg":"...", "data":{"username":"...", "permission":"...", "user_id":...}}
        """
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        return jsonify({
            "code": 0,
            "msg": "",
            "data": {
                "username": get_jwt_identity(),
                "permission": claims.get("permission", "访客"),
                "user_id": claims.get("user_id")
            }
        })

    def refresh(self):
        """
        POST /api/auth/refresh
        Header: Authorization: Bearer <refresh_token>
        用 refresh_token 换取新的 access_token
        响应: {"code":0, "msg":"...", "access_token":"..."}
        """
        @jwt_required(refresh=True)
        def _do_refresh():
            tokens = JWTManager.refresh_access_token()
            return jsonify({
                "code": 0,
                "msg": "Token 已刷新",
                "access_token": tokens["access_token"],
                "token_type": tokens["token_type"]
            })
        return _do_refresh()


# ============================================================
#  工具函数
# ============================================================

def _check_credentials(username: str, password: str) -> dict:
    """
    用户名 / 密码格式校验
    返回 {"code": 0} 表示通过，否则包含错误码和提示
    """
    if len(password) > 70:
        return {"code": -1, "msg": "密码长度不合法（应 ≤ 70）", "ErrorDetails": ""}
    if len(username) > 50:
        return {"code": -2, "msg": "用户名过长（应 ≤ 50）", "ErrorDetails": ""}
    if PATTERN_USERNAME.fullmatch(username) is None:
        return {"code": -3, "msg": "用户名包含非法字符", "ErrorDetails": ""}
    if PATTERN_PASSWORD.fullmatch(password) is None:
        return {"code": -4, "msg": "密码不合法（8-70位，字母/数字/!@#$%&_-）", "ErrorDetails": ""}
    return {"code": 0}


# ============================================================
#  路由注册
# ============================================================
auth = AuthController()

auth_bp.route('/login',    methods=['POST'])(auth.login)
auth_bp.route('/login',    methods=['GET'])(auth.login_page)
auth_bp.route('/register', methods=['POST'])(auth.register)
auth_bp.route('/logout',   methods=['POST'])(auth.logout)
auth_bp.route('/me',       methods=['GET'])(auth.me)
auth_bp.route('/refresh',  methods=['POST'])(auth.refresh)