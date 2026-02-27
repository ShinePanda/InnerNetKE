@echo off
REM ================================================================================
REM C++ AI Assistant - 打包离线部署包
REM ================================================================================

echo.
echo ========================================================================
echo   C++ AI Assistant - 打包离线部署包
echo ========================================================================
echo.

REM 设置变量
set PROJECT_DIR=%~dp0..
set OUTPUT_DIR=%PROJECT_DIR%
set PACKAGE_NAME=cpp-ai-assistant-offline.zip
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
set PACKAGE_WITH_TIME=cpp-ai-assistant-offline-%TIMESTAMP%.zip

echo 目标目录: %PROJECT_DIR%
echo 输出文件: %OUTPUT_DIR%\%PACKAGE_NAME%
echo.

REM 检查7-Zip
where 7z >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 使用7-Zip压缩...
    7z a -tzip "%OUTPUT_DIR%\%PACKAGE_NAME%" "%PROJECT_DIR%\*" ^
        -xr!*.tmp -xr!*.log -xr!__pycache__ -xr!.git -xr!node_modules ^
        -xr!venv -xr!.pytest_cache -xr!.idea -xr!.vscode
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [SUCCESS] 打包完成: %PACKAGE_NAME%
        echo.
        echo 文件大小:
        dir "%OUTPUT_DIR%\%PACKAGE_NAME%" | find "%PACKAGE_NAME%"
        echo.
        echo 下一步: 传输 %PACKAGE_NAME% 到内网服务器
    ) else (
        echo [ERROR] 打包失败
        exit /b 1
    )
) else (
    echo 7-Zip未找到，使用PowerShell压缩...
    powershell -Command "Compress-Archive -Path '%PROJECT_DIR%\*' -DestinationPath '%OUTPUT_DIR%\%PACKAGE_NAME%' -Force -CompressionLevel Optimal"
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [SUCCESS] 打包完成: %PACKAGE_NAME%
        echo.
        echo 文件大小:
        dir "%OUTPUT_DIR%\%PACKAGE_NAME%" | find "%PACKAGE_NAME%"
        echo.
        echo 下一步: 传输 %PACKAGE_NAME% 到内网服务器
    ) else (
        echo [ERROR] 打包失败
        exit /b 1
    )
)

echo.
echo ========================================================================
echo   打包完成！
echo ========================================================================
echo.
echo 输出文件: %PACKAGE_NAME%
echo.
echo 在内网服务器上的部署步骤:
echo 1. 解压到目标目录
echo 2. 运行 python install.py
echo 3. 配置 .env 文件
echo 4. 启动服务
echo.
pause