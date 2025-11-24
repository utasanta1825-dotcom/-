import streamlit as st
import os
import pandas as pd
from datetime import datetime

# --- 1. 定数と初期設定 ---
LOCAL_CSV = "data/local_data.csv"
# CSVを保存するディレクトリが存在しない場合は作成
os.makedirs(os.path.dirname(LOCAL_CSV), exist_ok=True)


# --- 2. st.session_state の初期化 ---
# is_admin (管理者フラグ) と clear_status (クリア結果のフィードバック) を初期化
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False # 初期値は False
if 'clear_status' not in st.session_state:
    st.session_state.clear_status = None


# --- 3. データ操作関数 ---

def init_csv_header():
    """
    CSVファイルにヘッダーのみを上書きで作成し、データをクリアする。
    Streamlit Cloudの環境に対応するため、os.removeは使用しない。
    """
    # ★★★ 注意: 実際のアプリに合わせて列名を修正してください ★★★
    header_columns = ['Timestamp', 'Data1', 'Data2', 'User'] 
    
    empty_df = pd.DataFrame(columns=header_columns)
    # ファイルを上書きしてヘッダーのみを書き込む (データクリア)
    empty_df.to_csv(LOCAL_CSV, index=False)


def load_data():
    """CSVファイルからデータをロードする"""
    if not os.path.exists(LOCAL_CSV):
        init_csv_header()
    
    try:
        df = pd.read_csv(LOCAL_CSV)
        return df
    except pd.errors.EmptyDataError:
        # ファイルが空の場合（ヘッダーしかない場合も含む）
        return pd.DataFrame(columns=['Timestamp', 'Data1', 'Data2', 'User'])
    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {e}")
        return pd.DataFrame()


def clear_local_data_callback():
    """🔴 全データ消去ボタンが押されたときに実行されるコールバック関数"""
    try:
        # ヘッダーを再作成する (=内容をクリアする)
        init_csv_header()
        st.session_state.clear_status = "success"
        
    except Exception as e:
        # ファイルの書き込みエラーを捕捉
        st.session_state.clear_status = f"error: {e}"
    
    # コールバック完了後、アプリをリロードして画面を更新
    st.rerun()


# --- 4. メインUIとロジック ---

st.title("🛡️ 管理機能付きサンプルアプリ")
st.caption(f"データファイル: {LOCAL_CSV}")

# 仮のログインロジック (ここではボタンで管理者フラグを切り替え)
col1, col2 = st.columns(2)
with col1:
    if st.button("管理者としてログイン (仮)"):
        st.session_state.is_admin = True
        st.rerun()
with col2:
    if st.button("ログアウト (仮)"):
        st.session_state.is_admin = False
        st.rerun()

st.write(f"現在の権限ステータス: **{'管理者' if st.session_state.is_admin else '一般ユーザー'}**")

st.markdown("---")

## 📊 メインのデータ表示
st.header("データ内容")
df_data = load_data()
st.dataframe(df_data, use_container_width=True)


## 🛠️ 管理者モード UI
if st.session_state.is_admin:
    st.header("管理者パネル")

    # --- データクリアのフィードバック表示 ---
    # clear_local_data_callbackで設定されたステータスを表示
    if st.session_state.clear_status:
        if st.session_state.clear_status == "success":
            st.info("✅ データがクリアされ、新しいCSVファイルが作成されました。")
        elif st.session_state.clear_status.startswith("error"):
            st.error(f"❌ データのクリア中にエラーが発生しました: {st.session_state.clear_status.split(': ')[1]}")
        
        # フィードバックを表示したらステータスをリセット
        st.session_state.clear_status = None
        
    
    # 💥 全データ消去ボタン
    # on_clickにコールバック関数を指定することで、ボタンが押された瞬間に処理を実行
    st.button(
        "🔴 全データ消去（リセット）",
        on_click=clear_local_data_callback,
        help="データファイルの内容を完全に削除し、ヘッダーのみを再作成します。",
        key="admin_clear_data_button"
    )

st.markdown("---")
