from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="業務アシスタントツール", page_icon="🛠️", layout="centered"
)

# サイドバーで機能を切り替え
st.sidebar.title("📌 機能選択")
app_mode = st.sidebar.selectbox(
    "利用するツールを選択してください",
    ["🚗 関越道 渋滞予測レポート", "📺 市民第一ch 番組紹介ジェネレーター"],
)

# ==========================================
# 1. 関越道 渋滞予測レポート
# ==========================================
if app_mode == "🚗 関越道 渋滞予測レポート":
  st.title("🚗 関越道 渋滞予測レポート作成ツール")
  st.write("カレンダーから日付を選び、レポートを生成できます。")


  def generate_traffic_report(date_str, lead_text):
    url = "https://www.drivetraffic.jp/cgi/getYosokuList"
    params = {"date": date_str, "type": "1"}
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "referer": "https://www.drivetraffic.jp/congestion",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
        ),
        "x-csrf-token": "diFrwFxtdPcRuATFpZIf4zeTQjMOfJmk8HylgnnJ",
        "x-requested-with": "XMLHttpRequest",
    }
    cookies = {
        "AWSALB": (
            "77KetncUsuBMy8AVSYZFs2xJtraQlvekBQNtuFusCeVeyUZ8CpZsslVZaTc6JpKD6NxQZWLWEGQBHLzJOkpzDb9zIyyKAg7D3xoI/5CJE2nPAzsXe6tCUvfqz15H"
        ),
        "AWSALBCORS": (
            "77KetncUsuBMy8AVSYZFs2xJtraQlvekBQNtuFusCeVeyUZ8CpZsslVZaTc6JpKD6NxQZWLWEGQBHLzJOkpzDb9zIyyKAg7D3xoI/5CJE2nPAzsXe6tCUvfqz15H"
        ),
        "laravel_session": (
            "eyJpdiI6ImlpK1pERkwwT05rYzFhdmNnMWw3OWc9PSIsInZhbHVlIjoiSzEyeXVGMkN1MEIyT21PcW5nQjJ0ckNHbmRrak1GWmVnekNSUDE5bElMNXlZS1p6dldsQjJBdnhwbU5tN3BXVWE4WE11YXN4aldqV1dQOEdLcm9LSkYrdmtOd0h4c3pNRHc0dmYwV25RRC9YYmd0U0UxemNjT3g4VVNDOFlsNTIiLCJtYWMiOiIxYTA4YjBjMTE2YjMwNzY3Zjk3NjA3ODM5NWY3N2E2ZWQ3YTE4Mzk3NzlhN2FmZjhiMmIxYWY1N2Y4OWYwNzEyIiwidGFnIjoiIn0="
        ),
    }

    response = requests.get(
        url, params=params, headers=headers, cookies=cookies
    )
    if response.status_code != 200:
      return None, f"データ取得失敗: ステータスコード {response.status_code}"

    res_json = response.json()
    traffic_info = (
        res_json.get("data", {}).get("trafficStatInfo", {}).get("関越自動車道")
    )
    if not traffic_info or not isinstance(traffic_info, list):
      return None, "指定された日付の関越自動車道のデータは見つかりませんでした。"

    try:
      dt_obj = datetime.strptime(date_str, "%Y%m%d")
      w_list = ["月", "火", "水", "木", "金", "土", "日"]
      date_formatted = (
          f"{dt_obj.month}月{dt_obj.day}日({w_list[dt_obj.weekday()]})"
      )
    except:
      date_formatted = date_str

    up_items = [
        item for item in traffic_info if "上り" in item.get("direct_name", "")
    ]
    down_items = [
        item for item in traffic_info if "下り" in item.get("direct_name", "")
    ]

    report = f"{lead_text}\n\nネクスコ東日本による渋滞予測では、\n{date_formatted}は"

    if up_items:
      report += "上り線で、\n\n"
      up_texts = []
      for item in up_items:
        s_ic = item.get("start_ic_name", "")
        e_ic = item.get("end_ic_name", "")
        s_t = item.get("start_time", "")
        e_t = item.get("end_time", "")
        b_neck = item.get("bottle_neck", "").replace("付近", "").strip()
        p_dist = item.get("peak_dist", "")
        up_texts.append(
            f"・{s_ic}～{e_ic}で、{s_t}～{e_t}にかけて\n"
            f" {b_neck}付近を中心とした、最大{p_dist}kmの渋滞"
        )
      report += "\n\n".join(up_texts) + "\n"

    if down_items:
      if up_items:
        report += "\n"
      report += "下り線で、\n\n"
      down_texts = []
      for item in down_items:
        s_ic = item.get("start_ic_name", "")
        e_ic = item.get("end_ic_name", "")
        s_t = item.get("start_time", "")
        e_t = item.get("end_time", "")
        b_neck = item.get("bottle_neck", "").replace("付近", "").strip()
        p_dist = item.get("peak_dist", "")
        down_texts.append(
            f"・{s_ic}～{e_ic}で、{s_t}～{e_t}にかけて\n"
            f" {b_neck}付近を中心とした、最大{p_dist}kmの渋滞"
        )
      report += "\n\n".join(down_texts) + "\n"

    report += "などが予測されています。"
    return report, None


  selected_date = st.date_input(
      "取得したい日付を選択してください", value=datetime.today().date()
  )
  default_lead = (
      "＜関越自動車道の様子＞\n\n"
      "現在ご覧いただいているのは午後〇時〇分ごろの関越自動車道の様子です。\n\n"
      "上り線下り線ともに交通量が多くみられたものの\n"
      "目立った渋滞はありませんでした。"
  )
  lead_input = st.text_area(
      "冒頭のリード文（編集可能）", value=default_lead, height=140
  )

  if st.button("渋滞予測を生成する", type="primary"):
    date_str = selected_date.strftime("%Y%m%d")
    with st.spinner("データを取得中..."):
      report, error = generate_traffic_report(date_str, lead_input)
      if error:
        st.error(error)
      else:
        st.success("レポート生成完了！")
        st.text_area("生成されたレポート", report, height=300)
        filename = f"{date_str[2:]}関越.txt"
        st.download_button(
            f"📥 {filename} をダウンロード",
            data=report,
            file_name=filename,
            mime="text/plain",
        )

