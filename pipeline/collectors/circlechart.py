"""circlechart.kr 연간 앨범 판매 Top100 차트 수집기.

circlechart.kr의 화면 자체는 JS 렌더링이지만, 화면이 내부적으로 호출하는
JSON API(POST /data/api/chart/album)를 직접 호출한다. 이 방식은
real_kpop_future(레거시 프로젝트)의 scrapers/circlechart.py에서 검증된
접근이며, 2026-09-27 기준 실제 응답을 확인해 필드명을 맞췄다
(SERVICE_RANKING/Album_CNT/ARTIST_NAME/ALBUM_NAME/de_nm).

주의:
  - 응답에 "targetTime" 파라미터가 부족하다는 ErrorMsg가 함께 오지만
    ResultStatus는 "OK"이고 List 데이터는 정상 반환된다 — 사이트 자체의
    느슨한 검증 메시지로 보이며 무시해도 된다.
  - 레거시 프로젝트는 이 API의 라이브 응답이 자사 과거 CSV와 연도별로
    정확히 일치하지 않았다고 경고했다(집계 시점/기준 차이 추정). 이
    수집기 출력을 신뢰하기 전에 circlechart.kr의 공식 "연간결산" 페이지
    수치와 사람이 직접 대조할 것.
  - de_nm(유통사)은 실제 소속사가 아니다 — 에이전시 분류에 쓰지 말 것
    (pipeline/derived/concentration.py도 이 필드를 쓰지 않는다).

실행: python -m pipeline.collectors.circlechart [--year 2025]
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime
from urllib import robotparser

import httpx

from pipeline.config import RAW_DIR

BASE_URL = "https://circlechart.kr"
API_URL = f"{BASE_URL}/data/api/chart/album"
PAGE_URL = f"{BASE_URL}/page_chart/album.circle"
USER_AGENT = "kpop-dashboard-v2-research-bot/0.1"
REQUEST_INTERVAL_SEC = 3.0


def _check_allowed() -> bool:
  """robots.txt를 확인한다. robots.txt가 없거나(404) 읽기에 성공하면 허용으로 간주하고,
  네트워크 오류로 아예 읽지 못한 경우에만 보수적으로 차단한다."""
  parser = robotparser.RobotFileParser()
  parser.set_url(f"{BASE_URL}/robots.txt")
  try:
    parser.read()
  except Exception:
    return False
  return parser.can_fetch(USER_AGENT, API_URL)


def fetch_album_chart(year: int) -> dict:
  if not _check_allowed():
    raise RuntimeError("robots.txt가 이 경로의 접근을 허용하지 않습니다.")

  payload = {
    "nationGbn": "T",
    "termGbn": "year",
    "hitYear": str(year),
    "targetTime": "",
    "yearTime": "1",
    "curUrl": PAGE_URL,
  }
  headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": PAGE_URL,
    "User-Agent": USER_AGENT,
  }
  response = httpx.post(API_URL, data=payload, headers=headers, timeout=15.0)
  response.raise_for_status()
  time.sleep(REQUEST_INTERVAL_SEC)
  return response.json()


def save_snapshot(year: int, data: dict) -> None:
  circlechart_dir = RAW_DIR / "circlechart"
  history_dir = circlechart_dir / "history"
  circlechart_dir.mkdir(parents=True, exist_ok=True)
  history_dir.mkdir(parents=True, exist_ok=True)

  latest_path = circlechart_dir / f"album_{year}.json"
  latest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

  today = date.today().isoformat()
  history_path = history_dir / f"{today}.json"
  history_payload = {
    "collected_at": datetime.now().astimezone().isoformat(),
    "year": year,
    "data": data,
  }
  history_path.write_text(
    json.dumps(history_payload, ensure_ascii=False, indent=2), encoding="utf-8"
  )

  print(f"저장 완료: {latest_path}")
  print(f"저장 완료: {history_path}")


def main() -> None:
  parser = argparse.ArgumentParser(description="circlechart.kr 연간 앨범 판매 Top100 수집")
  parser.add_argument(
    "--year", type=int, default=date.today().year - 1, help="수집할 연도(기본: 작년)"
  )
  args = parser.parse_args()

  print(f"circlechart.kr {args.year}년 앨범 차트 수집 중...")
  data = fetch_album_chart(args.year)
  if data.get("ResultStatus") != "OK":
    raise RuntimeError(f"circlechart API가 오류를 반환했습니다: {data.get('ErrorMsg')}")
  save_snapshot(args.year, data)


if __name__ == "__main__":
  main()
