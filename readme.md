# 🎙️ Auto Memo v3

Whisper + GPT による **音声議事録アプリ**（GUI / CLI 両対応）  
録音 → 書き起こし → 要約 を自動化。**ローカル実行・API接続型**で、セキュアに使えます。

---

## 🚀 機能概要

- ✅ ボタン1つで録音 → 書き起こし → GPT要約
- ✅ `.env` と `config.yaml` による柔軟な設定管理
- ✅ GUI / CLI 両対応
- ✅ Whisperモデル選択（例：`base`, `tiny`）
- ✅ ChatGPT（gpt-4/gpt-3.5）で自動要約
- ✅ MP3変換で容量最適化（`ffmpeg.exe` 同梱）
- ✅ 出力ファイルは日付＋タイトル付きで保存

---

## 🔧 セットアップ手順（Windows）

1. Python 3.10 以上をインストール 
    https://www.python.org/
    
2. `setup_env.bat` をダブルクリックまたはターミナルで実行：
   ```bat
   setup_env.bat
   ```
   > 仮想環境作成とライブラリ一式の導入が完了します

---

## ▶️ 使い方

### GUI モード（録音ボタン付きアプリ）

```bash
python auto_memo_v3.py
```

### CLI モード（Enterで録音開始/停止）

```bash
python auto_memo_v3.py --cli
```

---

## 📁 出力先フォルダ構成

| 種別       | 保存パス                                | 内容             |
|----------|--------------------------------------|------------------|
| 音声       | `output/audio/yyyyMMdd_audio_*.mp3`     | 録音ファイル（変換後） |
| 書き起こし   | `output/transcript/yyyyMMdd_transcript_*.txt` | Whisper書き起こし |
| 要約       | `output/summary/yyyyMMdd_summary_*.txt`   | GPTによる要約文   |
| ログ       | `auto_memo.log`                        | 実行ログ         |

---

## 🔐 APIキーの設定

プロジェクトルートに `.env` を作成し、以下の形式で記述：

```
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## ⚙️ 設定ファイル（config.yaml）

```yaml
whisper_model: base

output_paths:
  audio: output/audio
  transcript: output/transcript
  summary: output/summary

log_file: auto_memo.log

gpt_model_priority:
  - gpt-4
  - gpt-3.5-turbo

ui:
  theme: light
```

---

## 🛠️ EXEファイル作成（Windows）

1. 以下を実行して PyInstaller でビルド：

   ```bat
   build_auto_memo.bat
   ```

2. `dist/auto_memo/` に `.exe` が生成されます。
3. ZIP圧縮されたビルド成果物も自動生成されます。

---

## 📦 開発環境（requirements.txt）

```
openai==1.97.1
torch==2.7.1
numpy==2.3.2
python-dotenv==1.1.1
sounddevice==0.5.2
ffmpeg-python==0.2.0
git+https://github.com/openai/whisper.git
```

---

## 🧑‍💻 ライセンス / 注意事項

- 本アプリは OpenAI API を利用します。商用利用時は契約内容をご確認ください。
- 音声データ・要約文の管理には十分ご注意ください。

---

## ✨ 今後のアップデート予定

- モダンUI（Tkinter → ttkbootstrap）への切替
- Whisperモデルのローカルカスタム対応
- チーム内共有モード（クラウド共有）
