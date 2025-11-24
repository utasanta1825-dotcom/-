# --- app.py の先頭（インポートの下あたり）に追加 ---

import os
import pandas as pd # pandasを使ってファイルを空にする処理を追加

# LOCAL_CSV 変数が定義されていることを前提とします。
# 例: LOCAL_CSV = "data/local_data.csv"

def init_csv_header():
    """CSVファイルが存在しない場合にヘッダーを作成する関数（既存の関数を流用）"""
    # 実際には、この関数内でpd.DataFrame.to_csv()などを使って
    # ヘッダー行をファイルに書き込んでいるはずです。
    
    # 例:
    # header_df = pd.DataFrame(columns=['Timestamp', 'Data1', 'Data2'])
    # header_df.to_csv(LOCAL_CSV, index=False)
    
    # 既存の init_csv_header() の実装をそのまま使用してください。
    pass # 既存の init_csv_header() の中身に置き換える

def clear_local_data():
    """
    CSVファイルを空にし、ヘッダーのみを再作成する。
    Streamlit Cloudでのos.remove()失敗を回避するため、上書きで内容をクリアする。
    """
    try:
        # ヘッダーを再作成する（=内容をクリアする）
        # init_csv_header()が、LOCAL_CSVが存在するかどうかにかかわらず、
        # ヘッダーのみを書き込むように設計されていることが理想です。
        # もし init_csv_header() がファイル存在時を考慮しない場合は、
        # ここでヘッダーのみを強制的に上書きする処理を追加します。
        
        # 例：pandasを使用してヘッダーのみを上書きする
        header_columns = ['Timestamp', 'Data1', 'Data2'] # 実際のヘッダーに合わせてください
        empty_df = pd.DataFrame(columns=header_columns)
        empty_df.to_csv(LOCAL_CSV, index=False)
        
        # もしくは既存の init_csv_header() が上書き機能を持つなら
        # init_csv_header() を呼び出すだけでも可
        # init_csv_header()

        st.info("✅ データがクリアされ、新しいCSVファイル（ヘッダーのみ）が作成されました。")

    except Exception as e:
        # ファイルの書き込み自体に問題がある場合は、ユーザーにエラーを通知
        st.error(f"❌ データのクリア中にエラーが発生しました: {e}")
        # 詳細なデバッグ情報（Streamlit Cloud環境では特に重要）
        st.caption("ファイル操作権限に問題がある可能性があります。")

# --- 管理者モード UI のどこかに追加 ---
# (例: ログアウトボタンの前など)

# if st.session_state.is_admin: のブロック内に追加
if st.button("🔴 全データ消去（リセット）"):
    # 確認ステップを追加すると誤操作を防げる
    if st.session_state.get('confirm_clear', False):
        clear_local_data()
        # 確認フラグをリセットしてからリロード
        st.session_state.confirm_clear = False
        st.rerun() # リセット後にアプリをリロード
    else:
        st.session_state.confirm_clear = True
        st.warning("⚠️ 本当に全データを消去しますか？実行するにはもう一度ボタンを押してください。")
        # 確認待ちの状態を維持するために再描画
        st.rerun()
