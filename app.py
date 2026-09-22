import datetime
from datetime import timedelta
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="ニュースアシスタントツール", page_icon="🛠️", layout="centered"
)

# サイドバーで機能を切り替え
st.sidebar.title("📌 機能選択")
app_mode = st.sidebar.selectbox(
    "利用するツールを選択してください",
    [
        "🚗 関越道 渋滞予測レポート",
        "📺 日別番組紹介ジェネレーター",
        "📅 週間番組紹介（月〜日）ジェネレーター",
    ],
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
      dt_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
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
      "取得したい日付を選択してください", value=datetime.date.today()
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
# 2. 日別番組紹介ジェネレーター
# ==========================================
elif app_mode == "📺 日別番組紹介ジェネレーター":
  st.title("📺 日別番組紹介ジェネレーター")
  st.write(
      "番組表Excel（.xls / .xlsx）をアップロードして、日別の紹介文を生成します。"
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
            "放送日を選択", value=datetime.date.today()
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

# ==========================================
# 3. 週間番組紹介（月〜日）ジェネレーター
# ==========================================
elif app_mode == "📅 週間番組紹介（月〜日）ジェネレーター":
  st.title("📅 週間番組紹介（月〜日）ジェネレーター")
  st.write(
      "番組表Excelをアップロードし、起点となる月曜日を選択すると、月曜〜日曜の紹介文を生成します。"
  )

  uploaded_files = st.file_uploader(
      "📁 番組表Excelファイルを選択（月またぎ対応のため複数選択も可）",
      type=["xls", "xlsx"],
      accept_multiple_files=True,
  )

  if uploaded_files:
    schedule_dict = {}

    for file in uploaded_files:
      try:
        df = pd.read_excel(file, sheet_name=0, header=None)
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
            d_key = date_dt.date()
            schedule_dict[d_key] = {
                "date": d_key,
                "month": date_dt.month,
                "day": date_dt.day,
                "day_of_week": day_raw.replace("曜日", ""),
                "title": prog_title.replace("\r\n", " "),
            }
          except:
            continue
      except Exception as e:
        st.warning(f"ファイル {file.name} の読み込みスキップ: {e}")

    if not schedule_dict:
      st.error("有効な番組データが見つかりませんでした。")
    else:
      st.success(
          f"読み込み成功！ 合計 {len(schedule_dict)} 日分のデータがあります。"
      )
      st.markdown("---")

      # 直近の月曜日をデフォルト値にする
      today = datetime.date.today()
      default_monday = today - timedelta(days=today.weekday())

      selected_monday = st.date_input(
          "起点となる「月曜日」を選択してください", value=default_monday
      )

      # 選択された曜日を判定
      w_names = ["月", "火", "水", "木", "金", "土", "日"]
      sel_w_name = w_names[selected_monday.weekday()]

      if selected_monday.weekday() != 0:
        st.warning(
            f"⚠️ 選択された日付は「{sel_w_name}曜日」です。起点となる「月曜日」を選択してください。"
        )
      else:
        # 月曜〜日曜（7日間）のデータを取得
        week_dates = [selected_monday + timedelta(days=i) for i in range(7)]
        week_items = []
        missing_dates = []

        for d in week_dates:
          if d in schedule_dict:
            week_items.append(schedule_dict[d])
          else:
            missing_dates.append(d)

        if missing_dates:
          st.error(
              f"以下の日付のデータがExcel内に見つかりません: "
              + ", ".join([d.strftime("%Y/%m/%d") for d in missing_dates])
          )
        else:
          start_item = week_items[0]
          end_item = week_items[-1]

          start_str = f"{start_item['month']}月{start_item['day']}日({start_item['day_of_week']})"
          end_str = (
              f"{end_item['month']}月{end_item['day']}日({end_item['day_of_week']})"
          )

          lines = []
          lines.append(
              f"≪{start_str}～{end_str}の市民第1ch(111ch)番組紹介≫\n"
          )
          lines.append(
              f"{start_str}～{end_str}に\n市民第1ｃｈ(111ch)で放送する番組を紹介します。\n"
          )

          for item in week_items:
            m = item["month"]
            d = item["day"]
            dow = item["day_of_week"]
            date_formatted = f"{m}月{d:2d}日({dow})"
            lines.append(f'{date_formatted}「{item["title"]}」')

          lines.append("\n初回の放送は午前８時４５分からです。\n")
          lines.append("是非ご覧ください。")

          content = "\n".join(lines)
          filename = f"{start_str}～{end_str}_番組紹介.txt"

          st.text_area("生成プレビュー", content, height=320)
          st.download_button(
              f"📥 {filename} をダウンロード",
              data=content,
              file_name=filename,
              mime="text/plain",
              type="primary",
          )