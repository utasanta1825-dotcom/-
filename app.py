import streamlit as st
import random
import os
import csv
import soundfile as sf
from io import BytesIO
import datetime
import json
import re

# ---------- 設定 ----------
TONE_DIR = "24edo_single_tones"
LOCAL_CSV = "evaluation_results.csv"

USE_GSHEETS = os.getenv("USE_GSHEETS", "false").lower() == "true"

# ---------- ユーティリティ ----------
def load_tone_files():
    if not os.path.exists(TONE_DIR):
        return []
    return sorted([f for f in os.listdir(TONE_DIR) if f.lower().endswith(".wav")])

def init_csv_header():
    if not os.path.exists(LOCAL_CSV):
        header = ["Participant_ID", "Timestamp", "Tone_File", "Tone_Index",
                  "Valence", "Arousal", "Diff"]
        with open(LOCAL_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(header)

def append_row_local(row):
    with open(LOCAL_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)

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

# ---------- カスタム CSS ----------
st.markdown("""
<style>
.main {background-color: #fafafa;}
.big-title {font-size: 28px; font-weight: bold; color:#333;}
.section {padding:10px; background:#ffffff; border-radius:10px; margin-top:20px; border:1px solid #ddd;}
.progress-text {font-size:16px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p class='big-title'>音律評価実験</p>", unsafe_allow_html=True)

# ---------- 参加者 ID 入力 ----------
if "participant_id" not in st.session_state:
    st.session_state.participant_id = ""

if not st.session_state.participant_id:
    pid = st.text_input("参加者ID を入力してください（英数字のみ）")

    if pid:
        if not re.match(r"^[A-Za-z0-9_]+$", pid):
            st.error("英数字と _ のみ使用できます。再入力してください。")
        else:
            st.session_state.participant_id = pid
            st.rerun()
    st.stop()

participant_id = st.session_state.participant_id

# ---------- 音源ロード ----------
tone_files = load_tone_files()
if not tone_files:
    st.error(f"音源フォルダ **{TONE_DIR}** に .wav がありません。")
    st.stop()

# ---------- ランダム順初期化 ----------
if "order" not in st.session_state:
    st.session_state.order = random.sample(range(len(tone_files)), len(tone_files))
    st.session_state.index = 0
    init_csv_header()

total = len(tone_files)
index = st.session_state.index

# ---------- 完了画面 ----------
if index >= total:
    st.success("🎉 全ての音の評価が完了しました！ありがとうございました！")
    if os.path.exists(LOCAL_CSV):
        with open(LOCAL_CSV, "rb") as f:
            st.download_button("CSV をダウンロード", f, file_name=LOCAL_CSV, mime="text/csv")
    st.stop()

# ---------- 現在の音 ----------
current_idx = st.session_state.order[index]
current_file = tone_files[current_idx]
tone_path = os.path.join(TONE_DIR, current_file)

st.markdown(f"<p class='progress-text'>参加者ID: {participant_id} | {index+1} / {total}</p>", unsafe_allow_html=True)
st.progress((index+1)/total)

# ---------- 音の再生 ----------
try:
    data, sr = sf.read(tone_path)
    bio = BytesIO()
    sf.write(bio, data, sr, format="WAV")
    bio.seek(0)

    if st.button("▶ 音を再生"):
        st.audio(bio.read(), format="audio/wav")
        bio.seek(0)

except Exception as e:
    st.error(f"音声読み込みエラー: {e}")

# ---------- 評価フォーム ----------
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
    row = [participant_id, timestamp, current_file, current_idx, valence, arousal, diff]

    try:
        append_row_local(row)
        if USE_GSHEETS:
            upload_to_gsheet(row)
    except Exception as e:
        st.error(f"保存エラー: {e}")
        st.stop()

    st.session_state.index += 1
    st.rerun()

# ---------- CSV ダウンロード ----------
if os.path.exists(LOCAL_CSV):
    with open(LOCAL_CSV, "rb") as f:
        st.download_button("CSV をダウンロード", f, file_name=LOCAL_CSV, mime="text/csv")
