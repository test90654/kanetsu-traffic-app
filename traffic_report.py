"""Traffic report retrieval without persisting or displaying session credentials."""

import datetime
from html.parser import HTMLParser

import requests

BASE_URL = "https://www.drivetraffic.jp"
TIMEOUT = (5, 20)
FORMAT_ERROR = "取得先のデータ形式が想定と異なります。時間をおいて再度お試しください。"


class _CSRFParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.token = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("name") == "csrf-token":
            self.token = attrs.get("content")


def _response_error(response):
    # Never include response bodies, headers, URLs or exception text in errors.
    if response.status_code in (401, 403, 419):
        return "取得先の認証・セッション確認に失敗しました。時間をおいて再度お試しください。"
    if response.status_code == 429:
        return "取得先へのアクセスが集中しています。時間をおいて再度お試しください。"
    if not 200 <= response.status_code < 300:
        return f"データ取得失敗: HTTP {response.status_code}。時間をおいて再度お試しください。"
    if not response.content.strip():
        return "取得先から空の応答が返されました。時間をおいて再度お試しください。"
    return None


def _fetch_traffic_info(date_str):
    try:
        # Obtain current cookies and CSRF token from the same short-lived session.
        # Disable redirects so cookies/tokens cannot be forwarded to another URL.
        with requests.Session() as session:
            page = session.get(
                BASE_URL + "/congestion", timeout=TIMEOUT, allow_redirects=False
            )
            error = _response_error(page)
            if error:
                return None, error
            parser = _CSRFParser()
            parser.feed(page.text)
            headers = {
                "accept": "application/json",
                "referer": BASE_URL + "/congestion",
                "x-requested-with": "XMLHttpRequest",
            }
            if parser.token:
                headers["x-csrf-token"] = parser.token
            response = session.get(
                BASE_URL + "/cgi/getYosokuList",
                params={"date": date_str, "type": "1"},
                headers=headers,
                timeout=TIMEOUT,
                allow_redirects=False,
            )
            error = _response_error(response)
            if error:
                return None, error
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if content_type != "application/json" and not (
                content_type.startswith("application/") and content_type.endswith("+json")
            ):
                return None, "取得先からJSON以外の応答が返されました。メンテナンス等の可能性があります。時間をおいて再度お試しください。"
            try:
                res_json = response.json()
            except ValueError:
                return None, "取得先のJSONデータを読み取れませんでした。時間をおいて再度お試しください。"
    except requests.Timeout:
        return None, "データ取得がタイムアウトしました。時間をおいて再度お試しください。"
    except requests.RequestException:
        return None, "取得先に接続できませんでした。時間をおいて再度お試しください。"

    if not isinstance(res_json, dict):
        return None, FORMAT_ERROR
    data = res_json.get("data")
    if not isinstance(data, dict):
        return None, FORMAT_ERROR
    stats = data.get("trafficStatInfo")
    if not isinstance(stats, dict):
        return None, FORMAT_ERROR
    traffic_info = stats.get("関越自動車道")
    if traffic_info is None or traffic_info == []:
        return None, "指定された日付の関越自動車道のデータは見つかりませんでした。"
    if not isinstance(traffic_info, list):
        return None, FORMAT_ERROR
    text_fields = ("direct_name", "start_ic_name", "end_ic_name", "start_time", "end_time", "bottle_neck")
    for item in traffic_info:
        if not isinstance(item, dict):
            return None, FORMAT_ERROR
        if any(not isinstance(item.get(field, ""), str) for field in text_fields):
            return None, FORMAT_ERROR
        if not isinstance(item.get("peak_dist", ""), (str, int, float)):
            return None, FORMAT_ERROR
    return traffic_info, None


def generate_traffic_report(date_str, lead_text):
    traffic_info, error = _fetch_traffic_info(date_str)
    if error:
        return None, error

    try:
        dt_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
        w_list = ["月", "火", "水", "木", "金", "土", "日"]
        date_formatted = (
                f"{dt_obj.month}月{dt_obj.day}日({w_list[dt_obj.weekday()]})"
        )
    except ValueError:
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
