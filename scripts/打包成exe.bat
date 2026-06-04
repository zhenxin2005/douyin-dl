@echo off
chcp 65001 >nul
title 打包 douyin-dl 为独立 EXE

echo.
echo 正在安装 PyInstaller...
pip install pyinstaller -q

echo.
echo 正在打包 douyin-dl.py...
pyinstaller --onefile --name "douyin-dl" --clean "%~dp0douyin-dl.py"

echo.
echo ✅ 打包完成！
echo    EXE 文件在: dist\douyin-dl.exe
echo.
echo 把这个 exe 复制到任意 Windows 电脑即可使用，无需安装 Python！
echo.
pause
