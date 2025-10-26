import streamlit as st
import streamlit.components.v1 as components
from map_logic import deal, normalize_address, geocode_gsi, show_map, implementsql,main2,makesqldb
import time
import os

st.title("📍 廃業企業マップ")

# スライダーは常に表示
year_range = st.slider("廃業年の範囲を選択", 2015, 2025, (2023, 2024))

uploaded_file = st.file_uploader("法人番号CSVをアップロード", type=["csv"])

if uploaded_file is not None:
    with open("houjin.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        makesqldb("houjin.csv")
        if os.path.exists("houjin.db"):
            st.success("CSVファイルをアップロードしました。地図を生成中…")
            main2("houjin.db")
        else:
            st.error("DBファイルが見つかりません。CSVの読み込みに失敗している可能性があります。")
            st.stop()
    except Exception as e:
        st.error(f"処理中にエラーが発生しました:\n{e}")
        st.stop()
