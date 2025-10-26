import pandas as pd
import time
import requests
import urllib.parse
import re
import folium
from folium.plugins import HeatMap
import streamlit as st
import sqlite3
import streamlit.components.v1 as components

scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
# ジオコーダー初期化
path = r"C:\Users\Owner\Desktop\00_zenkoku_all_20250930.csv"

def normalize_address(addr):
    # 全角数字・記号を半角に変換
    import unicodedata
    return unicodedata.normalize('NFKC', addr)

def deal(path, year_range=(2023, 2024)):
   # CSV読み込み（Shift-JIS版）
   path = path
   df = pd.read_csv(path, encoding='cp932', header=None,dtype=str)

   # 必要なカラム名を定義（項番に対応）
   df.columns =  ["sequenceNumber","corporateNumber","process1","correct","updateDate",
                  "changeDate","name","nameImageId","process2","prefectureName",
                  "cityName","streetNumber","Address ImageId","prefectureCode",
                  "cityCode","postCode","addressOutside","AddressOutside ImageId",
                  "closeDate","closeCause","Successor CorporateNumber",
                  "changeCause","assignmentDate","Latest(0:old.1:latest)",
                  "enName","enPrefectureName","enCityName","enAddressOutside","furigana","hihyoji"
                  ]

   #print(df['process_code'])
   # 処理区分コードの意味（参考）
   process_map = {
      '01': '新規',
      '11': '商号変更',
      '12': '所在地変更',
      '21': '登記閉鎖（廃止・合併）',
      '22': '登記復活',
      '71': '吸収合併',
      '81': '商号抹消',
      '99': '削除'
   }
   legal_entity_codes = {
    "101": "国の機関（行政機関・国立大学法人など）",
    "201": "地方公共団体（都道府県、市町村、特別区など）",
    "301": "株式会社",
    "302": "有限会社（特例有限会社）",
    "303": "合名会社",
    "304": "合資会社",
    "305": "合同会社",
    "399": "その他の設立登記法人（一般社団法人など）",
    "401": "外国会社（外国法に基づく法人）",
    "499": "その他（区分不能な法人）"
}

   # 処理区分でフィルタ（設立・廃止・合併）
   target_codes = ['21']
   filtered = df[df['process1'].isin(target_codes)].copy()
   filtered['event'] = filtered['process1'].map(process_map)
   
   # 日付と年抽出
   filtered['changeDate'] = pd.to_datetime(filtered['changeDate'], errors='coerce')
   filtered['closed_year'] = filtered['changeDate'].dt.year

   # 住所結合（郵便番号付き）
   filtered['full_address'] =filtered['prefectureName'].fillna('') + \
                            filtered['cityName'].fillna('') + \
                            filtered['streetNumber'].fillna('')
                             
   result = filtered[[
      "corporateNumber", 'name', 'event', "changeDate", "closed_year",'full_address',]]
   result = result[(result['closed_year'] >= year_range[0]) &(result['closed_year'] <= year_range[1])]
   if result.empty:
    print("⚠️ 指定期間に該当する廃業企業が見つかりませんでした")
    return


   # 表示（またはCSV保存）
   #print(result)
   # result.to_csv('filtered_corp_events.csv', index=False, encoding='utf-8')
   return result

def geocode_gsi(address):
    # 郵便番号除去（〒123-4567 → 削除）
    address = re.sub(r'〒\d{3}-\d{4}', '', address)

    # 空白除去＋URLエンコード
    encoded = urllib.parse.quote(address.replace(' ', ''))

    # APIリクエスト
    url = f"https://msearch.gsi.go.jp/address-search/AddressSearch?q={encoded}"
    try:
        response = requests.get(url)
        time.sleep(1)  # レート制限対策

        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if data:
                lat = data[0]["geometry"]["coordinates"][1]
                lon = data[0]["geometry"]["coordinates"][0]
                return lat, lon
    except Exception as e:
        print(f"エラー: {e}")
    return None, None

