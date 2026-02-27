@echo off
REM ================================================================================
REM C++ AI Assistant - Python依赖包下载脚本（Windows批处理版）
REM
REM 功能: 在Windows下下载Python包到ext目录，解决编码问题
REM 使用方法: 双击运行此脚本
REM ================================================================================

setlocal enabledelayedexpansion

echo ================================================================================
echo   C++ AI Assistant - Python依赖包下载
echo ================================================================================
echo.

REM 切换到脚本所在目录的上级目录
cd /d "%~dp0.."
set PROJECT_DIR=%CD%
echo 项目目录: %PROJECT_DIR%
echo.

REM 创建ext目录结构
echo [1/4] 创建目录...
mkdir ext\01-python-pip 2>nul
mkdir ext\02-python-wheels 2>nul
echo 完成.
echo.

REM 设置Python版本
set PYTHON_VERSION=3.11.9
echo [2/4] Python版本: %PYTHON_VERSION%
echo.

REM 检查pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到pip，请先安装Python
    pause
    exit /b 1
)
echo pip版本检查通过: 
pip --version
echo.

REM 下载wheel包
echo [3/4] 下载Python Wheel包...
cd ext\02-python-wheels
pip download -r ..\..\requirements-wheels-en.txt --platform win_amd64 --only-binary :all: --python-version %PYTHON_VERSION% --exists-action i
if errorlevel 1 (
    echo [WARNING] wheel部分失败，继续...
) else (
    echo [SUCCESS] wheel下载完成
)
cd %PROJECT_DIR%
echo.

REM 下载源码包
echo [4/4] 下载Python Source包...
cd ext\01-python-pip
pip download -r ..\..\requirements-pip-en.txt --no-binary :all: --exists-action i
if errorlevel 1 (
    echo [WARNING] source部分失败，继续...
) else (
    echo [SUCCESS] source下载完成
)
cd %PROJECT_DIR%
echo.

REM 统计下载结果
echo ================================================================================
echo   下载统计
echo ================================================================================
set /a WHL_COUNT=0
for %%f in (ext\02-python-wheels\*.whl) do set /a WHL_COUNT+=1
set /a TAR_COUNT=0
for %%f in (ext\01-python-pip\*.tar.gz) do set /a TAR_COUNT+=1
for %%f in (ext\01-python-pip\*.zip) do set /a TAR_COUNT+=1
echo Wheel包文件数: %WHL_COUNT%
echo 源码包文件数: %TAR_COUNT%
echo.

if %WHL_COUNT% EQU 0 if %TAR_COUNT% EQU 0 (
    echo [警告] 未下载到任何Python包
    echo 请手动运行以下命令:
    echo   cd ext\02-python-wheels ^&^& pip download -r ..\..\requirements-wheels.txt --platform win_amd64 --only-binary :all: --python-version %PYTHON_VERSION%
    echo   cd ext\01-python-pip ^&^& pip download -r ..\..\requirements-pip.txt --no-binary :all:
) else (
    echo [成功] Python依赖包下载完成
)
echo.

pause