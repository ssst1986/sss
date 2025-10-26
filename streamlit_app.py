import streamlit as st
import os
from map_logic import makesqldb, main2

st.set_page_config(page_title="法人地図アプリ", layout="wide")

st.title("🏢 法人地図ビジュアライザー")
st.markdown("法人番号データを地図上に可視化するアプリです。")

uploaded_file = st.file_uploader("法人番号CSVをアップロード（国税庁データ）", type=["csv"])

if uploaded_file is not None:
    with open("houjin.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("CSVを受け取りました。SQLiteに変換します…")

    try:
        if os.path.exists("houjin.db"):
            os.remove("houjin.db")
        makesqldb("houjin.csv")
        st.success("変換完了！次に地図を表示します。")
        with st.spinner("地図を生成中..."):
            main2("houjin.db")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
else:
    st.info("まずはCSVファイルをアップロードしてください。")