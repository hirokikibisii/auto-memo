@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo [STEP 1] 仮想環境の有効化…
call venv\Scripts\activate || (
    echo [ERROR] 仮想環境のアクティベートに失敗しました。
    pause
    exit /b 1
)

echo [STEP 2] PyInstaller 依存チェック…
pip show pyinstaller >nul 2>&1 || (
    echo [INFO] PyInstaller をインストールします…
    pip install pyinstaller || (
        echo [ERROR] PyInstaller のインストールに失敗しました。
        pause
        exit /b 1
    )
)

echo [STEP 3] EXE をビルドします…
pyinstaller auto_memo.spec || (
    echo [ERROR] PyInstaller ビルドに失敗しました。
    pause
    exit /b 1
)

echo [STEP 4] ビルド成果物を zip にまとめます…
set DATETIME=%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%_%TIME:~0,2%%TIME:~3,2%
set DATETIME=%DATETIME: =0%
set ZIPNAME=auto_memo_build_%DATETIME%.zip

powershell -Command "Compress-Archive -Path dist\auto_memo\* -DestinationPath %ZIPNAME%" || (
    echo [ERROR] ZIP作成に失敗しました。
    pause
    exit /b 1
)

echo [✅ 完了] dist\auto_memo に exe が生成され、%ZIPNAME% に圧縮されました。
pause
endlocal
