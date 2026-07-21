"""
TalkingData 数据统服务架构（待对接）

设计思路：
  - 所有统计事件通过 AnalyticsService 统一入口，解耦业务逻辑
  - 事件队列 + 批量上报，避免阻塞主流程
  - 后端统计 + 前端 SDK 双轨：后端精确统计核心事件，前端采集用户行为

事件命名规范（蛇形命名，前缀区分模块）：
  auth_login          登录成功
  auth_login_failed   登录失败
  auth_register       注册成功
  auth_logout         登出
  package_download    安装包下载
  package_check       版本检查
  page_view           页面访问

TalkingData SDK 接入步骤（后续完成）：
  1. 注册 TalkingData 账号，获取 App ID
  2. 安装 SDK: pip install talkingdata-sdk (如有) 或通过 HTTP API 上报
  3. 在 .env 中配置 TALKINGDATA_APP_ID 和 TALKINGDATA_ENABLED=true
  4. 对接本模块的 FlushWorker，实现批量上报
"""

import threading
import queue
import time
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    数据统计服务
    
    当前为桩实现（Stub），所有事件仅打印日志。
    后续接入 TalkingData 时修改 _send() 方法即可。
    """

    # TalkingData 配置（从环境变量读取）
    TD_APP_ID: Optional[str] = None
    TD_ENABLED: bool = False

    # 事件队列 & 后台 Worker
    _queue: queue.Queue = queue.Queue()
    _worker: Optional[threading.Thread] = None
    _running: bool = False

    # 批量上报配置
    BATCH_SIZE: int = 20       # 每批最多上报条数
    FLUSH_INTERVAL: int = 10   # 最长等待间隔（秒）

    @classmethod
    def init_app(cls, app):
        """根据 Flask 配置初始化统计服务"""
        cls.TD_APP_ID = app.config.get('TALKINGDATA_APP_ID', None)
        cls.TD_ENABLED = app.config.get('TALKINGDATA_ENABLED', False)
        if cls.TD_ENABLED:
            cls.start_worker()
            logger.info(f"[TD] TalkingData initialized (app_id={cls.TD_APP_ID})")

    @classmethod
    def start_worker(cls):
        """启动后台批量上报线程"""
        if cls._running:
            return
        cls._running = True
        cls._worker = threading.Thread(target=cls._flush_loop, daemon=True)
        cls._worker.start()
        logger.info("[TD] Background flush worker started")

    @classmethod
    def _flush_loop(cls):
        """后台线程：定时批量上报"""
        bucket = []
        last_flush = time.time()

        while cls._running:
            try:
                event = cls._queue.get(timeout=1)
                bucket.append(event)

                # 批满 或 距上次冲刷超时
                if len(bucket) >= cls.BATCH_SIZE or time.time() - last_flush >= cls.FLUSH_INTERVAL:
                    cls._send(bucket)
                    bucket = []
                    last_flush = time.time()
            except queue.Empty:
                # 超时无新事件，冲刷残留
                if bucket and time.time() - last_flush >= cls.FLUSH_INTERVAL:
                    cls._send(bucket)
                    bucket = []
                    last_flush = time.time()

    @classmethod
    def _send(cls, events: list):
        """
        批量上报事件（桩实现，仅打印日志）
        TODO: 替换为 TalkingData HTTP API 调用
        """
        if cls.TD_ENABLED:
            logger.info(f"[TD] Batch report {len(events)} events:")
            for ev in events:
                logger.info(f"  - {ev['event']} | user={ev.get('user','?')} | {json.dumps(ev.get('data',{}), ensure_ascii=False)}")

    # ---- 公共 API ----

    @classmethod
    def track(cls, event: str, user: str = "", data: dict = None):
        """
        记录统计事件

        Args:
            event: 事件名（aa_bb 格式）
            user: 当前用户名（匿名用户传空）
            data: 附加数据（如页面路径、设备信息等）
        """
        payload = {
            "event": event,
            "user": user or "anonymous",
            "timestamp": int(time.time()),
            "data": data or {}
        }
        if cls.TD_ENABLED:
            cls._queue.put(payload)
        else:
            # 开发环境直接打日志
            logger.debug(f"[TD] {event} | user={user or 'anonymous'} | {json.dumps(data or {}, ensure_ascii=False)}")

    @classmethod
    def track_auth_login(cls, username: str, success: bool, reason: str = ""):
        """登录事件（成功/失败）"""
        event = "auth_login" if success else "auth_login_failed"
        cls.track(event, user=username, data={"success": success, "reason": reason})

    @classmethod
    def track_auth_register(cls, username: str, success: bool, reason: str = ""):
        """注册事件"""
        cls.track("auth_register", user=username, data={"success": success, "reason": reason})

    @classmethod
    def track_auth_logout(cls, username: str):
        """登出事件"""
        cls.track("auth_logout", user=username)

    @classmethod
    def track_package_download(cls, filename: str, user: str = ""):
        """安装包下载事件"""
        cls.track("package_download", user=user, data={"filename": filename})

    @classmethod
    def track_package_check(cls, current_ver: str, latest_ver: str, user: str = ""):
        """版本检查事件"""
        cls.track("package_check", user=user, data={
            "current_version": current_ver,
            "latest_version": latest_ver
        })


# 全局单例
analytics = AnalyticsService()