def makesqldb(path):
    df = pd.read_csv(path, encoding='cp932', header=None, dtype=str)
    st.write("CSV読み込み行数:", len(df))

    df.columns = [
        "sequenceNumber", "corporateNumber", "process1", "correct", "updateDate",
        "changeDate", "name", "nameImageId", "process2", "prefectureName",
        "cityName", "streetNumber", "Address ImageId", "prefectureCode",
        "cityCode", "postCode", "addressOutside", "AddressOutside ImageId",
        "closeDate", "closeCause", "Successor CorporateNumber",
        "changeCause", "assignmentDate", "Latest(0:old.1:latest)",
        "enName", "enPrefectureName", "enCityName", "enAddressOutside", "furigana", "hihyoji"
    ]

    conn = sqlite3.connect("houjin.db")
    df.to_sql("houjin", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    conn = sqlite3.connect("houjin.db")
    count_df = pd.read_sql("SELECT COUNT(*) FROM houjin", conn)
    st.write("DB登録件数:", count_df.iloc[0, 0])
    conn.close()

    return 

def implementsql(db_path):
    # GitHub上のJIS X 0401都道府県リスト作成
    url = "https://raw.githubusercontent.com/HirMtsd/Code/refs/heads/master/JISX0401/Prefecture_list.json"
    response = requests.get(url)
    pref_data = response.json()["prefectures"]

    # 都道府県名 → コードの辞書作成
    pref_options = {item["name"]: item["code"] for item in pref_data}
    
    # Streamlitで都道府県名を選択
    selected_pref_name = st.selectbox("都道府県を選択", list(pref_options.keys()))
    selected_pref_code = pref_options[selected_pref_name]

    # GitHub上の市町村JSON（JIS X 0402）
    url_city = "https://raw.githubusercontent.com/HirMtsd/Code/refs/heads/master/JISX0402/City_list.json"
    response_city = requests.get(url_city)
    city_data = response_city.json()["cities"]

    # 市町村名 → コードの辞書（選択された都道府県のみ）
    city_options = {
        item["name"]: {"pref_code": item["pref_code"], "city_code": item["city_code"]}
        for item in city_data if item["pref_code"] == selected_pref_code}

    #期待値　{"半田市": {"pref_code": "23", "city_code": "205"},"名古屋市": {"pref_code": "23", "city_code": "101"},"豊田市": {"pref_code": "23", "city_code": "239"},...}


    # Streamlitで市町村名を選択
    selected_city_name = st.selectbox("市町村を選択", list(city_options.keys()))
    selected_codes = city_options[selected_city_name]

    conn = sqlite3.connect(db_path)
    #conn = sqlite3.connect("data/houjin.db")  # リポジトリ内のdataフォルダ

    # 緯度・経度が未登録の法人データを抽出
    query = f"""
    SELECT *
    FROM houjin
    WHERE (lat IS NULL OR lon IS NULL)
    AND prefectureCode = '{selected_codes["pref_code"]}'
    AND cityCode = '{selected_codes["city_code"]}'
    """


    #df = pd.read_sql(query, conn)
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"SQL読み込みエラー: {e}")
        st.stop()
    #print(df['process_code'])
    # 処理区分コードの意味（参考）
    process_map = {
      '01': '新規',
      '11': '商号変更',
      '12': '所在地変更',
      '21': '登記閉鎖（廃止・合併）',
      '22': '登記復活',
      '71': '吸収合併',
      '81': '商号抹消',
      '99': '削除'
    }

    legal_entity_codes = {
    "101": "国の機関（行政機関・国立大学法人など）",
    "201": "地方公共団体（都道府県、市町村、特別区など）",
    "301": "株式会社",
    "302": "有限会社（特例有限会社）",
    "303": "合名会社",
    "304": "合資会社",
    "305": "合同会社",
    "399": "その他の設立登記法人（一般社団法人など）",
    "401": "外国会社（外国法に基づく法人）",
    "499": "その他（区分不能な法人）"
    }

    # 処理区分でフィルタ（設立・廃止・合併）
    target_codes = ['21']
    filtered = df[df['process1'].isin(target_codes)].copy()
    filtered['event'] = filtered['process1'].map(process_map)

    # 住所結合（都道府県＋市町村＋番地）
    df["full_address"] = (
        df["prefectureName"].fillna("") +
        df["cityName"].fillna("") +
        df["streetNumber"].fillna("")
    )
    df["assignmentDate"] = pd.to_datetime(df["assignmentDate"], errors="coerce")
    df["changeDate"] = pd.to_datetime(df["changeDate"], errors="coerce")

    # コメント生成
    def classify_lifespan(days):
        if pd.isna(days):
            return "不明"
        elif days < 180:
            return "⚠️短命！"
        elif days >= 3650:
            return "🏆長寿！"
        else:
            return "普通"

    # 3. 寿命計算
    df["lifespan_days"] = (df["changeDate"] - df["assignmentDate"]).dt.days
    df["lifespan_years"] = (df["lifespan_days"] / 365).round(1)

    # 4. コメント生成（短命・長寿など）
    df["lifespan_comment"] = df["lifespan_days"].apply(classify_lifespan)
    df["lifespan_text"] = (
        "存続期間：" +
        df["lifespan_days"].astype(str) + "日（約" +
        df["lifespan_years"].astype(str) + "年） " +
        df["lifespan_comment"]
    )

    conn.close()
    return df

def show_map(df):
    m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=10)
    for _, row in df.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=f"{row['name']}<br>{row['lifespan_text']}",
            tooltip=row["full_address"]
        ).add_to(m)
    return m

def main2(db_path):
    import time

    # 緯度経度の列を追加
    latitudes = []
    longitudes = []

    # 法人データ抽出（寿命情報付き）
    filtered = implementsql(db_path)
    filtered = filtered.iloc[:10, :]  # サンプル制限

    # ジオコーディング（地理院API）
    for addr in filtered['full_address']:
        normalized = normalize_address(addr)
        lat, lon = geocode_gsi(normalized)
        latitudes.append(lat)
        longitudes.append(lon)
        time.sleep(1.1)  # API制限対策

    # 緯度・経度をDataFrameに追加
    filtered.loc[:, 'lat'] = latitudes
    filtered.loc[:, 'lon'] = longitudes

    # 地図描画に使う列だけ抽出
    geo_df = filtered[["corporateNumber", 'name', 'event', "changeDate", "closed_year",'full_address', 'lat', 'lon',"lifespan_years","lifespan_days"]]

    # 欠損を除外（緯度経度が取得できなかった行を除く）
    geo_df = geo_df.dropna(subset=['lat', 'lon'])
    m = show_map(geo_df)
    m.save("corp_map.html")  # HTMLとして一時保存
    components.html(m._repr_html_(), height=600)
    # ダウンロードリンク表示
    with open("corp_map.html", "rb") as f:
        st.download_button(
            label="📥 地図をHTMLで保存",
            data=f,
            file_name="corp_map.html",
            mime="text/html"
        )

    return 

