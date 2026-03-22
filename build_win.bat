@echo off
chcp 65001 >nul
echo =========================================
echo   开始构建 3D 音乐空间 Windows 桌面应用
echo =========================================

echo.
echo [1/3] 正在编译 Vue 前端代码...
cd frontend
call pnpm install
call npm run build:prod
cd ..

echo.
echo [2/3] 正在将前端产物同步至后端目录...
:: 如果后端存在旧的 dist 文件夹，先删除它
if exist backend\dist rmdir /s /q backend\dist
:: 将前端打包出的 dist 文件夹整个复制到 backend 目录下
xcopy /E /I /Y frontend\dist backend\dist

echo.
echo [3/3] 正在使用 PyInstaller 打包可执行文件...
cd backend
:: 确保安装了依赖
call pip install pywebview pyinstaller

:: 执行 PyInstaller 打包
:: --noconsole 隐藏黑色命令行窗口
:: --onefile 打包成单文件 exe
:: --add-data "dist;dist" 将前端的 dist 文件夹内嵌到 exe 中
:: --icon=../icon.ico 如果你有图标，可以加上这个参数
call pyinstaller --noconsole --onefile --add-data "dist;dist" desktop.py

echo.
echo =========================================
echo   构建完成！
echo   请前往 backend\dist 目录下查找 desktop.exe
echo =========================================
pause