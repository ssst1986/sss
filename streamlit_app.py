import streamlit as st
import streamlit.components.v1 as components
from map_logic import deal, normalize_address, geocode_gsi, show_map, implementsql,main2,makesqldb
import time
import os
st.title("📍 廃業企業マップ")

# CSVアップロード
uploaded_file = st.file_uploader("法人番号CSVをアップロード", type=["csv"])

if uploaded_file is not None:
    # ファイル保存
    csv_path = "houjin.csv"
    with open(csv_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("CSVファイルを保存しました")

    # DB作成 → 地図表示
    try:
        db_path = "houjin.db"
        makesqldb(csv_path)
        if os.path.exists(db_path):
            st.success("CSVファイルをアップロードしました。地図を生成中…")
            main2(db_path)
        else:
            st.error("DBファイルが見つかりません。CSVの読み込みに失敗している可能性があります。")
            st.stop()
    except Exception as e:
        st.error(f"処理中にエラーが発生しました:\n{e}")
        st.stop()
