"""maedong.kr 공개 API 에서 오늘치를 받아 CSV 로 떨군다.

이 저장소의 목적은 **찾아지는 것**이다. 국내 증시 시그널을 2020년부터 매일
기록해 20거래일 뒤 수익률까지 집계한 데이터는 공개된 곳이 없다. 깃허브 검색과
구글 색인에 걸리면 퀀트·개발자 쪽에서 사이트를 발견한다.

인증이 없는 공개 API 만 쓴다 — 이 스크립트는 누구 컴퓨터에서든 돌고, 결과가
사이트 화면과 갈릴 수가 없다(같은 계산을 쓴다).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import urllib.request
import json

BASE = "https://maedong.kr"
ROOT = Path(__file__).resolve().parent.parent
LISTS_IN_DAILY = ("value-surge", "high-52w", "low-52w", "gap-up", "dry-surge")


def api(path: str) -> dict:
    req = urllib.request.Request(f"{BASE}{path}", headers={"User-Agent": "maedong-data github-action"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def write(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{path.relative_to(ROOT)}  {len(rows)}행")


def main() -> None:
    index = api("/api/v1")
    # 성과가 집계되는 목록만 — 재무 기반(저PER·고배당)은 과거 날짜에 오늘 재무를
    # 쓰게 되어(미래 참조) 사이트도 집계하지 않는다
    slugs = [s["signal"] for s in index["signals"] if s.get("has_stats")]
    date = api("/api/v1/market")["meta"]["data_date"]

    # 1) 목록별 성과 — 이 저장소의 핵심
    rows = []
    for slug in slugs:
        try:
            st = api(f"/api/v1/signals/{slug}/stats?window=all")
        except Exception as exc:                      # noqa: BLE001
            print(f"  {slug}: {exc}", file=sys.stderr)
            continue
        h = {x["trading_days"]: x for x in st.get("horizons", [])}
        h20 = h.get(20) or {}
        if not h20.get("n"):
            continue
        rows.append([st["label"], slug, st.get("since"), st.get("signal_days"), h20.get("n"),
                     (h.get(1) or {}).get("avg_pct"), (h.get(5) or {}).get("avg_pct"),
                     h20.get("avg_pct"), h20.get("median_pct"), h20.get("market_avg_pct"),
                     h20.get("excess_pp"), h20.get("win_rate_pct"), st.get("verdict")])
    rows.sort(key=lambda r: (r[10] is None, -(r[10] or 0)))
    write(ROOT / "data" / "signal_performance.csv",
          ["label", "slug", "since", "signal_days", "n",
           "avg_1d_pct", "avg_5d_pct", "avg_20d_pct", "median_20d_pct",
           "market_avg_20d_pct", "excess_20d_pp", "win_rate_20d_pct", "verdict"], rows)

    # 2) 그날의 목록 구성원 — 날짜별 한 장
    day = []
    for slug in LISTS_IN_DAILY:
        try:
            body = api(f"/api/v1/signals?signal={slug}&limit=100")
        except Exception:                              # noqa: BLE001
            continue
        for it in body.get("items", []):
            day.append([date, slug, it["code"], it["name"], it.get("market"),
                        it.get("close_krw"), it.get("change_pct"), it.get("value_krw"),
                        it.get("metric_text"),
                        "|".join(f["code"] for f in (it.get("flags") or []))])
    if day:
        write(ROOT / "data" / "daily" / f"{date}.csv",
              ["date", "signal", "code", "name", "market", "close_krw", "change_pct",
               "value_krw", "metric", "flags"], day)

    (ROOT / "data" / "LATEST").write_text(date + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
