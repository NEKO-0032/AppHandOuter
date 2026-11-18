"""
安装包服务 — 统一管理 APK 的上传、版本校验、Redis 元数据、磁盘存储

Redis 数据结构:
  packages:index         → List[filename]           按上传时间倒序排列的文件名列表
  package:<filename>     → Hash {version,size_mb,uploaded_at,uploader,path}
  latest_luorian_package          → str   最新安装包文件名（兼容旧 key）
  latest_luorian_package_version  → str   最新安装包版本号

命名规范:  落雨<主>_<次>_<补>.apk  例: 落雨1_1_0.apk
版本比较:  逐位数字比较，不允许上传 ≤ 当前最大版本
"""

import os
import re
import time
import json
from typing import Optional, Tuple, List

from app.extentions_reali import redisClient
from app.config import Config

# 命名规范正则
_PATTERN_NAME = re.compile(r'^落雨(\d+)_(\d+)_(\d+)\.apk$')

# 上传限制
MAX_FILE_SIZE_MB = 500        # 单文件最大 500MB
ALLOWED_EXTENSIONS = {'.apk'}

# Redis key 前缀
_KEY_INDEX = 'packages:index'           # 文件名列表
_KEY_PREFIX = 'package:'                # 单包元数据前缀
_KEY_LATEST_FILE = 'latest_luorian_package'
_KEY_LATEST_VER  = 'latest_luorian_package_version'


# ============================================================
#  工具函数
# ============================================================
def _parse_version(filename: str) -> Optional[Tuple[int, int, int]]:
    """从文件名提取版本号元组 或 None"""
    m = _PATTERN_NAME.match(filename)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _version_str(ver: Tuple[int, int, int]) -> str:
    return f"{ver[0]}.{ver[1]}.{ver[2]}"


