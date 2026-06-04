@echo off
chcp 65001 >nul
title 抖音视频下载

echo.
echo ╔══════════════════════════════════╗
echo ║       抖音无水印视频下载         ║
echo ╚══════════════════════════════════╝
echo.

set /p url=📎 请粘贴抖音链接:
echo.

echo 🔍 正在解析并下载...
echo.

python "%~dp0douyin-dl.py" "%url%" "%~dp0downloads"

echo.
echo ════════════════════════════════════
echo   下载完成！文件在 downloads 目录
echo ════════════════════════════════════
echo.
pause
