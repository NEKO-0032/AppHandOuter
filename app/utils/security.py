"""
安全模块 — 多层防线防止未授权操作

设计思路（由外到内）：

  Layer 1  IP 白名单:     只允许特定 IP 访问敏感路由（防公网扫描）
  Layer 2  注册开关:      生产环境禁止公开注册（ALLOW_PUBLIC_REGISTER=false）
  Layer 3  令牌认证:      已有 JWT / permission_required 保护
  Layer 4  Admin Secret:  可选的后门密钥，用于脚本/CI 绕过 JWT

关于 IP 伪造：
  - request.remote_addr 取的是 TCP 层真实 IP，不受 X-Forwarded-For 头影响
  - 如果部署在反向代理后面，需额外配置 trusted_proxies
  - 本模块默认信任 request.remote_addr（适合直连部署）

Usage:
    from app.utils.security import ip_whitelist, disable_public_register

    @ip_whitelist                              # 仅白名单 IP 可访问
    @permission_required("管理员")
    def admin_only():
        ...
"""

from functools import wraps
from flask import request, jsonify, current_app
import ipaddress
import hmac
import hashlib


# ---- IP 白名单 ----

def _parse_whitelist(whitelist_str: str) -> set:
    """解析白名单字符串（逗号分隔的 IP/CIDR）"""
    entries = set()
    for item in whitelist_str.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            # 支持 CIDR 格式
            if "/" in item:
                entries.add(ipaddress.ip_network(item, strict=False))
            else:
                entries.add(ipaddress.ip_address(item))
        except ValueError:
            continue
    return entries


def ip_whitelist(fn=None, *, custom_list: str = None, allow_localhost: bool = True):
    """
    IP 白名单装饰器：不在白名单中的 IP 返回 403

    支持两种用法:
        @ip_whitelist                         # 使用 config 中的 ADMIN_IP_WHITELIST
        @ip_whitelist(custom_list="192.168.1.0/24,10.0.0.1")
    """
    def _wrap(f):
        @wraps(f)
        def _wrapper(*args, **kwargs):
            client_ip = request.remote_addr or "0.0.0.0"

            # 始终允许 localhost
            if allow_localhost and client_ip in ("127.0.0.1", "::1", "localhost"):
                return f(*args, **kwargs)

            # 读取白名单
            whitelist_str = custom_list or current_app.config.get("ADMIN_IP_WHITELIST", "")
            if not whitelist_str:
                # 未配置白名单 = 不限制
                return f(*args, **kwargs)

            whitelist = _parse_whitelist(whitelist_str)
            try:
                client_addr = ipaddress.ip_address(client_ip)
            except ValueError:
                return _forbidden(client_ip)

            for entry in whitelist:
                if isinstance(entry, ipaddress.IPv4Network) or isinstance(entry, ipaddress.IPv6Network):
                    if client_addr in entry:
                        return f(*args, **kwargs)
                elif client_addr == entry:
                    return f(*args, **kwargs)

            return _forbidden(client_ip)
        return _wrapper

    if fn is None:
        return _wrap
    return _wrap(fn)


def _forbidden(ip: str):
    return jsonify({
        "code": -403,
        "msg": f"IP {ip} 不在白名单中",
        "ErrorDetails": "ip_whitelist"
    }), 403


# ---- 公开注册开关 ----

def disable_public_register():
    """
    检查是否允许公开注册。
    应在 /api/auth/register 中调用，生产环境返回 403。
    """
    if not current_app.config.get("ALLOW_PUBLIC_REGISTER", True):
        return jsonify({
            "code": -403,
            "msg": "公开注册已关闭，请联系管理员创建账号",
            "ErrorDetails": "register_disabled"
        }), 403
    return None


# ---- Admin Secret (后门密钥) ----

def check_admin_secret(request_obj=None) -> bool:
    """
    检查请求是否携带正确的 Admin Secret。
    从 Header (X-Admin-Secret) 或 Query (?admin_secret=) 中读取。
    用于脚本/CI 场景绕过 JWT，但需配合 IP 白名单使用。
    """
    req = request_obj or request
    expected = current_app.config.get("ADMIN_SECRET_KEY", "")
    if not expected:
        return False

    supplied = req.headers.get("X-Admin-Secret", "") or req.args.get("admin_secret", "")
    return hmac.compare_digest(supplied, expected)
