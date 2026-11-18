from app import create_app
from app.services.package_service import PackageService

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 启动前同步磁盘中的安装包到 Redis
    synced = PackageService.sync_from_disk()
    if synced:
        print(f"[init] 已同步 {len(synced)} 个安装包到 Redis")
    app.run(debug=True)
