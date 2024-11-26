@echo off
chcp 65001
echo =========================================
echo 正在安装必要的依赖...
echo =========================================

REM 安装 Microsoft Visual C++ Redistributable
echo 正在下载 Visual C++ Redistributable...
curl -L -o vc_redist.x64.exe https://aka.ms/vs/17/release/vc_redist.x64.exe
echo 正在安装 Visual C++ Redistributable...
vc_redist.x64.exe /quiet /norestart
del vc_redist.x64.exe

echo 正在安装 Python 依赖...
python -m pip install --upgrade pip
python -m pip install pyinstaller flask pywebview PyPDF2 pycryptodome pywin32 requests

echo.
echo =========================================
echo 正在打包应用...
echo =========================================

REM 确保在正确的目录
cd /d %~dp0

REM 检查图标文件是否存在
if not exist "icon.ico" (
    echo 警告：icon.ico 文件不存在，将使用默认图标
    set ICON_PARAM=
) else (
    set ICON_PARAM=--icon=icon.ico
)

REM 清理之前的构建
rmdir /s /q build dist
del /f /q *.spec

REM 运行打包命令
python -m PyInstaller ^
    --onefile ^
    --add-data "templates;templates" ^
    --hidden-import flask ^
    --hidden-import webview ^
    --hidden-import win32api ^
    --hidden-import win32con ^
    --exclude-module setuptools ^
    --exclude-module pkg_resources ^
    --exclude-module _bootlocale ^
    --noconsole ^
    %ICON_PARAM% ^
    --name "PDF空白页添加工具" ^
    run.py

echo.
echo =========================================
echo 打包完成！
echo =========================================
pause 