#!/bin/bash
# ============================================================
# 抖音视频下载脚本 (包装器)
# 用法: bash douyin-dl.sh <douyin_url> [output_dir]
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -lt 1 ]; then
    echo "❌ 用法: $0 <douyin_url> [output_dir]"
    exit 1
fi

python3 "$SCRIPT_DIR/douyin-dl.py" "$@"
