"""End-to-end smoke test of a running exam server.

Usage:
    EXAM_URL=http://127.0.0.1:8099 uv run python scripts/smoke_api.py
"""

from __future__ import annotations

import json
import os
import re
import sys

import httpx

BASE = os.environ.get("EXAM_URL", "http://127.0.0.1:8000")
KNOWN = {
    "integer-01": "l = int(input())\nprint(l // 100)\n",
    "integer-10": "n = int(input())\nprint(n % 10)\nprint((n // 10) % 10)\n",
    "if-02": "n = int(input())\nprint(n + 1 if n > 0 else n - 2)\n",
    "for-18": (
        "a = float(input())\nn = int(input())\n"
        "total = 0.0\nsign = 1\npower = 1.0\n"
        "for _ in range(n + 1):\n    total += sign * power\n    sign = -sign\n    power *= a\n"
        "print(total)\n"
    ),
    "proc-14": (
        "for _ in range(2):\n"
        "    a = float(input()); b = float(input()); c = float(input())\n"
        "    print(c, a, b)\n"
    ),
    "series-06": (
        "n = int(input())\nvalues = list(map(float, input().split()))\n"
        "parts = [x - int(x) for x in values]\nproduct = 1.0\n"
        "for x in parts:\n    product *= x\nprint(*parts)\nprint(product)\n"
    ),
}


def parse_config(html: str) -> dict:
    match = re.search(r'id="exam-config">(.*?)</script>', html, re.DOTALL)
    if not match:
        raise RuntimeError("exam config not found")
    return json.loads(match.group(1))


def main() -> int:
    for attempt in range(1, 41):
        client = httpx.Client(base_url=BASE, follow_redirects=True, timeout=30)
        start = client.post("/start", data={"name": "Smoke Test", "consent": "yes"})
        if start.status_code != 200:
            print("start failed", start.status_code, start.text[:200])
            return 1
        config = parse_config(start.text)
        assert 'id="fullscreen-gate"' in start.text, "fullscreen gate missing"
        assert 'id="enter-fullscreen"' in start.text, "fullscreen button missing"
        chosen = next((task for task in config["tasks"] if task["id"] in KNOWN), None)
        if chosen is None:
            client.close()
            continue
        task_id = chosen["id"]
        response = client.post(
            f"/api/exam/{config['sessionId']}/run",
            json={"task_id": task_id, "code": KNOWN[task_id]},
        )
        data = response.json()
        print("run", task_id, response.status_code, data)
        if response.status_code != 200 or not data.get("solved"):
            print("correct solution did not solve the task")
            return 1
        state = client.get(f"/api/exam/{config['sessionId']}/state").json()
        assert state["score"] == 1, state
        client.post(f"/api/exam/{config['sessionId']}/finish", json={})
        result = client.get(f"/result/{config['sessionId']}")
        assert result.status_code == 200 and "задач решено" in result.text

        bad_client = httpx.Client(base_url=BASE, follow_redirects=True, timeout=30)
        bad_start = bad_client.post("/start", data={"name": "Sandbox Test", "consent": "yes"})
        bad_config = parse_config(bad_start.text)
        bad_id = bad_config["sessionId"]
        first_id = bad_config["tasks"][0]["id"]
        second_id = bad_config["tasks"][1]["id"]
        timeout_run = bad_client.post(
            f"/api/exam/{bad_id}/run",
            json={"task_id": first_id, "code": "while True:\n    pass\n"},
        )
        assert timeout_run.status_code == 200, timeout_run.text
        assert timeout_run.json()["error_kind"] == "timeout", timeout_run.json()
        forbidden_run = bad_client.post(
            f"/api/exam/{bad_id}/run",
            json={"task_id": second_id, "code": "import os\nprint(1)\n"},
        )
        assert forbidden_run.status_code == 200, forbidden_run.text
        assert forbidden_run.json()["error_kind"] == "not_allowed_or_syntax", forbidden_run.json()
        print("sandbox limits passed")

        banned_client = httpx.Client(base_url=BASE, follow_redirects=True, timeout=30)
        banned_start = banned_client.post("/start", data={"name": "Ban Test", "consent": "yes"})
        banned_config = parse_config(banned_start.text)
        banned_id = banned_config["sessionId"]
        violation = banned_client.post(
            f"/api/exam/{banned_id}/violation", json={"reason": "tab_switch"}
        )
        assert violation.status_code == 204
        banned_page = banned_client.get(f"/banned/{banned_id}")
        assert banned_page.status_code == 200 and "дисквалифицирована" in banned_page.text
        print(f"smoke passed on attempt {attempt}")
        return 0
    print("could not get a known task in 40 attempts")
    return 1


if __name__ == "__main__":
    sys.exit(main())
