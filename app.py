from datetime import datetime
import streamlit as st
import requests

# ページ設定
st.set_page_config(
    page_title="関越道 渋滞予測レポート作成ツール", page_icon="🚗", layout="centered"
)


def generate_traffic_report(date_str, lead_text):
  url = "https://www.drivetraffic.jp/cgi/getYosokuList"
  params = {"date": date_str, "type": "1"}

  headers = {
      "accept": "application/json, text/plain, */*",
      "accept-language": "ja-JP,ja;q=0.9,en-US;q=0.8,en-US;q=0.7",
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
    date_formatted = f"{dt_obj.month}月{dt_obj.day}日({w_list[dt_obj.weekday()]})"
  except:
    date_formatted = date_str

  up_items = []
  down_items = []

  for item in traffic_info:
    direction = item.get("direct_name", "")
    if "上り" in direction:
      up_items.append(item)
    elif "下り" in direction:
      down_items.append(item)

  # 冒頭のリード文を結合
  report = f"{lead_text}\n\n"
  report += f"ネクスコ東日本による渋滞予測では、\n{date_formatted}は"

  if up_items:
    report += "上り線で、\n\n"
    up_texts = []
    for item in up_items:
      start_ic = item.get("start_ic_name", "")
      end_ic = item.get("end_ic_name", "")
      start_time = item.get("start_time", "")
      end_time = item.get("end_time", "")
      bottle_neck = item.get("bottle_neck", "").replace("付近", "").strip()
      peak_dist = item.get("peak_dist", "")

      text = (
          f"・{start_ic}～{end_ic}で、{start_time}～{end_time}にかけて\n"
          f" {bottle_neck}付近を中心とした、最大{peak_dist}kmの渋滞"
      )
      up_texts.append(text)
    report += "\n\n".join(up_texts) + "\n"

  if down_items:
    if up_items:
      report += "\n"
    report += "下り線で、\n\n"
    down_texts = []
    for item in down_items:
      start_ic = item.get("start_ic_name", "")
      end_ic = item.get("end_ic_name", "")
      start_time = item.get("start_time", "")
      end_time = item.get("end_time", "")
      bottle_neck = item.get("bottle_neck", "").replace("付近", "").strip()
      peak_dist = item.get("peak_dist", "")

      text = (
          f"・{start_ic}～{end_ic}で、{start_time}～{end_time}にかけて\n"
          f" {bottle_neck}付近を中心とした、最大{peak_dist}kmの渋滞"
      )
      down_texts.append(text)
    report += "\n\n".join(down_texts) + "\n"

  report += "などが予測されています。"
  return report, None


# UIデザイン
st.title("🚗 関越道 渋滞予測レポート作成ツール")
st.write(
    "カレンダーから日付を選び、当日の実際の様子を入力してボタンを押すと、ニュース原稿風のレポートが作成できます。"
)

# カレンダーで日付選択
selected_date = st.date_input(
    "取得したい日付を選択してください", value=datetime(2026, 9, 23).date()
)

# 冒頭のリード文（空欄テンプレート形式）
default_lead = (
    "＜関越自動車道の様子＞\n\n"
    "現在ご覧いただいているのは午後〇時〇分ごろの関越自動車道の様子です。\n\n"
    "上り線下り線ともに交通量が多くみられたものの\n"
    "目立った渋滞はありませんでした。"
)

lead_input = st.text_area(
    "冒頭のリード文（実際の様子）を編集できます", value=default_lead, height=150
)

if st.button("渋滞予測を生成する", type="primary"):
  date_str = selected_date.strftime("%Y%m%d")

  with st.spinner(f"{date_str} のデータを取得中..."):
    report, error = generate_traffic_report(date_str, lead_input)

    if error:
      st.error(error)
    else:
      st.success("データの取得と文章生成に成功しました！")

      # 生成された文章のプレビュー表示
      st.text_area("生成されたレポート（プレビュー）", report, height=350)

      # ファイル名設定 (例: 20260923 -> 260923関越.txt)
      yy_mm_dd = date_str[2:]
      filename = f"{yy_mm_dd}関越.txt"

      # ダウンロードボタン
      st.download_button(
          label=f"📥 {filename} をダウンロードする",
          data=report,
          file_name=filename,
          mime="text/plain",
      )