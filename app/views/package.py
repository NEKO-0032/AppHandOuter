"""
安装包蓝图 — 版本检查 / 下载

已重构: 核心逻辑移入 app.services.package_service.PackageService
"""

from flask import Blueprint, jsonify, send_from_directory, current_app
from app.extentions_reali import hardwareController, redisClient
from app.services.package_service import PackageService

package_bp = Blueprint('package', __name__, url_prefix='/api')


def sync_and_get_latest():
    """返回最新版本信息"""
    synced = PackageService.sync_from_disk()
    latest = PackageService.get_latest()
    return latest


@package_bp.route('/getLatestPackage', methods=['GET'])
def get_latest_package():
    """获取最新安装包信息（兼容旧接口）"""
    latest = PackageService.get_latest()
    if not latest:
        return {"latest_package": None, "latest_version": "0.0.0"}

    return {
        "latest_package": latest["filename"],
        "latest_version": latest["version"]
    }


@package_bp.route('/download/<filename>', methods=['GET'])
def download_package(filename):
    """下载指定安装包"""
    storage = PackageService.get_storage_dir()
    return send_from_directory(storage, filename, as_attachment=True)