# ============================================================
#  PackageService
# ============================================================
class PackageService:

    @staticmethod
    def get_storage_dir() -> str:
        """安装包存储目录（优先 Config，回退到环境变量/默认值）"""
        path = Config.BINARY_FILES_PATH or './binaryFiles'
        os.makedirs(path, exist_ok=True)
        return path

    # ---- 查询 ----

    @staticmethod
    def get_all_packages() -> List[dict]:
        """返回所有安装包信息（最新在前）"""
        filenames = redisClient.lrange(_KEY_INDEX, 0, -1)
        result = []
        for fn in filenames:
            meta = PackageService._get_meta(fn)
            if meta:
                result.append(meta)
        return result

    @staticmethod
    def get_latest() -> Optional[dict]:
        """返回最新安装包信息"""
        fn = redisClient.get(_KEY_LATEST_FILE)
        if not fn:
            return None
        return PackageService._get_meta(fn)

    @staticmethod
    def _get_meta(filename: str) -> Optional[dict]:
        """从 Redis 读取单个包的元数据"""
        data = redisClient.hgetall(_KEY_PREFIX + filename)
        if not data:
            return None
        ver = _parse_version(filename)
        return {
            "filename": filename,
            "version": data.get("version", ""),
            "version_tuple": list(ver) if ver else [],
            "size_mb": data.get("size_mb", "0"),
            "uploaded_at": data.get("uploaded_at", ""),
            "uploader": data.get("uploader", ""),
            "path": data.get("path", "")
        }

    # ---- 上传 ----

    @staticmethod
    def upload(file_obj, uploader: str = "", changelog: str = "") -> Tuple[bool, str, Optional[dict]]:
        """
        上传安装包（完整校验流程）

        Args:
            file_obj:  Flask request.files['file'] 对象
            uploader:  上传者用户名
            changelog: 更新日志（暂存 Redis，后续可扩展）

        Returns:
            (success, message, metadata_dict_or_None)
        """
        filename = file_obj.filename or ""

        # === 1. 扩展名校验 ===
        _, ext = os.path.splitext(filename)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            return False, f"仅允许 {', '.join(ALLOWED_EXTENSIONS)} 格式", None

        # === 2. 命名规范校验 ===
        ver = _parse_version(filename)
        if ver is None:
            return False, "文件名不符合规范: 落雨<主版本>_<次版本>_<补丁版本>.apk，如 落雨1_0_0.apk", None

        # === 3. 版本比较（不允许降级） ===
        latest = PackageService.get_latest()
        if latest and latest.get("version_tuple"):
            latest_ver = tuple(latest["version_tuple"])
            if ver <= latest_ver:
                return False, (
                    f"不允许上传更低或相同版本 (当前最新: {_version_str(latest_ver)}, "
                    f"你上传的是: {_version_str(ver)})"
                ), None

        # === 4. 文件大小校验 ===
        file_obj.seek(0, os.SEEK_END)
        file_size = file_obj.tell()
        file_obj.seek(0)
        size_mb = round(file_size / (1024 * 1024), 2)
        if size_mb > MAX_FILE_SIZE_MB:
            return False, f"文件过大 ({size_mb}MB)，上限 {MAX_FILE_SIZE_MB}MB", None

        # === 5. 保存到磁盘 ===
        storage = PackageService.get_storage_dir()
        save_path = os.path.join(storage, filename)
        file_obj.save(save_path)

        # === 6. 写入 Redis 元数据 ===
        uploaded_at = time.strftime("%Y-%m-%d %H:%M:%S")
        meta_key = _KEY_PREFIX + filename
        redisClient.hset(meta_key, mapping={
            "version": _version_str(ver),
            "size_mb": str(size_mb),
            "uploaded_at": uploaded_at,
            "uploader": uploader,
            "path": save_path
        })
        redisClient.expire(meta_key, 365 * 86400)  # 365 天过期

        # 添加到索引列表（最新在前）
        redisClient.lpush(_KEY_INDEX, filename)

        # 更新 latest 指针
        redisClient.set(_KEY_LATEST_FILE, filename)
        redisClient.set(_KEY_LATEST_VER, _version_str(ver))

        meta = {
            "filename": filename,
            "version": _version_str(ver),
            "version_tuple": list(ver),
            "size_mb": size_mb,
            "uploaded_at": uploaded_at,
            "uploader": uploader,
            "path": save_path
        }
        return True, "上传成功", meta

    # ---- 启动时同步 ----

    @staticmethod
    def sync_from_disk():
        """
        启动时从磁盘扫描所有 APK，同步到 Redis
        用于首次部署或 Redis 数据丢失后的恢复

        示例流程（第一包落雨1_0_0.apk）:
          1. 扫描 ./binaryFiles/ 下所有 落雨*_*_*.apk
          2. 按版本排序
          3. 逐个写入 Redis (package:xxx 元数据 + packages:index)
          4. 最后一个（最高版本）设为 latest
        """
        storage = PackageService.get_storage_dir()
        if not os.path.isdir(storage):
            return []

        # 收集所有合法安装包
        packages = []
        for fname in os.listdir(storage):
            ver = _parse_version(fname)
            if ver is None:
                continue
            full_path = os.path.join(storage, fname)
            size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 2)
            packages.append((ver, fname, full_path, size_mb))

        if not packages:
            return []

        # 按版本升序排列
        packages.sort(key=lambda x: x[0])

        # 清空旧索引
        redisClient.delete(_KEY_INDEX)

        synced = []
        for ver, fname, fpath, size_mb in packages:
            meta_key = _KEY_PREFIX + fname
            redisClient.hset(meta_key, mapping={
                "version": _version_str(ver),
                "size_mb": str(size_mb),
                "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "uploader": "auto-sync",
                "path": fpath
            })
            redisClient.expire(meta_key, 365 * 86400)
            # lpush 保证最终列表是最新在前
            redisClient.lpush(_KEY_INDEX, fname)
            synced.append({
                "filename": fname,
                "version": _version_str(ver),
                "size_mb": size_mb
            })

        # 最高版本 = 列表最后一个
        latest = packages[-1]
        redisClient.set(_KEY_LATEST_FILE, latest[1])
        redisClient.set(_KEY_LATEST_VER, _version_str(latest[0]))

        return synced
