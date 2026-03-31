#!/bin/bash

# This script extracts frames from video files for motion analysis using FFmpeg and OpenCV.

# Check if the video file is provided as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <video_file>"
    exit 1
fi

VIDEO_FILE="$1"

# Create a directory to store extracted frames
FRAME_DIR="frames"
mkdir -p "$FRAME_DIR"

# Extract frames from the video using FFmpeg
ffmpeg -i "$VIDEO_FILE" -vf "fps=1" "$FRAME_DIR/frame_%04d.png"

echo "Frames extracted to $FRAME_DIR"