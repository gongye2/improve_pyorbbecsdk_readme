#!/usr/bin/env python3
"""
修复 pyorbbecsdk pyi 文件中的返回类型问题

使用方法:
    python fix_pyi.py <input_pyi_file> [output_pyi_file]

如果不指定 output_pyi_file，则直接修改输入文件。
"""

import re
import sys
from pathlib import Path


def fix_pyi_content(content: str) -> str:
    """修复 pyi 文件内容中的返回类型问题"""

    # 1. 修复 typing_extensions.Buffer 导入问题
    # pybind11_stubgen 生成 typing_extensions.Buffer 但不添加 import
    if 'typing_extensions.Buffer' in content and 'import typing_extensions' not in content:
        # 在文件开头添加 typing_extensions 导入
        # 查找最后一个 import 语句的位置
        import_pattern = r'^(import .+|from .+ import .+)$'
        last_import_end = 0
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            last_import_end = match.end()

        if last_import_end > 0:
            # 在最后一个 import 后添加 typing_extensions 导入
            content = content[:last_import_end] + '\nimport typing_extensions' + content[last_import_end:]
        else:
            # 如果没有找到 import，在文件开头添加（跳过可能的 shebang 和 docstring）
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('#') or line.strip() == '':
                    insert_pos = i + 1
                else:
                    break
            lines.insert(insert_pos, 'import typing_extensions')
            content = '\n'.join(lines)

    # 2. 修复枚举类型默认参数值
    # pybind11_stubgen 无法解析 C++ 枚举默认值，生成 ... 作为占位符
    # 使用行级别的替换，匹配整个函数签名行
    ENUM_DEFAULTS = [
        # Config 类方法 - enable_accel_stream (有两个参数需要修复)
        (r'(def enable_accel_stream\(self, full_scale_range: OBAccelFullScaleRange) = \.\.\., (sample_rate: OBGyroSampleRate) = \.\.\.', r'\1 = OBAccelFullScaleRange.ACCEL_FS_UNKNOWN, \2 = OBGyroSampleRate.SAMPLE_RATE_UNKNOWN'),
        # Config 类方法 - enable_gyro_stream
        (r'(def enable_gyro_stream\(self, full_scale_range: OBGyroFullScaleRange) = \.\.\., (sample_rate: OBGyroSampleRate) = \.\.\.', r'\1 = OBGyroFullScaleRange.FS_UNKNOWN, \2 = OBGyroSampleRate.SAMPLE_RATE_UNKNOWN'),
        # Config 类方法 - enable_lidar_stream
        (r'(def enable_lidar_stream\(self, scan_rate: OBLiDARScanRate) = \.\.\., (format: OBFormat) = \.\.\.', r'\1 = OBLiDARScanRate.LIDAR_SCAN_UNKNOWN, \2 = OBFormat.UNKNOWN_FORMAT'),
        # Config 类方法 - enable_video_stream
        (r'(def enable_video_stream\(.*format: OBFormat) = \.\.\.', r'\1 = OBFormat.UNKNOWN_FORMAT'),
        # Context 类方法
        (r'(def create_net_device\(.*access_mode: OBDeviceAccessMode) = \.\.\.', r'\1 = OBDeviceAccessMode.OB_DEVICE_DEFAULT_ACCESS'),
        # DeviceList 类方法
        (r'(def get_device_by_index\(.*access_mode: OBDeviceAccessMode) = \.\.\.', r'\1 = OBDeviceAccessMode.OB_DEVICE_DEFAULT_ACCESS'),
        (r'(def get_device_by_serial_number\(.*access_mode: OBDeviceAccessMode) = \.\.\.', r'\1 = OBDeviceAccessMode.OB_DEVICE_DEFAULT_ACCESS'),
        (r'(def get_device_by_uid\(.*access_mode: OBDeviceAccessMode) = \.\.\.', r'\1 = OBDeviceAccessMode.OB_DEVICE_DEFAULT_ACCESS'),
        # StreamProfileList 类方法
        (r'(def get_video_stream_profile\(.*format: OBFormat) = \.\.\.', r'\1 = OBFormat.UNKNOWN_FORMAT'),
    ]

    for pattern, replacement in ENUM_DEFAULTS:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            print(f"  Fixed: {pattern[:50]}...")
        content = new_content

    # 定义需要修复的方法映射：类名 -> {方法名: 返回类型}
    FIXES = {
        # Frame 类
        "Frame": {
            "as_video_frame": "VideoFrame",
            "as_color_frame": "ColorFrame",
            "as_depth_frame": "DepthFrame",
            "as_ir_frame": "IRFrame",
            "as_frame_set": "FrameSet",
            "as_accel_frame": "AccelFrame",
            "as_gyro_frame": "GyroFrame",
            "as_confidence_frame": "ConfidenceFrame",
            "as_points_frame": "PointsFrame",
            "as_lidar_points_frame": "LiDARPointsFrame",
        },
        # VideoFrame 类
        "VideoFrame": {
            "as_color_frame": "ColorFrame",
            "as_depth_frame": "DepthFrame",
            "as_ir_frame": "IRFrame",
            "as_confidence_frame": "ConfidenceFrame",
            "as_points_frame": "PointsFrame",
        },
        # StreamProfile 类
        "StreamProfile": {
            "as_video_stream_profile": "VideoStreamProfile",
            "as_accel_stream_profile": "AccelStreamProfile",
            "as_gyro_stream_profile": "GyroStreamProfile",
            "as_lidar_stream_profile": "LiDARStreamProfile",
        },
    }

    # 修复方法：找到类定义，然后修复其中的方法
    for class_name, methods in FIXES.items():
        for method_name, return_type in methods.items():
            # 匹配类中的方法定义
            # 格式: def method_name(self) -> ...:
            pattern = rf'(class {class_name}[^{{]*?\n)(.*?)(def {method_name}\(self\) -> \.\.\.:)'
            replacement = rf'\1\2def {method_name}(self) -> {return_type}:'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # 修复特殊返回类型（带类型参数的泛型）
    # Sensor.get_recommended_filters() -> list[...] 修复为 list[Filter]
    content = re.sub(
        r'(class Sensor[^{]*?\n)(.*?)(def get_recommended_filters\(self\) -> list\[\.\.\.\]:)',
        r'\1\2def get_recommended_filters(self) -> list[Filter]:',
        content,
        flags=re.DOTALL
    )

    return content


def fix_pyi_file(input_path: Path, output_path: Path = None) -> None:
    """修复 pyi 文件"""
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path
    else:
        output_path = Path(output_path)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    print(f"Reading: {input_path}")
    content = input_path.read_text(encoding='utf-8')

    fixed_content = fix_pyi_content(content)

    if content == fixed_content:
        print("No changes needed.")
    else:
        output_path.write_text(fixed_content, encoding='utf-8')
        print(f"Fixed: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_pyi.py <input_pyi_file> [output_pyi_file]")
        print("")
        print("Example:")
        print("  python fix_pyi.py pyorbbecsdk.pyi")
        print("  python fix_pyi.py pyorbbecsdk.pyi pyorbbecsdk_fixed.pyi")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    fix_pyi_file(input_path, output_path)


if __name__ == "__main__":
    main()
