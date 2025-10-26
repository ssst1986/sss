import streamlit as st
from map_logic import deal, normalize_address, geocode_gsi, show_map
import time

st.title("📍 廃業企業マップ")

# 年範囲を選ぶスライダー
year_range = st.slider("廃業年の範囲を選択", 2015, 2025, (2023, 2024))

# CSVアップロード
uploaded_file = st.file_uploader("法人番号CSVをアップロード", type=["csv"])

if uploaded_file is not None:
    with open("houjin.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # deal() に年範囲を渡してフィルタ
    df = deal("houjin.csv", year_range=year_range)
    st.write("データフレームの列一覧：", df.columns.tolist())#後で削除

    if df is None or df.empty:
        st.warning("指定年に該当する廃業企業が見つかりませんでした")
        st.stop()

    df = df.iloc[:10, :]  # サンプル制限

    # ジオコーディング
    latitudes = []
    longitudes = []
    for addr in df["full_address"]:
        norm = normalize_address(addr)
        lat, lon = geocode_gsi(norm)
        latitudes.append(lat)
        longitudes.append(lon)
        time.sleep(1.1)

    df["lat"] = latitudes
    df["lon"] = longitudes
    df = df.dropna(subset=["lat", "lon"])
    print(df.columns) 

    # 地図表示
    m = show_map(df)
    m.save("corp_map.html")
    st.components.v1.html(m._repr_html_(), height=600)

    # ダウンロードボタン
    with open("corp_map.html", "rb") as f:
        st.download_button("📥 地図をHTMLで保存", f, "corp_map.html", "text/html")