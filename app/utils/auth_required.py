"""
认证装饰器模块
提供认证 + 权限分级两个维度的装饰器：

  login_required:     必须登录才能访问，未登录返回 401
  optional_login:     可选登录（已登录则注入 g.current_user，未登录也放行）
  permission_required: 必须登录且达到指定权限等级

权限等级（由低到高）：
  锁定 < 访客 < 管理员 < 最高管理员
"""

from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from flask import request, g, jsonify

# 权限等级映射（数字越大权限越高）
_PERMISSION_LEVEL = {
    "锁定": 0,
    "访客": 1,
    "管理员": 2,
    "最高管理员": 3,
}


def login_required(fn=None, *, optional=False, fresh=False, refresh=False):
    """
    强制登录装饰器。支持两种用法:

        @login_required                          # 裸装饰
        @login_required(optional=True)           # 带参数

    Args:
        optional: 是否可选登录
        fresh: 是否要求 fresh token
        refresh: 是否接受 refresh token
    """
    def _wrap(f):
        @wraps(f)
        def _wrapper(*args, **kwargs):
            verify_jwt_in_request(
                optional=optional,
                fresh=fresh,
                refresh=refresh,
                locations=["headers", "cookies"]
            )
            current_identity = get_jwt_identity()
            if current_identity:
                g.current_user = current_identity
            return f(*args, **kwargs)
        return _wrapper

    if fn is None:
        return _wrap
    return _wrap(fn)


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


def permission_required(min_permission: str):
    """
    权限分级装饰器：要求用户至少达到 min_permission 等级
    必须作为 @permission_required("管理员") 调用，不支持裸装饰

    权限层级: 锁定 < 访客 < 管理员 < 最高管理员
    min_permission 为 "锁定" 时等同于 @login_required
    """
    valid_perms = set(_PERMISSION_LEVEL.keys())
    if min_permission not in valid_perms:
        raise ValueError(f"无效的权限值: {min_permission}，可选: {valid_perms}")

    min_level = _PERMISSION_LEVEL[min_permission]

    def _wrap(f):
        @wraps(f)
        def _wrapper(*args, **kwargs):
            verify_jwt_in_request(optional=False, locations=["headers", "cookies"])
            identity = get_jwt_identity()
            claims = get_jwt()
            user_permission = claims.get("permission", "锁定")
            user_level = _PERMISSION_LEVEL.get(user_permission, 0)

            if user_level < min_level:
                return jsonify({
                    "code": -14,
                    "msg": f"权限不足，需要: {min_permission}，当前: {user_permission}",
                    "ErrorDetails": "forbidden"
                }), 403

            g.current_user = identity
            return f(*args, **kwargs)
        return _wrapper
    return _wrap
