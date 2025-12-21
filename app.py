import streamlit as st
import random
import os
import csv
from io import BytesIO
import datetime
import json
import re
import wave
import pandas as pd

# --- 設定 ---
TONE_DIR = "24edo_single_tones"
LOCAL_CSV = "evaluation_results.csv"
ADMIN_PIN = "0000"

USE_GSHEETS = os.getenv("USE_GSHEETS", "false").lower() == "true"

# ---------- ユーティリティ ----------
def load_tone_files():
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_tone_dir_path = os.path.join(base_path, TONE_DIR)

    if not os.path.exists(full_tone_dir_path):
        st.error(f"音源ディレクトリ '{TONE_DIR}' が見つかりません。")
        return []

    files = sorted([f for f in os.listdir(full_tone_dir_path) if f.lower().endswith(".wav")])
    if not files:
        st.error("wavファイルが見つかりません。")
    return files

def init_csv_header():
    if not os.path.exists(LOCAL_CSV):
        header = [
            "Participant_ID",
            "Timestamp",
            "Tone_File",
            "Tone_Index",
            "Valence",
            "Arousal",
            "Diff",
            "Play_Count"   # ★①追加
        ]
        with open(LOCAL_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(header)

def append_row_local(row):
    with open(LOCAL_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

def load_audio_bytes(tone_path):
    try:
        with open(os.path.abspath(tone_path), "rb") as f:
            return f.read()
    except:
        return None

# ---------- ページ設定 ----------
st.set_page_config(page_title="音律評価実験", layout="centered")

st.markdown("""
<style>
.big-title {font-size: 28px; font-weight: bold;}
.section {padding:10px; background:#fff; border-radius:10px; margin-top:20px;}
.progress-text {font-size:16px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p class='big-title'>音律評価実験</p>", unsafe_allow_html=True)

# ---------- セッション初期化 ----------
if "participant_id" not in st.session_state:
    st.session_state.participant_id = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ★①追加：再生管理
if "played" not in st.session_state:
    st.session_state.played = False
if "play_count" not in st.session_state:
    st.session_state.play_count = 0

# ---------- 参加者ID入力 ----------
if not st.session_state.participant_id and not st.session_state.is_admin:
    pid = st.text_input("参加者ID（管理者PINもこちら）")
    if pid:
        if pid == ADMIN_PIN:
            st.session_state.is_admin = True
            st.rerun()
        elif re.match(r"^[A-Za-z0-9_]+$", pid):
            st.session_state.participant_id = pid
            st.rerun()
        else:
            st.error("英数字と _ のみ使用できます。")
    st.stop()

# ---------- 管理者モード ----------
if st.session_state.is_admin:
    st.warning("管理者モード（評価は記録されません）")
    if os.path.exists(LOCAL_CSV):
        with open(LOCAL_CSV, "rb") as f:
            st.download_button("CSVダウンロード", f, file_name=LOCAL_CSV)
        df = pd.read_csv(LOCAL_CSV)
        st.info(f"記録件数：{len(df)}")
    if st.button("終了"):
        st.session_state.clear()
        st.rerun()
    st.stop()

participant_id = st.session_state.participant_id

# ---------- 音源ロード ----------
tone_files = load_tone_files()
if not tone_files:
    st.stop()

# ---------- ランダム順 ----------
if "order" not in st.session_state:
    st.session_state.order = random.sample(range(len(tone_files)), len(tone_files))
    st.session_state.index = 0
    init_csv_header()

index = st.session_state.index
total = len(tone_files)

# ---------- 完了 ----------
if index >= total:
    st.success("🎉 全て完了しました。ありがとうございました！")
    st.stop()

current_idx = st.session_state.order[index]
current_file = tone_files[current_idx]
tone_path = os.path.join(TONE_DIR, current_file)

st.markdown(
    f"<p class='progress-text'>ID: {participant_id} | {index+1}/{total}</p>",
    unsafe_allow_html=True
)
st.progress((index+1)/total)

# ---------- 再生 ----------
audio_bytes = load_audio_bytes(tone_path)

if audio_bytes:
    # --- 再生ボタン（状態管理用） ---
if st.button("▶ 再生を有効化"):
    st.session_state.played = True
    st.session_state.play_count += 1

# --- audioプレイヤーは常に表示 ---
st.audio(audio_bytes, format="audio/wav")

st.caption(f"再生回数：{st.session_state.play_count}")

    st.caption(f"再生回数：{st.session_state.play_count}")
else:
    st.error("音源の読み込みに失敗しました。")

# ---------- 評価 ----------
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 評価（1 = 低い / 5 = 高い）")

col1, col2, col3 = st.columns(3)
with col1:
    valence = st.radio("快〜不快", [1,2,3,4,5], index=2, horizontal=True)
with col2:
    arousal = st.radio("落ち着く〜緊張", [1,2,3,4,5], index=2, horizontal=True)
with col3:
    diff = st.radio("自然〜違和感", [1,2,3,4,5], index=2, horizontal=True)

st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.played:
    st.warning("⚠️ 音を再生してから評価してください。")

# ---------- 保存 ----------
if st.button(
    "評価を記録して次へ",
    disabled=not st.session_state.played
):
    timestamp = datetime.datetime.utcnow().isoformat()
    row = [
        participant_id,
        timestamp,
        current_file,
        current_idx,
        valence,
        arousal,
        diff,
        st.session_state.play_count
    ]

    append_row_local(row)

    # ★①リセット
    st.session_state.index += 1
    st.session_state.played = False
    st.session_state.play_count = 0
    st.rerun()
