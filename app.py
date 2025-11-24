# --- app.py の先頭（インポートの下あたり）に追加 ---

def clear_local_data():
    """CSVファイルを削除し、ヘッダーのみを再作成する"""
    if os.path.exists(LOCAL_CSV):
        try:
            os.remove(LOCAL_CSV)
        except OSError as e:
            # Streamlit Cloudではos.removeが失敗することがあるため、エラーを抑制
            pass
    # ヘッダーを再作成
    init_csv_header()
    st.info("✅ データがクリアされ、新しいCSVファイルが作成されました。")

# --- 管理者モード UI のどこかに追加 ---
# (例: ログアウトボタンの前など)

# if st.session_state.is_admin: のブロック内に追加
if st.button("🔴 全データ消去（リセット）"):
    clear_local_data()
    st.rerun() # リセット後にアプリをリロード
