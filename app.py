import streamlit as st
import os
import pandas as pd # ファイル操作に必要
# ... (その他のインポート)

# LOCAL_CSV の定義や init_csv_header() は省略しません

def init_csv_header():
    """CSVファイルが存在しない場合にヘッダーを作成する関数（実際のヘッダーに合わせて修正してください）"""
    header_columns = ['Timestamp', 'Data1', 'Data2'] 
    empty_df = pd.DataFrame(columns=header_columns)
    # ファイルを上書きしてヘッダーのみを書き込む
    empty_df.to_csv(LOCAL_CSV, index=False)
    # st.info("✅ CSVヘッダーが初期化されました。") # コールバック内での表示は不要

# --- app.py の先頭に追加 ---

def clear_local_data_callback():
    """コールバック関数として、CSVファイルをクリアし、アプリをリロードする"""
    try:
        # ヘッダーを再作成する（=内容をクリアする）
        init_csv_header()
        st.session_state.clear_status = "success"
        
    except Exception as e:
        # ファイルI/Oのエラーを補足し、セッションに保存
        st.session_state.clear_status = f"error: {e}"
    
    # コールバック完了後、アプリをリロード
    st.rerun()

# --- 管理者モード UI のどこかに追加 ---

# 画面へのフィードバック表示
if 'clear_status' in st.session_state:
    if st.session_state.clear_status == "success":
        st.info("✅ データがクリアされ、新しいCSVファイルが作成されました。")
    elif st.session_state.clear_status.startswith("error"):
        st.error(f"❌ データのクリア中にエラーが発生しました: {st.session_state.clear_status.split(': ')[1]}")
    # フィードバックを表示したらステータスをリセット
    del st.session_state.clear_status

# if st.session_state.is_admin: のブロック内（管理者モード）
# 注: このブロック全体が正しくインデントされている必要があります。
if st.session_state.is_admin:
    
    # 💥 全データ消去ボタン
    # on_clickにコールバック関数を指定することで、ボタンが押された瞬間に処理を実行
    st.button(
        "🔴 全データ消去（リセット）",
        on_click=clear_local_data_callback,
        # キーを指定して、他のボタンとの衝突を防ぐ
        key="admin_clear_data_button"
    )
