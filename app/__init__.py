from flask import Flask
from app.config import Config
import os
from app.views import package_bp, auth_bp, dashboard_bp, events_bp
from app.utils import JWTManager
from app.services.analytics import analytics


# 全局 JWT 管理器实例
jwt_manager = JWTManager()


def create_app(config_class=Config):
    """应用工厂函数"""
    # 项目根目录（app 的父目录）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # 加载配置
    app.config.from_object(config_class)

    # 初始化 JWT
    jwt_manager.init_app(app)

    # 初始化 TalkingData 统计（桩实现，不影响业务）
    analytics.init_app(app)

    # 注册蓝图
    app.register_blueprint(package_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(events_bp)

    return app
