"""
前端事件采集接口（TalkingData 通道）

设计思路：
  TalkingData 本质上是一个"不用登录就能上报事件"的统计 SDK。
  本模块提供等价的后端收口：前端通过 HTTP POST 推送事件，
  后端接入 AnalyticsService 事件队列，最终批量推给 TalkingData。

接口特点：
  - 无需登录（开放接口），与 TalkingData 的匿名统计理念一致
  - 支持单条/批量上报
  - 轻量校验 + 快速响应，不阻塞前端
"""

from flask import Blueprint, jsonify, request
from app.services.analytics import analytics
import time
import re

events_bp = Blueprint('events', __name__, url_prefix='/api/events')

# 事件名验证
_EVENT_PATTERN = re.compile(r'^[a-z][a-z0-9_]*(:[a-z][a-z0-9_]*)*$')


class EventsController:
    """前端事件入口控制器"""

    def track(self):
        """
        POST /api/events/track
        Content-Type: application/json

        TalkingData 风格的匿名事件上报接口。
        无需登录，前端接入后即可自动采集用户行为。

        === 请求体（单条） ===
        {
            "event": "page_view",
            "data": {
                "page": "/home",
                "duration_ms": 3200,
                "device": "android"
            },
            "user_id": "optional_device_or_user_id"
        }

        === 请求体（批量） ===
        {
            "events": [
                {"event": "page_view", "data": {"page": "/home"}},
                {"event": "button_click", "data": {"button": "download"}}
            ]
        }

        === 成功响应 ===
        {"code": 0, "msg": "ok", "accepted": 1}         // 单条
        {"code": 0, "msg": "ok", "accepted": 5}         // 批量

        === 失败响应 ===
        {"code": -15, "msg": "事件数据格式错误", "ErrorDetails": "..."}

        === 前端调用示例 ===
        // 单条
        fetch("/api/events/track", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                event: "page_view",
                data: { page: "/dashboard" }
            })
        });

        // 批量
        fetch("/api/events/track", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                events: [
                    {event: "page_view", data: {page: "/login"}},
                    {event: "button_click", data: {button: "login_btn"}}
                ]
            })
        });
        """
        body = request.get_json(silent=True)
        if not body:
            return jsonify({
                "code": -15, "msg": "请求体不能为空", "ErrorDetails": ""
            }), 400

        # 批量模式
        if "events" in body:
            events = body["events"]
            if not isinstance(events, list) or len(events) == 0:
                return jsonify({
                    "code": -15, "msg": "events 必须是非空数组", "ErrorDetails": ""
                }), 400
            if len(events) > 100:
                return jsonify({
                    "code": -15, "msg": "单次最多上报 100 条事件", "ErrorDetails": ""
                }), 400

            accepted = 0
            for ev in events:
                if self._accept(ev):
                    accepted += 1
            return jsonify({"code": 0, "msg": "ok", "accepted": accepted})

        # 单条模式
        if self._accept(body):
            return jsonify({"code": 0, "msg": "ok", "accepted": 1})
        else:
            return jsonify({
                "code": -15, "msg": "事件格式错误（缺少 event 字段）", "ErrorDetails": ""
            }), 400

    def _accept(self, ev: dict) -> bool:
        """
        校验并接收单条事件
        返回 True 表示已入队，False 表示格式非法
        """
        if not isinstance(ev, dict):
            return False

        event_name = ev.get("event", "")
        if not event_name or not isinstance(event_name, str):
            return False

        # 事件名校验（宽松：允许 a-z 0-9 _ : 组合）
        if not _EVENT_PATTERN.fullmatch(event_name):
            return False

        user_id = str(ev.get("user_id", ev.get("user", "")))
        event_data = ev.get("data", {})
        if not isinstance(event_data, dict):
            event_data = {}

        # 注入客户端 IP 和 User-Agent（可选）
        event_data.setdefault("_ip", request.remote_addr or "")
        event_data.setdefault("_ua", request.headers.get("User-Agent", "")[:200])
        event_data.setdefault("_ts", int(time.time() * 1000))

        analytics.track(event_name, user=user_id, data=event_data)
        return True


# 路由注册
ctrl = EventsController()
events_bp.route('/track', methods=['POST'])(ctrl.track)
