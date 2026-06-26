#!/usr/bin/env python3
"""
定时录制抖音直播间脚本
规则: 录5分钟 → 停30分钟 → 录5分钟 → ... 直到下播
"""
import os
import sys
import time
import subprocess
import json
from datetime import datetime

ROOM_URL = "https://live.douyin.com/452466948652"
RECORDER_DIR = "C:\\Users\\zhenx\\douyin-recorder"
OUTPUT_DIR = "C:\\Users\\zhenx\\douyin-dl\\downloads\\直播间录制"
PROFILE = "tiny"  # 最小格式: 540p H.265
RECORD_SECONDS = 300  # 每次录5分钟
WAIT_MINUTES = 30  # 停30分钟

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONPATH"] = RECORDER_DIR

def log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] {msg}", flush=True)

def is_live():
    """检查直播间是否还在播"""
    try:
        result = subprocess.run(
            ["python", "-m", "douyin_recorder", "info", ROOM_URL],
            cwd=RECORDER_DIR, capture_output=True, text=False, timeout=30,
            env={**os.environ, "PYTHONPATH": RECORDER_DIR}
        )
        output = result.stdout.decode("utf-8", errors="replace")
        output += result.stderr.decode("utf-8", errors="replace")
        return "直播中" in output
    except Exception as e:
        print(f"  is_live检查出错: {e}", flush=True)
        return False

def record_once(round_num):
    """录制一次，返回是否正常完成（未被中断）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = f"DOUYIN_452466948652_{timestamp}_第{round_num}轮"
    
    log(f"🎬 第{round_num}轮录制开始 (5分钟, {PROFILE}模式)")
    log(f"   输出: {OUTPUT_DIR}\\{output_name}.ts")
    
    result = subprocess.run(
        ["python", "-m", "douyin_recorder", "record", ROOM_URL,
         "--profile", PROFILE,
         "--duration", str(RECORD_SECONDS),
         "-o", OUTPUT_DIR],
        cwd=RECORDER_DIR, capture_output=True, text=True, timeout=600,
        env={**os.environ, "PYTHONPATH": RECORDER_DIR}
    )
    
    # 检查录制是否成功
    if "录制完成" in result.stdout or "录制中" in result.stdout:
        log(f"✅ 第{round_num}轮录制完成")
        return True
    else:
        log(f"⚠️ 第{round_num}轮可能异常: {result.stderr[-200:] if result.stderr else '无错误'}")
        return False

def main():
    log("=" * 50)
    log("📡 直播间定时录制启动")
    log(f"   房间: {ROOM_URL}")
    log(f"   模式: {PROFILE} (540p H.265)")
    log(f"   规则: 录5分钟 → 停30分钟 → 录5分钟 → ...")
    log(f"   目录: {OUTPUT_DIR}")
    log("=" * 50)
    
    if not is_live():
        log("❌ 直播间当前未开播，等待开播中...")
        while not is_live():
            time.sleep(60)
        log("✅ 直播间已开播！")
    
    round_num = 0
    while True:
        if not is_live():
            log("📴 直播间已下播，结束录制")
            break
        
        round_num += 1
        record_once(round_num)
        
        # 检查是否还在播
        if not is_live():
            log("📴 录制过程中下播了，结束")
            break
        
        # 等待30分钟
        log(f"⏳ 等待{WAIT_MINUTES}分钟后再录下一轮...")
        for i in range(WAIT_MINUTES):
            time.sleep(60)
            # 每5分钟检查一下是否还在播
            if (i + 1) % 5 == 0 and not is_live():
                log("📴 等待过程中下播了，结束")
                return
        
        # 检查下播状态
        if not is_live():
            log("📴 等待30分钟后已下播，结束")
            break
    
    log(f"\n📊 录制结束，共完成 {round_num} 轮录制")
    log(f"📁 文件保存在: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
