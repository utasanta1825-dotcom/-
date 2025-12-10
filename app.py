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
        st.error(f"現在の実行パス: {os.getcwd()}")
        return []
    files = sorted([f for f in os.listdir(full_tone_dir_path) if f.lower().endswith(".wav")])
    if not files:
        st.error(f"ディレクトリ '{TONE_DIR}' 内に .wav ファイルが見つかりません。")
    return files

def init_csv_header():
    if not os.path.exists(LOCAL_CSV):
        header = [
            "Participant_ID", "Timestamp", "Tone_File", "Tone_Index",
            "Valence", "Arousal", "Diff",
            "Pitch_Ability", "Instrument_Experience"   # ★追加：新しい項目
        ]
        with open(LOCAL_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(header)

def append_row_local(row):
    try:
        with open(LOCAL_CSV, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
    except Exception as e:
        st.error(f"ローカルCSV保存エラー: {e}")

def load_audio_bytes(tone_path):
    try:
        full_path = os.path.abspath(tone_path)
        with open(full_path, 'rb') as f:
            return f.read()
    except Exception as e:
        st.error(f"ファイルの読み込みエラー: {full_path} - {e}")
        return None

# ---------- ページ設定 ----------
st.set_page_config(page_title="音律評価実験", layout="centered")

# ---------- 初期化 ----------
if "participant_id" not in st.session_state:
    st.session_state.participant_id = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

### ★追加：音感・楽器経験の保存領域
if "pitch_ability" not in st.session_state:
    st.session_state.pitch_ability = None
if "instrument_exp" not in st.session_state:
    st.session_state.instrument_exp = None

# ---------- 参加者ID / 管理者PIN ----------
if not st.session_state.participant_id and not st.session_state.is_admin:

    st.markdown("### 実験開始")
    pid = st.text_input("参加者ID を入力してください（管理者PINもこちら）", key="pid_input")

    if pid:
        if pid == ADMIN_PIN:
            st.session_state.is_admin = True
            st.success("管理者モードで起動します。")
            st.rerun()
        elif not re.match(r"^[A-Za-z0-9_]+$", pid):
            st.error("英数字と _ のみ使用できます。再入力してください。")
        else:
            st.session_state.participant_id = pid
            st.rerun()
    st.stop()

# ---------- ★追加：音感・楽器経験の質問 ----------
if st.session_state.pitch_ability is None or st.session_state.instrument_exp is None:

    st.markdown("### 事前アンケート")

    st.session_state.pitch_ability = st.radio(
        "音感はありますか？",
        ["絶対音感", "相対音感", "どちらもある", "ない", "わからない"]
    )

    st.session_state.instrument_exp = st.radio(
        "楽器経験はありますか？",
        ["ある", "ない"]
    )

    if st.button("次へ進む"):
        st.rerun()

    st.stop()

# ---------- 管理者モード ----------
if st.session_state.is_admin:
    st.warning("⚠️ 管理者モード：評価は記録されません。")
    if os.path.exists(LOCAL_CSV):
        with open(LOCAL_CSV, "rb") as f:
            st.download_button("⬇️ 全評価データ CSV", f, file_name=LOCAL_CSV)
        try:
            df = pd.read_csv(LOCAL_CSV)
            st.info(f"現在 **{len(df)} 件** 記録されています。")
        except:
            st.info("データなし")
    else:
        st.info("まだ評価データがありません。")
    if st.button("管理者モード終了"):
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

total = len(tone_files)
index = st.session_state.index

# ---------- 完了 ----------
if index >= total:
    st.success("🎉 全ての音の評価が完了しました！ありがとうございました！")
    st.stop()

# ---------- 現在の音 ----------
current_idx = st.session_state.order[index]
current_file = tone_files[current_idx]
tone_path_for_loading = os.path.join(TONE_DIR, current_file)

st.markdown(f"参加者ID: {participant_id} | {index+1} / {total}")
st.progress((index+1)/total)

audio_bytes = load_audio_bytes(tone_path_for_loading)

if audio_bytes:
    if st.button("▶ 音を再生"):
        st.audio(audio_bytes, format="audio/wav")

# ---------- 評価 ----------
valence = st.radio("快〜不快", [1,2,3,4,5], index=2, horizontal=True)
arousal = st.radio("落ち着く〜緊張", [1,2,3,4,5], index=2, horizontal=True)
diff = st.radio("自然〜違和感", [1,2,3,4,5], index=2, horizontal=True)

# ---------- 保存 ----------
if st.button("評価を記録して次へ"):
    timestamp = datetime.datetime.utcnow().isoformat()

    row = [
        participant_id, timestamp, current_file, current_idx,
        valence, arousal, diff,
        st.session_state.pitch_ability,        # ★追加
        st.session_state.instrument_exp        # ★追加
    ]

    append_row_local(row)

    st.session_state.index += 1
    st.rerun()

