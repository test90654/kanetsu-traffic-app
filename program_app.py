from datetime import datetime
import pandas as pd
import streamlit as st

# ページ設定
st.set_page_config(
    page_title="市民第一ch 番組紹介ジェネレーター", page_icon="📺", layout="centered"
)

st.title("📺 市民第一ch 番組紹介ジェネレーター")
st.write(
    "お手元の番組表Excel（.xls / .xlsx）をアップロードして、掲載されている日付ごとの番組紹介文を簡単に生成・ダウンロードできます。"
)

# ファイルアップロード機能
uploaded_file = st.file_uploader(
    "📁 番組表のExcelファイルを選択してください", type=["xls", "xlsx"]
)

if uploaded_file is not None:
  try:
    # アップロードされたExcelを読み込む
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

      day_short = day_raw.replace("曜日", "")

      schedule_dict[date_key] = {
          "month": date_dt.month,
          "day": date_dt.day,
          "day_of_week": day_short,
          "title": prog_title.replace("\r\n", "\n"),
      }

    if schedule_dict:
      st.success(
          f"ファイルの読み込みに成功しました！合計 {len(schedule_dict)}"
          " 日分のデータが見つかりました。"
      )

      st.markdown("---")
      st.subheader("📅 放送日を選択して紹介文を作成")

      # カレンダーで日付選択
      selected_date = st.date_input(
          "作成したい放送日を選択", value=datetime.today().date()
      )

      if selected_date in schedule_dict:
        info = schedule_dict[selected_date]
        m = info["month"]
        d = info["day"]
        dow = info["day_of_week"]
        prog_title = info["title"]

        date_str = f"{m}月{d}日({dow})"

        # 紹介文の自動生成
        content = f"""＜市民第１ｃｈ(１１１ｃｈ）{date_str}放送の番組紹介＞

{date_str}市民第1ch(111ch)で放送する番組は、

「{prog_title}」です。

初回の放送は、午前８時４５分からです。

ぜひご覧ください。
"""

        st.subheader("📝 生成されたプレビュー")
        st.text_area("文章確認", content, height=220)

        filename = f"{m}月{d}日({dow})_番組紹介.txt"

        # ダウンロードボタン
        st.download_button(
            label=f"📥 {filename} をダウンロードする",
            data=content,
            file_name=filename,
            mime="text/plain",
        )
      else:
        st.warning(
            f"選択された日付 ({selected_date.strftime('%Y年%m月%d日')})"
            "の番組データがこのファイル内に見つかりませんでした。日付をご確認ください。"
        )
    else:
      st.error(
          "有効な番組データが見つかりませんでした。ファイルのフォーマットを確認してください。"
      )

  except Exception as e:
    st.error(f"ファイルの読み込み中にエラーが発生しました: {e}")
else:
  st.info(
      "👆 上のボタンから、社内からダウンロードした番組表Excelファイルを選択（またはドラッグ＆ドロップ）してください。"
  )