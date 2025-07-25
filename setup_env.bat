@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo [STEP 1] OSとPythonバージョン確認
ver
python --version || (
    echo [ERROR] Pythonが見つかりません。PATHを確認してください。
    pause
    exit /b 1
)

:: 仮想環境の作成（未作成の場合）
if not exist "venv\Scripts\activate.bat" (
    echo [STEP 2] 仮想環境を作成中…
    python -m venv venv || (
        echo [ERROR] 仮想環境の作成に失敗しました。
        pause
        exit /b 1
    )
)

:: 仮想環境を有効化
call venv\Scripts\activate || (
    echo [ERROR] 仮想環境のアクティベートに失敗しました。
    pause
    exit /b 1
)

echo [STEP 3] pip, setuptools, wheel をアップグレード中…
python -m pip install --upgrade pip setuptools wheel >nul || (
    echo [ERROR] pip等のアップグレードに失敗しました。
    pause
    exit /b 1
)

:: 明示的に全パッケージをバージョン固定でインストール
echo [STEP 4] 必要ライブラリをインストール中…
pip install numpy==2.3.2 --prefer-binary || (
    echo [ERROR] NumPy のインストールに失敗しました。
    pause
    exit /b 1
)
pip install torch==2.7.1 --prefer-binary || (
    echo [ERROR] PyTorch のインストールに失敗しました。
    pause
    exit /b 1
)
pip install git+https://github.com/openai/whisper.git || (
    echo [ERROR] Whisper のインストールに失敗しました。
    pause
    exit /b 1
)
pip install openai==1.97.1 || (
    echo [ERROR] OpenAI のインストールに失敗しました。
    pause
    exit /b 1
)
pip install python-dotenv==1.1.1 || (
    echo [ERROR] dotenv のインストールに失敗しました。
    pause
    exit /b 1
)
pip install sounddevice==0.5.2 || (
    echo [ERROR] sounddevice のインストールに失敗しました。
    pause
    exit /b 1
)
pip install ffmpeg-python==0.2.0 || (
    echo [ERROR] ffmpeg-python のインストールに失敗しました。
    pause
    exit /b 1
)
pip install pyyaml || (
    echo [ERROR] PyYAML のインストールに失敗しました。
    pause
    exit /b 1
)

echo [STEP 5] Auto Memo v3 を起動します…
python auto_memo_v3.py

:: 仮想環境を終了
deactivate
endlocal
