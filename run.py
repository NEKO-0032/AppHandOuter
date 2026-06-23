from app import create_app
from app.views.package import update_latest_package

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 启动前更新最新安装包信息
    update_latest_package()
    app.run(debug=True)
