from flask import Blueprint, jsonify
from app.services.hardware_io import HardwareIO
from app.extensions import RedisConnector

"""
软件安装包相关接口

"""


# 创建硬件资源调用实例
hardwareController = HardwareIO()

# 创建 Redis 连接实例
redisConnector = RedisConnector('localhost', 6379, 0)
redisConnector.init_redis()
redisClient = redisConnector.client

# 创建蓝图
package_bp = Blueprint('package', __name__, url_prefix='/api')


def update_latest_package():
    """更新最新安装包信息到 Redis"""
    latest_file_name, latest_version_list = hardwareController.readLatestFile("落雨")
    print(latest_file_name, latest_version_list)
    # 转换为字符串
    latest_version_str = ".".join(map(str, latest_version_list))

    redisClient.set('latest_luorian_package', latest_file_name, ex=24 * 3600)  # 最新安装包文件名
    redisClient.set('latest_luorian_package_version', latest_version_str, ex=24 * 3600)  # 最新安装包版本号


@package_bp.route('/getLatestPackage', methods=['GET'])
def get_latest_package():
    """获取最新安装包信息"""
    update_latest_package()
    return {
        'latest_package': redisClient.get('latest_luorian_package'),
        'latest_version': redisClient.get('latest_luorian_package_version')
    }
