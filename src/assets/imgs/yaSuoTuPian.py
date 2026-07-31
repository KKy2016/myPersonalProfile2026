import sys
import os
from PIL import Image

def compress_image(input_path, output_path, target_size_kb=500, max_attempts=10):
    """
    压缩图片至指定大小以下（单位KB）
    策略：优先降低质量（JPEG）或压缩级别（PNG），若无效则缩小尺寸
    """
    if not os.path.exists(input_path):
        print(f"错误：文件 {input_path} 不存在")
        return

    # 打开图片并保留原始格式
    with Image.open(input_path) as img:
        original_format = img.format
        # 如果是PNG且无法通过质量调整，可能需要转为JPEG，但这里先保留原格式
        # 对于JPEG，直接调整quality
        # 对于PNG，可以调整compress_level，但效果有限，若不行则转为JPEG
        # 我们用更通用的方式：先尝试质量压缩，如果不行再缩放

        # 1. 获取原始尺寸
        width, height = img.size

        # 2. 尝试降低质量（仅对JPEG有效，PNG则调整压缩级别）
        if original_format.upper() == 'JPEG':
            # 质量从95开始尝试，逐步降低
            for quality in range(95, 10, -5):
                # 保存到临时文件检查大小
                temp_path = output_path + '.tmp'
                img.save(temp_path, format='JPEG', quality=quality, optimize=True)
                size_kb = os.path.getsize(temp_path) / 1024
                os.remove(temp_path)
                if size_kb <= target_size_kb:
                    # 最终保存
                    img.save(output_path, format='JPEG', quality=quality, optimize=True)
                    print(f"压缩成功：质量={quality}, 大小={size_kb:.2f}KB")
                    return
            # 若质量降到最低仍大于目标，则缩放
            print("质量压缩无法达到目标，尝试缩小尺寸...")
            scale_down(img, output_path, target_size_kb, original_format)

        elif original_format.upper() == 'PNG':
            # PNG 先尝试调整压缩级别（0-9），但通常效果不大
            for compress_level in range(9, -1, -1):
                temp_path = output_path + '.tmp'
                img.save(temp_path, format='PNG', compress_level=compress_level, optimize=True)
                size_kb = os.path.getsize(temp_path) / 1024
                os.remove(temp_path)
                if size_kb <= target_size_kb:
                    img.save(output_path, format='PNG', compress_level=compress_level, optimize=True)
                    print(f"压缩成功：压缩级别={compress_level}, 大小={size_kb:.2f}KB")
                    return
            # 若PNG压缩无效，考虑转为JPEG（如果允许改变格式）
            print("PNG压缩无法达到目标，尝试转换为JPEG...")
            # 转换为RGB（如果需要）
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            # 然后按JPEG方式处理
            for quality in range(95, 10, -5):
                temp_path = output_path + '.tmp'
                img.save(temp_path, format='JPEG', quality=quality, optimize=True)
                size_kb = os.path.getsize(temp_path) / 1024
                os.remove(temp_path)
                if size_kb <= target_size_kb:
                    # 最终保存为JPEG（注意修改扩展名）
                    base, ext = os.path.splitext(output_path)
                    final_path = base + '.jpg'
                    img.save(final_path, format='JPEG', quality=quality, optimize=True)
                    print(f"转换为JPEG并压缩成功，质量={quality}, 大小={size_kb:.2f}KB, 保存为 {final_path}")
                    return
            # 若转JPEG后仍不行，缩放
            print("转换为JPEG后仍无法达到目标，尝试缩小尺寸...")
            scale_down(img, output_path, target_size_kb, 'JPEG')  # 转为JPEG并缩放

        else:
            # 其他格式（如BMP、GIF等）先尝试转JPEG
            print(f"不支持的格式 {original_format}，尝试转换为JPEG...")
            img = img.convert('RGB')
            for quality in range(95, 10, -5):
                temp_path = output_path + '.tmp'
                img.save(temp_path, format='JPEG', quality=quality, optimize=True)
                size_kb = os.path.getsize(temp_path) / 1024
                os.remove(temp_path)
                if size_kb <= target_size_kb:
                    base, ext = os.path.splitext(output_path)
                    final_path = base + '.jpg'
                    img.save(final_path, format='JPEG', quality=quality, optimize=True)
                    print(f"转换为JPEG并压缩成功，质量={quality}, 大小={size_kb:.2f}KB, 保存为 {final_path}")
                    return
            # 还不行就缩放
            print("转换JPEG后仍无法达到目标，尝试缩小尺寸...")
            scale_down(img, output_path, target_size_kb, 'JPEG')

def scale_down(img, output_path, target_size_kb, target_format):
    """按比例缩小图片尺寸直到大小低于目标"""
    width, height = img.size
    # 如果已经是RGB，否则转换
    if target_format.upper() == 'JPEG' and img.mode != 'RGB':
        img = img.convert('RGB')

    # 循环缩小比例
    scale = 0.9
    while scale > 0.1:
        new_width = int(width * scale)
        new_height = int(height * scale)
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        # 保存并检查大小
        temp_path = output_path + '.tmp'
        if target_format.upper() == 'JPEG':
            resized_img.save(temp_path, format='JPEG', quality=85, optimize=True)
        else:
            resized_img.save(temp_path, format=target_format, optimize=True)
        size_kb = os.path.getsize(temp_path) / 1024
        os.remove(temp_path)
        if size_kb <= target_size_kb:
            # 最终保存
            if target_format.upper() == 'JPEG':
                resized_img.save(output_path, format='JPEG', quality=85, optimize=True)
            else:
                resized_img.save(output_path, format=target_format, optimize=True)
            print(f"缩小尺寸成功：新尺寸={new_width}x{new_height}, 大小={size_kb:.2f}KB")
            return
        scale -= 0.05
    # 如果还是不行，最低质量保存
    print("尝试最低质量保存...")
    if target_format.upper() == 'JPEG':
        img.save(output_path, format='JPEG', quality=10, optimize=True)
    else:
        img.save(output_path, format=target_format, optimize=True)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"最终保存，大小={size_kb:.2f}KB，可能低于或略高于目标")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python compress_image.py <输入图片路径> <输出图片路径> [目标大小KB，默认500]")
        sys.exit(1)
    input_img = sys.argv[1]
    output_img = sys.argv[2]
    target = 500
    if len(sys.argv) >= 4:
        try:
            target = int(sys.argv[3])
        except ValueError:
            print("目标大小必须是整数（KB），使用默认值500")
    compress_image(input_img, output_img, target)