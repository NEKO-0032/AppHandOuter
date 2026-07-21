"""
JWT 工具模块
负责 token 的生成、验证、刷新，基于 flask-jwt-extended

设计思路：
  - Access Token: 短期（默认 30 分钟），用于 API 鉴权
  - Refresh Token: 长期（默认 7 天），用于无感刷新 Access Token
  - Token 存储在 localStorage（由前端管理），每次请求通过 Authorization 头携带
"""

from flask_jwt_extended import (
    JWTManager as _FlaskJWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
    jwt_required,
)
from datetime import timedelta
from flask import jsonify


class JWTManager:
    """JWT 管理器，封装 flask-jwt-extended 的常用操作"""

    def __init__(self, app=None):
        self._jwt = _FlaskJWTManager()
        if app:
            self.init_app(app)

    def init_app(self, app):
        """初始化 JWT 到 Flask 应用"""
        self._jwt.init_app(app)
        self._register_handlers()

    def _register_handlers(self):
        """注册 JWT 异常处理器：token 过期、无效、缺失"""

        @self._jwt.expired_token_loader
        def expired_token_callback(_jwt_header, _jwt_payload):
            return jsonify({
                "code": -10,
                "msg": "Token 已过期，请刷新",
                "ErrorDetails": "expired"
            }), 401

        @self._jwt.invalid_token_loader
        def invalid_token_callback(error_str):
            return jsonify({
                "code": -11,
                "msg": "Token 无效",
                "ErrorDetails": str(error_str)
            }), 401

        @self._jwt.unauthorized_loader
        def missing_token_callback(error_str):
            return jsonify({
                "code": -12,
                "msg": "缺少认证 Token",
                "ErrorDetails": str(error_str)
            }), 401

    # ---- Token 生成 ----

    @staticmethod
    def create_token_pair(identity: str, additional_claims: dict = None):
        """
        生成 access_token + refresh_token 对

        Args:
            identity: 用户标识（通常是 username）
            additional_claims: 附加声明（如权限等级），会编入 token payload

        Returns:
            dict: {"access_token": "...", "refresh_token": "..."}
        """
        access_token = create_access_token(
            identity=identity,
            additional_claims=additional_claims or {},
            expires_delta=timedelta(minutes=30)
        )
        refresh_token = create_refresh_token(
            identity=identity,
            additional_claims=additional_claims or {},
            expires_delta=timedelta(days=7)
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    def refresh_access_token():
        """
        用当前有效的 refresh_token 换取新的 access_token
        需在 @jwt_required(refresh=True) 保护的路由内调用
        """
        identity = get_jwt_identity()
        claims = get_jwt()
        additional_claims = {k: v for k, v in claims.items() if k not in ("sub", "iat", "nbf", "exp", "type", "jti", "fresh", "csrf")}
        new_access = create_access_token(
            identity=identity,
            additional_claims=additional_claims,
            expires_delta=timedelta(minutes=30)
        )
        return {
            "access_token": new_access,
            "token_type": "bearer"
        }
