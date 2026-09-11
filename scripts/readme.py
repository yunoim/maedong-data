"""README 의 표를 최신 데이터로 다시 쓴다.

README 가 이 저장소의 얼굴이다 — 깃허브 검색·구글이 읽는 것도, 사람이 처음
보는 것도 여기다. 손으로 적으면 반드시 낡으므로 매번 CSV 에서 만든다.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START, END = "<!-- TABLE:START -->", "<!-- TABLE:END -->"


def main() -> None:
    rows = list(csv.DictReader((ROOT / "data" / "signal_performance.csv").open(encoding="utf-8")))
    lines = ["| 목록 | 표본 | 20일 평균 | 시장 대비 | 상승 확률 | 판정 |",
             "|---|---:|---:|---:|---:|---|"]
    for r in rows:
        lines.append(f"| {r['label']} | {int(r['n']):,} | {float(r['avg_20d_pct']):+.2f}% | "
                     f"**{float(r['excess_20d_pp']):+.2f}%p** | "
                     f"{float(r['win_rate_20d_pct']):.1f}% | {r['verdict']} |")
    lost = sum(1 for r in rows if r["verdict"] == "시장 하회")
    beat = sum(1 for r in rows if r["verdict"] == "시장 상회")
    total = sum(int(r["n"]) for r in rows)
    since = min(r["since"] for r in rows)

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    body = (f"{START}\n{since}부터 목록 {len(rows)}종을 매일 기록해 1·5·20거래일 뒤 수익률까지 "
            f"집계했습니다. 표본 **{total:,}건**. 그중 **{lost}종이 20거래일 뒤 시장을 밑돌았고 "
            f"{beat}종이 웃돌았습니다.**\n\n" + "\n".join(lines) + f"\n{END}")
    if START in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), body, text, flags=re.S)
    readme.write_text(text, encoding="utf-8")
    print(f"README 갱신 — {len(rows)}종 · {total:,}건")


if __name__ == "__main__":
    main()