# ==========================================
# 2. 市民第一ch 番組紹介ジェネレーター
# ==========================================
elif app_mode == "📺 市民第一ch 番組紹介ジェネレーター":
  st.title("📺 市民第一ch 番組紹介ジェネレーター")
  st.write(
      "番組表Excel（.xls / .xlsx）をアップロードして、紹介文を生成します。"
  )

  uploaded_file = st.file_uploader(
      "📁 番組表Excelファイルを選択", type=["xls", "xlsx"]
  )

  if uploaded_file is not None:
    try:
      df = pd.read_excel(uploaded_file, sheet_name=0, header=None)
      schedule_dict = {}

      for index, row in df.iterrows():
        if index < 2:
          continue
        date_raw = row.iloc[0]
        day_raw = str(row.iloc[1]).strip()
        prog_title = str(row.iloc[2]).strip()

        if pd.isna(date_raw) or not prog_title or prog_title == "nan":
          continue

        try:
          date_dt = pd.to_datetime(str(date_raw))
          date_key = date_dt.date()
        except:
          continue

        schedule_dict[date_key] = {
            "month": date_dt.month,
            "day": date_dt.day,
            "day_of_week": day_raw.replace("曜日", ""),
            "title": prog_title.replace("\r\n", "\n"),
        }

      if schedule_dict:
        st.success(
            f"読み込み成功！ 合計 {len(schedule_dict)} 日分のデータがあります。"
        )
        st.markdown("---")
        selected_date = st.date_input(
            "放送日を選択", value=datetime.today().date()
        )

        if selected_date in schedule_dict:
          info = schedule_dict[selected_date]
          m = info["month"]
          d = info["day"]
          dow = info["day_of_week"]
          prog_title = info["title"]
          date_str = f"{m}月{d}日({dow})"

          content = f"""＜市民第１ｃｈ(１１１ｃｈ）{date_str}放送の番組紹介＞

{date_str}市民第1ch(111ch)で放送する番組は、

「{prog_title}」です。

初回の放送は、午前８時４５分からです。

ぜひご覧ください。
"""
          st.text_area("生成プレビュー", content, height=200)
          filename = f"{m}月{d}日({dow})_番組紹介.txt"
          st.download_button(
              f"📥 {filename} をダウンロード",
              data=content,
              file_name=filename,
              mime="text/plain",
          )
        else:
          st.warning(
              f"選択された日付 ({selected_date.strftime('%Y/%m/%d')}) の番組データが見つかりませんでした。"
          )
      else:
        st.error("有効な番組データが見つかりませんでした。")
    except Exception as e:
      st.error(f"ファイル読み込みエラー: {e}")