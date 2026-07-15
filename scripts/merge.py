import os
import re
import glob
import subprocess

# --- 配置 ---
PREFIX = "file"
SUFFIX = ".mp4"
OUTPUT_FILE = "output.mp4"
FILE_LIST = "filelist.txt"

def find_and_sort_files(prefix, suffix):
    """自动查找并按数字顺序排序文件。"""
    # 使用 glob 查找所有匹配格式的文件
    pattern = f"{prefix}*{suffix}"
    files = glob.glob(pattern)
    
    # 定义一个函数，用于从文件名中提取数字部分
    def extract_number(filename):
        # 使用正则表达式查找文件名中的所有数字
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else -1

    # 根据提取的数字对文件列表进行排序
    # 这样可以确保 video2.mp4 在 video10.mp4 之前
    files.sort(key=extract_number)
    return files

def merge_auto_delete():
    """自动查找、合并并提示删除视频分片。"""
    
    print("正在自动查找并排序分片文件...")
    existing_files = find_and_sort_files(PREFIX, SUFFIX)

    if not existing_files:
        print(f"错误：未找到任何符合 '{PREFIX}*{SUFFIX}' 格式的视频分片。")
        return

    print("找到以下文件，将按此顺序合并:")
    for f in existing_files:
        print(f" - {f}")

    # 创建 FFmpeg 需要的文件列表
    with open(FILE_LIST, "w", encoding="utf-8") as f:
        for filename in existing_files:
            f.write(f"file '{filename}'\n")

    command = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", FILE_LIST, "-c", "copy", OUTPUT_FILE]

    print("\n正在执行 FFmpeg 命令进行合并...")
    print(" ".join(command))

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"\n合并成功！输出文件为: {OUTPUT_FILE}")

        confirm = input(f"是否要删除原始的 {len(existing_files)} 个视频分片? (y/N): ").lower()
        if confirm in ['y', 'yes']:
            print("正在删除原始分片...")
            for file in existing_files:
                try:
                    os.remove(file)
                    print(f"已删除: {file}")
                except OSError as e:
                    print(f"删除文件 {file} 时出错: {e}")
            print("原始分片已删除。")
        else:
            print("未删除原始分片。")

    except FileNotFoundError:
        print("\n错误: 未找到 'ffmpeg' 命令。请确保已正确安装并配置了环境变量。")
    except subprocess.CalledProcessError as e:
        print("\nFFmpeg 执行出错:")
        print(e.stderr)
        print("合并失败，未删除任何文件。")
    finally:
        if os.path.exists(FILE_LIST):
            os.remove(FILE_LIST)
    
    print("\n脚本执行完毕。")

if __name__ == "__main__":
    merge_auto_delete()