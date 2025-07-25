# auto_memo_v3.py
# ------------------------------
# GUI/CLI両対応の音声議事録アプリ（Whisper + GPT 要約）
# ・設定は config.yaml/.env に分離
# ・ログ出力、Whisperモデル選択対応

import os
import sys
import argparse
import threading
import datetime
import wave
import time
import subprocess
import logging
import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import numpy as np
import whisper
import yaml
from openai import OpenAI
from dotenv import load_dotenv

# ------------------------------
# 初期設定（設定ファイル読み込み）
# ------------------------------
load_dotenv()
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

AUDIO_DIR = config.get("audio_dir", "output/audio")
TRANSCRIPT_DIR = config.get("transcript_dir", "output/transcript")
SUMMARY_DIR = config.get("summary_dir", "output/summary")
WHISPER_MODEL = config.get("whisper_model", "base")
LOG_FILE = config.get("log_file", "auto_memo.log")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(SUMMARY_DIR, exist_ok=True)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# ------------------------------
# ユーティリティ
# ------------------------------
def load_api_key():
    return os.getenv("OPENAI_API_KEY", "")

def save_api_key(key):
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"OPENAI_API_KEY={key.strip()}")

def generate_unique_title():
    i = 1
    while True:
        name = f'meeting_{i:04d}'
        date = datetime.datetime.now().strftime('%Y%m%d')
        path = os.path.join(AUDIO_DIR, f"{date}_audio_{name}.wav")
        if not os.path.exists(path):
            return name
        i += 1

def convert_to_mp3(wav_path):
    mp3_path = wav_path.replace('.wav', '.mp3')
    try:
        subprocess.run(['ffmpeg', '-y', '-i', wav_path, mp3_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(wav_path)
        return mp3_path
    except Exception as e:
        logging.error(f"MP3変換エラー: {e}")
        return None

def call_openai_summary(text, api_key):
    prompt = f"次の会話内容を要約してください：\n{text}"
    client = OpenAI(api_key=api_key)
    for model in ["gpt-4", "gpt-3.5-turbo"]:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.warning(f"{model}失敗: {e}")
    raise RuntimeError("全モデルで要約失敗")

# ------------------------------
# 録音処理
# ------------------------------
class Recorder:
    def __init__(self):
        self.fs = 44100
        self.frames = []
        self.start_time = None

    def record(self):
        self.frames = []
        self.start_time = time.time()
        with sd.InputStream(callback=self.callback, samplerate=self.fs, channels=1):
            input("[ENTER] で録音停止 > ")

    def callback(self, indata, frames, time_info, status):
        self.frames.append(indata.copy())

    def save(self, filename):
        data = np.concatenate(self.frames)
        with wave.open(filename, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.fs)
            wf.writeframes((data * 32767).astype(np.int16).tobytes())
        return time.time() - self.start_time

# ------------------------------
# 書き起こし＋要約
# ------------------------------
def transcribe_and_summarize(mp3_path, api_key, title):
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(mp3_path)
    text = result.get("text", "")

    date = datetime.datetime.now().strftime('%Y%m%d')
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{date}_transcript_{title}.txt")
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(text)

    if not text.strip():
        print("書き起こし失敗または空")
        return

    summary = call_openai_summary(text, api_key)
    summary_path = os.path.join(SUMMARY_DIR, f"{date}_summary_{title}.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print("\u2705 要約完了")

def transcribe_and_summarize_gui(mp3_path, api_key, title, duration, status_var):
    try:
        model = whisper.load_model(WHISPER_MODEL)
        result = model.transcribe(mp3_path)
        text = result.get("text", "")

        date = datetime.datetime.now().strftime('%Y%m%d')
        transcript_path = os.path.join(TRANSCRIPT_DIR, f"{date}_transcript_{title}.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(text)

        if not text.strip():
            status_var.set("書き起こし失敗または空")
            return

        summary = call_openai_summary(text, api_key)
        summary_path = os.path.join(SUMMARY_DIR, f"{date}_summary_{title}.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        msg = f"完了 \U0001f389\n録音時間: {round(duration,1)} 秒"
        status_var.set(msg)
        messagebox.showinfo("完了", msg)
        logging.info(f"完了: {title}（{round(duration,1)}秒）")

    except Exception as e:
        status_var.set(f"エラー: {e}")
        logging.error(f"書き起こし/要約エラー: {e}")

# ------------------------------
# CLIモード実行
# ------------------------------
def run_cli():
    print("\U0001f399録音開始（Enterで停止）")
    title = generate_unique_title()
    date = datetime.datetime.now().strftime('%Y%m%d')
    wav_path = os.path.join(AUDIO_DIR, f"{date}_audio_{title}.wav")

    recorder = Recorder()
    recorder.record()
    duration = recorder.save(wav_path)

    mp3_path = convert_to_mp3(wav_path)
    if not mp3_path:
        print("\u274c MP3変換失敗")
        return

    transcribe_and_summarize(mp3_path, load_api_key(), title)
    print(f"\U0001f552 録音時間: {round(duration,1)} 秒")

# ------------------------------
# GUIアプリ
# ------------------------------
class AutoMemoApp:
    def __init__(self, master):
        self.master = master
        self.recorder = Recorder()
        self.api_key = load_api_key()
        self.recording = False

        tk.Label(master, text="OpenAI APIキー→").pack()
        self.api_entry = tk.Entry(master, width=60)
        self.api_entry.insert(0, self.api_key)
        self.api_entry.pack()

        tk.Label(master, text="議事録タイトル→").pack()
        self.title_entry = tk.Entry(master, width=60)
        self.title_entry.pack()

        self.button = tk.Button(master, text="\U0001f399録音して議事録作成", command=self.toggle_recording)
        self.button.pack(pady=10)

        self.status_var = tk.StringVar()
        self.status_var.set("待機中")
        tk.Label(master, textvariable=self.status_var, fg="blue").pack()

        button_opts = {'padx': 10, 'pady': 5, 'relief': 'groove', 'borderwidth': 2}
        btn_frame = tk.Frame(master)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="\U0001f3a7 音声フォルダ", command=lambda: os.startfile(AUDIO_DIR), **button_opts).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="\U0001f4dd 書き起こし", command=lambda: os.startfile(TRANSCRIPT_DIR), **button_opts).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="\U0001f4c4 要約フォルダ", command=lambda: os.startfile(SUMMARY_DIR), **button_opts).pack(side=tk.LEFT, padx=5)

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.recording = True
        self.button.config(text="■録音停止")
        threading.Thread(target=self.recorder.record).start()

    def stop_recording(self):
        self.recording = False
        self.button.config(text="\U0001f399録音して議事録作成")

        api_key = self.api_entry.get().strip()
        save_api_key(api_key)
        title = self.title_entry.get().strip() or generate_unique_title()
        date = datetime.datetime.now().strftime('%Y%m%d')
        wav_path = os.path.join(AUDIO_DIR, f"{date}_audio_{title}.wav")

        try:
            duration = self.recorder.save(wav_path)
            mp3_path = convert_to_mp3(wav_path)
            if not mp3_path:
                self.status_var.set("MP3変換失敗")
                return
            self.status_var.set(f"処理中... ({round(duration,1)}秒)")
            threading.Thread(target=transcribe_and_summarize_gui, args=(mp3_path, api_key, title, duration, self.status_var)).start()
        except Exception as e:
            self.status_var.set(f"エラー: {e}")

# ------------------------------
# 起動エントリーポイント
# ------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", action="store_true", help="CLIモードで起動")
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        root = tk.Tk()
        root.title("Auto Memo v3")
        app = AutoMemoApp(root)
        root.mainloop()
