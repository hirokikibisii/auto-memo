# auto_memo_v2_with_comments.py
# -------------------------------
# 音声録音 → 文字起こし（Whisper）→ 要約（GPT）をGUIで一括処理するアプリ
# メンテナンス性・視認性を高めるため、関数・クラスごとにコメントを整理
# GUIの改善：モダンで丸みを帯びたボタンスタイルに（Tkinterテーマ拡張推奨）

import os
import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import numpy as np
import wave
import datetime
import threading
import subprocess
import whisper
from openai import OpenAI
from dotenv import load_dotenv
import time
import logging

# ------------------------------
# 定数・ログ設定
# ------------------------------
AUDIO_DIR = 'output/audio'
TRANSCRIPT_DIR = 'output/transcript'
SUMMARY_DIR = 'output/summary'
CONFIG_FILE = '.env'
LOG_FILE = 'auto_memo.log'

# 必要な出力フォルダを作成
for d in [AUDIO_DIR, TRANSCRIPT_DIR, SUMMARY_DIR]:
    os.makedirs(d, exist_ok=True)

# ログ出力初期化
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# ------------------------------
# APIキーの読み込み・保存
# ------------------------------
def load_api_key():
    load_dotenv(CONFIG_FILE)
    return os.getenv('OPENAI_API_KEY', '')

def save_api_key(key):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(f'OPENAI_API_KEY={key.strip()}')

# ------------------------------
# 録音ファイル名の自動生成
# ------------------------------
def generate_unique_title():
    i = 1
    while True:
        name = f'meeting_{i:04d}'
        date = datetime.datetime.now().strftime('%Y%m%d')
        path = os.path.join(AUDIO_DIR, f"{date}_audio_{name}.wav")
        if not os.path.exists(path):
            return name
        i += 1

# ------------------------------
# 録音クラス
# ------------------------------
class Recorder:
    def __init__(self):
        self.fs = 44100  # サンプリングレート
        self.frames = []
        self.recording = False
        self.start_time = None

    def start(self):
        self.frames = []
        self.recording = True
        self.start_time = time.time()
        self.stream = sd.InputStream(callback=self.callback, samplerate=self.fs, channels=1)
        self.stream.start()

    def stop(self):
        self.recording = False
        self.stream.stop()
        self.stream.close()

    def callback(self, indata, frames, time_info, status):
        if self.recording:
            self.frames.append(indata.copy())

    def save_wav(self, filename):
        data = np.concatenate(self.frames)
        with wave.open(filename, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.fs)
            wf.writeframes((data * 32767).astype(np.int16).tobytes())

# ------------------------------
# mp3変換処理（ffmpeg使用）
# ------------------------------
def convert_to_mp3(wav_path):
    mp3_path = wav_path.replace('.wav', '.mp3')
    try:
        subprocess.run(['ffmpeg', '-y', '-i', wav_path, mp3_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(wav_path)
        return mp3_path
    except Exception as e:
        logging.error(f"MP3変換エラー: {e}")
        return None

# ------------------------------
# GPT API要約処理
# ------------------------------
def call_openai_summary(text, api_key, status_var):
    prompt = f"次の会話内容を要約してください：\n{text}"
    client = OpenAI(api_key=api_key)
    for model in ["gpt-4", "gpt-3.5-turbo"]:
        try:
            status_var.set(f"{model} で要約中...")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.warning(f"{model} 失敗: {e}")
            continue
    raise RuntimeError("全モデルで要約失敗")

# ------------------------------
# 書き起こし＋要約処理
# ------------------------------
def transcribe_and_summarize(mp3_path, api_key, title, status_var, duration_sec):
    try:
        status_var.set("Whisper 文字起こし中...")
        model = whisper.load_model("base")  # 多言語対応（日本語OK）
        result = model.transcribe(mp3_path)
        text = result.get('text', '')

        date = datetime.datetime.now().strftime('%Y%m%d')
        transcript_path = os.path.join(TRANSCRIPT_DIR, f"{date}_transcript_{title}.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(text or "書き起こし結果なし")

        if not text.strip():
            status_var.set("書き起こし失敗または空")
            return

        summary = call_openai_summary(text, api_key, status_var)
        summary_path = os.path.join(SUMMARY_DIR, f"{date}_summary_{title}.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        status_var.set("完了")
        messagebox.showinfo("完了", f"録音時間: {round(duration_sec,1)}秒\n処理が完了しました。")
        logging.info(f"完了: {title}（{round(duration_sec,1)}秒）")

    except Exception as e:
        status_var.set(f"エラー: {e}")
        logging.error(f"書き起こし/要約エラー: {e}")

# ------------------------------
# GUIアプリ本体
# ------------------------------
class AutoMemoApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Auto Memo")

        self.recorder = Recorder()
        self.api_key = load_api_key()

        tk.Label(master, text="OpenAI APIキー→").pack()
        self.api_entry = tk.Entry(master, width=60)
        self.api_entry.insert(0, self.api_key)
        self.api_entry.pack()

        tk.Label(master, text="議事録タイトル→").pack()
        self.title_entry = tk.Entry(master, width=60)
        self.title_entry.pack()

        self.button = tk.Button(master, text="🎙録音して議事録作成", command=self.toggle_recording)
        self.button.pack(pady=10)

        self.status_var = tk.StringVar()
        self.status_var.set("待機中")
        tk.Label(master, textvariable=self.status_var, fg="blue").pack()

        # モダン風ボタン（丸み・余白強調）
        button_opts = {'padx': 10, 'pady': 5, 'relief': 'groove', 'borderwidth': 2}
        tk.Button(master, text="🎧 音声フォルダ", command=lambda: os.startfile(AUDIO_DIR), **button_opts).pack(side=tk.LEFT, padx=5)
        tk.Button(master, text="📝 書き起こし", command=lambda: os.startfile(TRANSCRIPT_DIR), **button_opts).pack(side=tk.LEFT, padx=5)
        tk.Button(master, text="📄 要約フォルダ", command=lambda: os.startfile(SUMMARY_DIR), **button_opts).pack(side=tk.LEFT, padx=5)

        self.recording = False

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.recording = True
        self.button.config(text="■録音停止")
        threading.Thread(target=self.recorder.start).start()

    def stop_recording(self):
        self.recording = False
        self.button.config(text="🎙録音して議事録作成")
        self.recorder.stop()

        api_key = self.api_entry.get().strip()
        save_api_key(api_key)
        title = self.title_entry.get().strip() or generate_unique_title()
        date = datetime.datetime.now().strftime('%Y%m%d')
        wav_path = os.path.join(AUDIO_DIR, f"{date}_audio_{title}.wav")

        try:
            self.recorder.save_wav(wav_path)
            mp3_path = convert_to_mp3(wav_path)
            if not mp3_path:
                self.status_var.set("MP3変換失敗")
                return

            duration = time.time() - self.recorder.start_time
            threading.Thread(target=transcribe_and_summarize, args=(mp3_path, api_key, title, self.status_var, duration)).start()

        except Exception as e:
            self.status_var.set(f"保存エラー: {e}")
            logging.error(f"録音保存エラー: {e}")

# ------------------------------
# アプリ実行
# ------------------------------
if __name__ == '__main__':
    root = tk.Tk()
    app = AutoMemoApp(root)
    root.mainloop()
