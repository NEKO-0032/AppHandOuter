"""
认证装饰器模块
提供两个认证级别的装饰器：

  login_required: 必须登录才能访问，未登录返回 401
  optional_login: 可以登录也可以不登录，用于同时支持游客和登录用户的接口
"""

from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import request, g


def login_required(fn=None, *, optional=False, fresh=False, refresh=False):
    """
    强制登录装饰器

    Usage:
        @login_required
        def protected_route():
            username = g.current_user  # 从 g 对象中获取当前用户名
            ...

    Args:
        optional: 是否可选登录
        fresh: 是否要求 fresh token
        refresh: 是否接受 refresh token
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request(
                optional=optional,
                fresh=fresh,
                refresh=refresh,
                locations=["headers", "cookies"]
            )
            # 将当前用户注入 flask.g，方便视图函数使用
            current_identity = get_jwt_identity()
            if current_identity:
                g.current_user = current_identity
            return f(*args, **kwargs)
        return wrapper
    return decorator


def optional_login(fn):
    """可选登录装饰器：已登录则注入用户，未登录也放行"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True, locations=["headers", "cookies"])
            current_identity = get_jwt_identity()
            if current_identity:
                g.current_user = current_identity
        except Exception:
            pass
        return fn(*args, **kwargs)
    return wrapper
