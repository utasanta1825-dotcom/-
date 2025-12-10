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
        header = ["Participant_ID", "Pitch_Sense", "Instrument_Exp",
                  "Timestamp", "Tone_File", "Tone_Index",
                  "Valence", "Arousal", "Diff"]
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

def upload_to_gsheet(row):
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
    except:
        st.error("Google Sheets バックアップには gspread と oauth2client が必要です。")
        return False

    creds_json_env = os.getenv("GOOGLE_CREDS_JSON", "")
    sheet_id = os.getenv("GSHEET_ID", "")

    if not creds_json_env or not sheet_id:
        st.error("Google Sheets の環境変数が不足しています。")
        return False

    creds = json.loads(creds_json_env)
    scope = ["https://spreadsheets.google.com/feeds",
              "https://www.googleapis.com/auth/drive"]
    client = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(creds, scope))
    sh = client.open_by_key(sheet_id)
    sh.sheet1.append_row(row)
    return True

# ---------- ページ設定 ----------
st.set_page_config(page_title="音律評価実験", layout="centered")

st.markdown("""
<style>
.main {background-color: #fafafa;}
.big-title {font-size: 28px; font-weight: bold; color:#333;}
.section {padding:10px; background:#ffffff; border-radius:10px; margin-top:20px; border:1px solid #ddd;}
.progress-text {font-size:16px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p class='big-title'>音律評価実験</p>", unsafe_allow_html=True)

# ---------- Session 初期化 ----------
if "participant_id" not in st.session_state:
    st.session_state.participant_id = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "pitch_sense" not in st.session_state:
    st.session_state.pitch_sense = None
if "instrument_exp" not in st.session_state:
    st.session_state.instrument_exp = None

# ---------- 参加者ID ----------
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

# ---------- 管理者モード ----------
if st.session_state.is_admin:
    st.markdown("---")
    st.warning("⚠️ 管理者モード：評価は記録されません。")
    st.markdown("### データダウンロード")

    if os.path.exists(LOCAL_CSV):
        with open(LOCAL_CSV, "rb") as f:
            st.download_button(
                "⬇️ 全評価データ CSV をダウンロード",
                f, file_name=LOCAL_CSV, mime="text/csv"
            )

        try:
            df = pd.read_csv(LOCAL_CSV)
            st.info(f"現在、**{len(df)} 件**の評価が記録されています。")
        except:
            st.info("まだ評価データがありません。")
    else:
        st.info("評価データがありません。")

    if st.button("管理者モードを終了"):
        st.session_state.clear()
        st.rerun()

    st.stop()

participant_id = st.session_state.participant_id

# ========= 事前アンケート（音感・楽器経験）追加部分 =========

if st.session_state.pitch_sense is None or st.session_state.instrument_exp is None:

    st.markdown("### 事前アンケート")

    st.session_state.pitch_sense = st.radio(
        "音感はありますか？",
        ["絶対音感", "相対音感", "どちらも", "ない", "わからない"],
        index=None,
        key="pitch_q"
    )

    st.session_state.instrument_exp = st.radio(
        "楽器経験はありますか？",
        ["ある", "ない"],
        index=None,
        key="inst_q"
    )

    if st.session_state.pitch_sense and st.session_state.instrument_exp:
        if st.button("次へ進む"):
            st.rerun()
    else:
        st.info("※ 両方の質問に回答すると次へ進めます。")

    st.stop()

# ==========================================================

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

current_idx = st.session_state.order[index]
current_file = tone_files[current_idx]
tone_path_for_loading = os.path.join(TONE_DIR, current_file)

st.markdown(
    f"<p class='progress-text'>参加者ID: {participant_id} | {index+1} / {total}</p>",
    unsafe_allow_html=True
)
st.progress((index+1)/total)

audio_bytes = load_audio_bytes(tone_path_for_loading)

if audio_bytes:
    if st.button("▶ 音を再生"):
        st.audio(audio_bytes, format="audio/wav")
else:
    st.error("音源ファイルの読み込みに失敗しました。")

st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 評価（1 = 低い / 5 = 高い）")

col1, col2, col3 = st.columns(3)
with col1:
    valence = st.radio("快（好き）〜不快（嫌い）", [1,2,3,4,5], index=2, horizontal=True)
with col2:
    arousal = st.radio("落ち着く〜緊張する", [1,2,3,4,5], index=2, horizontal=True)
with col3:
    diff = st.radio("自然〜違和感", [1,2,3,4,5], index=2, horizontal=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------- 保存処理 ----------
if st.button("評価を記録して次へ"):
    timestamp = datetime.datetime.utcnow().isoformat()

    row = [
        participant_id,
        st.session_state.pitch_sense,
        st.session_state.instrument_exp,
        timestamp,
        current_file,
        current_idx,
        valence,
        arousal,
        diff
    ]

    append_row_local(row)

    if USE_GSHEETS:
        try:
            upload_to_gsheet(row)
        except Exception as e:
            st.error(f"Google Sheets エラー: {e}")
            st.stop()

    st.session_state.index += 1
    st.rerun()
