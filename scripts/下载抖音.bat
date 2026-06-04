@echo off
chcp 65001 >nul
title 抖音视频下载

echo.
echo ╔══════════════════════════════════╗
echo ║       抖音无水印视频下载         ║
echo ╚══════════════════════════════════╝
echo.
echo  [1] 下载单个视频
echo  [2] 批量下载（从 urls.txt 文件）
echo  [3] 批量下载（粘贴多个链接）
echo.
set /p mode=请选择 (1/2/3):

if "%mode%"=="1" goto single
if "%mode%"=="2" goto batch_file
if "%mode%"=="3" goto batch_paste
goto end

:single
echo.
set /p url=📎 粘贴抖音链接:
python "%~dp0douyin-dl.py" "%url%" "%~dp0downloads"
goto end

:batch_file
echo.
echo 📄 请确认 urls.txt 文件已放在当前目录
echo    每行一个链接，# 开头为注释
echo.
pause
python "%~dp0douyin-dl.py" "%~dp0urls.txt" "%~dp0downloads"
goto end

:batch_paste
echo.
echo 📝 请粘贴多个链接（每行一个），粘贴完毕后按 Ctrl+Z 再回车:
echo.
setlocal enabledelayedexpansion
set TEMP_FILE=%~dp0_temp_urls.txt
if exist "%TEMP_FILE%" del "%TEMP_FILE%"
:read
set /p line=
if "!line!"=="" goto done
echo !line!>> "%TEMP_FILE%"
goto read
:done
python "%~dp0douyin-dl.py" "%TEMP_FILE%" "%~dp0downloads"
del "%TEMP_FILE%" 2>nul

:end
echo.
echo ════════════════════════════════════
echo   下载完成！文件在 downloads 目录
echo ════════════════════════════════════
echo.
pause
