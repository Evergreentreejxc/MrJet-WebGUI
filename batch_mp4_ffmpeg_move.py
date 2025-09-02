import os
import sys
import subprocess
import tempfile
import shutil

# 修改为你的目标文件夹（必须存在，或者改为自动创建）
DEST_DIR = r"D:\IDM Download"

def find_mp4_files(path):
    mp4_files = []
    if os.path.isfile(path) and path.lower().endswith('.mp4'):
        mp4_files.append(os.path.abspath(path))
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith('.mp4'):
                    mp4_files.append(os.path.abspath(os.path.join(root, file)))
    return mp4_files

def is_already_faststarted(file_path):
    # 简单判断已封装：用 ffprobe 查 moov atom 是否在文件头部
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "format_tags=major_brand", "-of", "default=nw=1:nk=1", file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        # 只要能正常读取格式就认为封装过，或者可用更复杂的判断
        return True
    except Exception:
        return False

def ffmpeg_faststart_overwrite(input_file):
    dir_name = os.path.dirname(input_file)
    with tempfile.NamedTemporaryFile(dir=dir_name, suffix='.mp4', delete=False) as tmpfile:
        tempname = tmpfile.name
    cmd = [
        'ffmpeg',
        '-y',
        '-i', input_file,
        '-c', 'copy',
        '-movflags', 'faststart',
        tempname
    ]
    try:
        print(f"正在封装: {input_file}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        shutil.move(tempname, input_file)
        print(f"覆盖完成: {input_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"封装失败: {input_file}")
        print(e.stderr.decode())
        if os.path.exists(tempname):
            os.remove(tempname)
        return False

def move_to_dest(file_path, dest_dir):
    file_name = os.path.basename(file_path)
    dest_path = os.path.join(dest_dir, file_name)
    # 防止重名覆盖
    base, ext = os.path.splitext(dest_path)
    i = 1
    while os.path.exists(dest_path):
        dest_path = f"{base}_{i}{ext}"
        i += 1
    shutil.move(file_path, dest_path)
    print(f"已移动到: {dest_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python batch_mp4_faststart_move.py <文件夹路径或mp4文件路径>")
        sys.exit(1)
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
    target_path = sys.argv[1]
    mp4_list = find_mp4_files(target_path)
    if not mp4_list:
        print("未找到 mp4 文件。")
        sys.exit(0)
    print(f"共找到 {len(mp4_list)} 个 mp4 文件，开始处理...")

    for mp4_file in mp4_list:
        # 跳过已封装文件（可自定义规则，示例默认全部处理）
        # 若需严格判断是否已经 faststart 可用 is_already_faststarted 方法
        # if is_already_faststarted(mp4_file):
        #     print(f"已封装，跳过: {mp4_file}")
        #     continue
        # 简单跳过已移动的文件（比如目标目录已存在同名文件）
        if os.path.abspath(os.path.dirname(mp4_file)) == os.path.abspath(DEST_DIR):
            print(f"目标目录已存在，跳过: {mp4_file}")
            continue
        result = ffmpeg_faststart_overwrite(mp4_file)
        if result:
            move_to_dest(mp4_file, DEST_DIR)
    print("批量封装并移动完成。")