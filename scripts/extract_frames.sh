#!/bin/bash
# 从动效视频/GIF 中提取关键帧 (v2 - 自适应帧率)
# 用法: bash extract_frames.sh <输入文件> [帧率覆盖]
# 依赖: ffmpeg (brew install ffmpeg)
#
# 自适应帧率策略:
#   视频 < 5s  → 15fps (快速过渡需要高时间分辨率)
#   视频 5~10s → 8fps  (中等平衡)
#   视频 > 10s → 4fps  (防止帧爆炸)
#   如传入第二参数，则手动覆盖

set -e

INPUT_FILE="$1"
MANUAL_FPS="$2"
PROJECT_ROOT="$(pwd)"
OUTPUT_DIR="$PROJECT_ROOT/motion-input/frames"

if [ -z "$INPUT_FILE" ]; then
    echo "用法: bash extract_frames.sh <输入文件> [帧率覆盖]"
    echo "  输入文件: .mp4、.webm 或 .gif 文件路径"
    echo "  帧率覆盖: 可选，手动指定每秒提取帧数"
    echo ""
    echo "  自适应帧率: <5s→15fps, 5~10s→8fps, >10s→4fps"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ 需要安装 ffmpeg，请运行: brew install ffmpeg"
    exit 1
fi

# 清理旧帧
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 获取视频时长
echo "📹 输入文件: $INPUT_FILE"
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$INPUT_FILE" 2>/dev/null || echo "0")
echo "⏱  时长: ${DURATION}s"

# ====== 自适应帧率计算 ======
if [ -n "$MANUAL_FPS" ]; then
    FPS="$MANUAL_FPS"
    echo "📐 帧率: ${FPS}fps (手动指定)"
else
    # 使用 awk 做浮点比较
    FPS=$(echo "$DURATION" | awk '{
        if ($1 < 5.0) print 15;
        else if ($1 < 10.0) print 8;
        else print 4;
    }')
    echo "📐 帧率: ${FPS}fps (自适应 — 基于 ${DURATION}s 时长)"
fi

echo "🎞  正在以 $FPS fps 提取关键帧..."
ffmpeg -i "$INPUT_FILE" -vf "fps=$FPS" "$OUTPUT_DIR/frame_%04d.png" -hide_banner -loglevel error

if [ $? -eq 0 ]; then
    echo "✅ 成功提取关键帧，输出目录: $OUTPUT_DIR"
    
    # Run OpenCV tracker
    echo "🔍 启动机器视觉追踪 (OpenCV Spatial Tracking)..."
    python3 "$(dirname "$0")/track_elements.py"
else
    echo "❌ 提取帧失败，请检查视频文件或 ffmpeg 是否正常安装。"
    exit 1
fi

FRAME_COUNT=$(ls -1 "$OUTPUT_DIR"/*.png 2>/dev/null | wc -l | tr -d ' ')
echo "✅ 成功提取 $FRAME_COUNT 帧，输出目录: $OUTPUT_DIR/"
echo ""
echo "帧文件列表:"
ls -1 "$OUTPUT_DIR"/*.png
