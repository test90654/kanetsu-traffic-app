import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import requests

from traffic_report import generate_traffic_report, TIMEOUT

SECRET = "test-only-sensitive-value"
PAGE = '<meta name="csrf-token" content="' + SECRET + '">'
ITEM = {
    "direct_name": "上り", "start_ic_name": "前橋", "end_ic_name": "花園",
    "start_time": "10:00", "end_time": "15:00",
    "bottle_neck": "高坂付近", "peak_dist": 20,
}


def response(body="", status=200, content_type="application/json"):
    result = requests.Response()
    result.status_code = status
    result._content = body.encode("utf-8")
    result.encoding = "utf-8"
    result.headers["Content-Type"] = content_type
    return result


def payload(items=None):
    return {"data": {"trafficStatInfo": {"関越自動車道": [ITEM] if items is None else items}}}


class TrafficReportTests(unittest.TestCase):
    def run_report(self, result, page=None):
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.side_effect = [page if page is not None else response(PAGE, content_type="text/html"), result]
        output = io.StringIO()
        with patch("traffic_report.requests.Session", return_value=session), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output), self.assertNoLogs():
            report, error = generate_traffic_report("20261105", "リード")
        self.assertNotIn(SECRET, output.getvalue())
        self.assertNotIn(SECRET, error or "")
        self.assertNotIn(SECRET, report or "")
        session.__exit__.assert_called_once()
        return report, error, session

    def test_success_and_fresh_session_headers(self):
        report, error, session = self.run_report(response(json.dumps(payload())))
        self.assertIsNone(error)
        self.assertIn("11月5日(木)", report)
        self.assertIn("最大20km", report)
        self.assertTrue(report.startswith("リード"))
        calls = session.get.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1].kwargs["headers"]["x-csrf-token"], SECRET)
        self.assertNotIn("cookies", calls[1].kwargs)
        for call in calls:
            self.assertEqual(call.kwargs["timeout"], TIMEOUT)
            self.assertFalse(call.kwargs["allow_redirects"])

    def test_both_directions(self):
        report, error, _ = self.run_report(response(json.dumps(payload([ITEM, dict(ITEM, direct_name="下り")]))))
        self.assertIsNone(error)
        self.assertIn("上り線", report)
        self.assertIn("下り線", report)

    def test_page_without_token(self):
        _, error, session = self.run_report(response(json.dumps(payload())), page=response("<html></html>", content_type="text/html"))
        self.assertIsNone(error)
        self.assertNotIn("x-csrf-token", session.get.call_args.kwargs["headers"])

    def test_http_errors_do_not_decode_or_expose_body(self):
        for status in (301, 302, 400, 401, 403, 404, 419, 429, 500, 503):
            with self.subTest(status=status):
                result = response(SECRET, status)
                with patch.object(result, "json") as decode:
                    report, error, _ = self.run_report(result)
                self.assertIsNone(report)
                self.assertTrue(error)
                decode.assert_not_called()

    def test_empty_responses(self):
        for body, status in (("", 200), (" \r\n\t", 200), ("", 204)):
            with self.subTest(status=status, body=body):
                result = response(body, status)
                report, error, _ = self.run_report(result)
                self.assertIsNone(report)
                self.assertIn("空の応答", error)

    def test_non_json_content_types(self):
        for kind in ("text/html", "text/plain", ""):
            with self.subTest(kind=kind):
                report, error, _ = self.run_report(response(SECRET, content_type=kind))
                self.assertIsNone(report)
                self.assertIn("JSON以外", error)

    def test_invalid_json_with_json_header(self):
        for body in ("<html>" + SECRET, "{broken", SECRET):
            report, error, _ = self.run_report(response(body))
            self.assertIsNone(report)
            self.assertIn("JSONデータ", error)

    def test_json_media_types(self):
        for kind in ("application/json; charset=utf-8", "Application/JSON", "application/problem+json"):
            _, error, _ = self.run_report(response(json.dumps(payload()), content_type=kind))
            self.assertIsNone(error)

    def test_network_errors(self):
        for exception in (requests.Timeout(SECRET), requests.ConnectionError(SECRET), requests.TooManyRedirects(SECRET)):
            with self.subTest(exception=type(exception).__name__):
                report, error, _ = self.run_report(exception)
                self.assertIsNone(report)
                self.assertTrue(error)

    def test_bootstrap_failures_stop_api_call(self):
        for page in (response(SECRET, 403), response(SECRET, 503), response("", 200), response(SECRET, 302)):
            report, error, session = self.run_report(response(json.dumps(payload())), page=page)
            self.assertIsNone(report)
            self.assertTrue(error)
            self.assertEqual(session.get.call_count, 1)

    def test_bootstrap_network_failure(self):
        with patch("traffic_report.requests.Session") as factory, self.assertNoLogs():
            factory.return_value.__enter__.return_value.get.side_effect = requests.Timeout(SECRET)
            report, error = generate_traffic_report("20261105", "")
        self.assertIsNone(report)
        self.assertIn("タイムアウト", error)
        self.assertNotIn(SECRET, error)

    def test_unexpected_json_shapes(self):
        shapes = [None, [], "text", {}, {"data": None}, {"data": []},
                  {"data": {"trafficStatInfo": None}},
                  {"data": {"trafficStatInfo": []}}]
        shapes.extend(payload(value) for value in ("invalid", {}, [None], [1], [dict(ITEM, direct_name=None)], [dict(ITEM, bottle_neck=[])], [dict(ITEM, peak_dist={})]))
        for value in shapes:
            with self.subTest(value=value):
                report, error, _ = self.run_report(response(json.dumps(value)))
                self.assertIsNone(report)
                self.assertIn("データ形式", error)

    def test_no_traffic(self):
        for value in (payload([]), {"data": {"trafficStatInfo": {}}}):
            report, error, _ = self.run_report(response(json.dumps(value)))
            self.assertIsNone(report)
            self.assertIn("見つかりません", error)

    def test_no_embedded_session_credentials(self):
        root = Path(__file__).resolve().parents[1]
        for filename in ("app.py", "traffic_report.py"):
            source = (root / filename).read_text(encoding="utf-8")
            self.assertNotIn("laravel_session", source)
            self.assertNotIn("AWSALB", source)


if __name__ == "__main__":
    unittest.main()
