import os

class HardwareIO:
    """硬件资源操作类"""
    
    def __init__(self, binary_files_path=None):
        # 如果没有指定路径，使用默认路径
        if binary_files_path is None:
            self.binary_files_path = "./binaryFiles/"
        else:
            self.binary_files_path = binary_files_path

    def readLatestFile(self, target_file: str) -> tuple[str, list[int]]:
        """
        读取最新文件
        :param target_file: 目标文件名
        :return: 最新文件名与版本号列表
        :rtype: tuple[str, list[int]]
        """
        latest_version_tuple = (0, 0, 0)

        file_list = os.listdir(self.binary_files_path)
        for file in file_list:
            if file.startswith(target_file):
                f = file.replace(target_file, "")
                f = f.replace(".apk", "")
                f = f.split("_")

                try:
                    f_tuple = tuple(int(x) for x in f)
                except ValueError:
                    continue
                if f_tuple > latest_version_tuple:
                    latest_version_tuple = f_tuple
        
        final_string = f"{target_file}{latest_version_tuple[0]}"
        for i in range(1, len(latest_version_tuple)):
            final_string += f"_{latest_version_tuple[i]}"

        # 返回最新安装包文件名与版本号列表
        return (final_string + ".apk", list(latest_version_tuple))
