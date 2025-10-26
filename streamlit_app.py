import streamlit as st
import streamlit.components.v1 as components
from map_logic import deal, normalize_address, geocode_gsi, show_map, implementsql,main2,makesqldb
import time
import os

st.title("📍 廃業企業マップ")

# 年範囲を選ぶスライダー
year_range = st.slider("廃業年の範囲を選択", 2015, 2025, (2023, 2024))

# CSVアップロード
uploaded_file = st.file_uploader("法人番号CSVをアップロード", type=["csv"])

if uploaded_file is not None:
    with open("houjin.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    try:
        makesqldb("houjin.csv")
        st.write("houjin.db の存在:", os.path.exists("houjin.db"))
        st.success("CSVファイルをアップロードしました。地図を生成中…")
        main2("houjin.db")
    except Exception as e:
        st.error(f"処理中にエラーが発生しました: {e}")
        st.stop()
