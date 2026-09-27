"""YouTube Data API v3 수집기 — 댓글/조회수 스냅샷을 1회성으로 저장한다.

일일 쿼터(기본 10,000 units)를 지키기 위해 두 가지를 설계 원칙으로 삼는다.

1. search.list(호출당 100 units)는 절대 쓰지 않는다. 대신
   pipeline/curated/youtube_targets.yaml에 분석가가 직접 등록한 video_id만
   videos.list/commentThreads.list(호출당 ~1 unit)로 조회한다.
2. 자동 주기 없이 "수동 트리거만" 수집한다 — pipeline/raw/youtube/state.json에
   이미 스냅샷이 있으면 기본적으로 재수집을 건너뛰고, 분석가가 명시적으로
   --force를 줬을 때만 다시 수집한다. 수집이 중간에 실패하면 state.json을
   갱신하지 않아, 다음 실행이 "이미 수집됨"으로 잘못 막히지 않는다.

실행: python -m pipeline.collectors.youtube [--force]
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime

import httpx
import yaml

from pipeline.config import CURATED_DIR, RAW_DIR, YOUTUBE_API_KEY

API_BASE = "https://www.googleapis.com/youtube/v3"
STATE_PATH = RAW_DIR / "youtube" / "state.json"
MAX_COMMENT_PAGES = 5


def load_targets() -> list[str]:
  path = CURATED_DIR / "youtube_targets.yaml"
  data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
  return [v["video_id"] for v in data.get("videos", []) if v.get("video_id")]


def load_state() -> dict:
  if STATE_PATH.exists():
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))
  return {}


def save_state(video_ids: list[str]) -> None:
  STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
  state = {
    "last_collected_at": datetime.now().astimezone().isoformat(),
    "video_ids": video_ids,
  }
  STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_videos(video_ids: list[str]) -> dict:
  params = {
    "key": YOUTUBE_API_KEY,
    "id": ",".join(video_ids),
    "part": "snippet,statistics",
  }
  response = httpx.get(f"{API_BASE}/videos", params=params, timeout=15.0)
  response.raise_for_status()
  return response.json()


def fetch_comments(video_id: str, max_pages: int = MAX_COMMENT_PAGES) -> list[dict]:
  comments: list[dict] = []
  page_token: str | None = None
  for _ in range(max_pages):
    params = {
      "key": YOUTUBE_API_KEY,
      "videoId": video_id,
      "part": "snippet",
      "maxResults": 100,
      "textFormat": "plainText",
    }
    if page_token:
      params["pageToken"] = page_token
    response = httpx.get(f"{API_BASE}/commentThreads", params=params, timeout=15.0)
    response.raise_for_status()
    payload = response.json()
    comments.extend(payload.get("items", []))
    page_token = payload.get("nextPageToken")
    if not page_token:
      break
  return comments


def collect(video_ids: list[str]) -> None:
  today_dir = RAW_DIR / "youtube" / datetime.now().date().isoformat()
  today_dir.mkdir(parents=True, exist_ok=True)

  videos_payload = fetch_videos(video_ids)
  (today_dir / "videos.json").write_text(
    json.dumps(videos_payload, ensure_ascii=False, indent=2), encoding="utf-8"
  )

  all_comments = {video_id: fetch_comments(video_id) for video_id in video_ids}
  (today_dir / "comments.json").write_text(
    json.dumps(all_comments, ensure_ascii=False, indent=2), encoding="utf-8"
  )

  print(f"저장 완료: {today_dir}")
  save_state(video_ids)  # 성공했을 때만 기록 — 실패 시 다음 실행이 막히지 않도록 함


def main() -> None:
  parser = argparse.ArgumentParser(description="YouTube Data API 1회성 수집")
  parser.add_argument(
    "--force", action="store_true", help="이미 수집된 스냅샷이 있어도 다시 수집한다"
  )
  args = parser.parse_args()

  state = load_state()
  if state.get("last_collected_at") and not args.force:
    print(
      f"YouTube 데이터가 이미 {state['last_collected_at']}에 수집되어 있습니다. "
      "다시 수집하려면 --force를 사용하세요."
    )
    return

  if not YOUTUBE_API_KEY:
    print("YOUTUBE_API_KEY가 설정되지 않았습니다 (.env 확인). 수집을 중단합니다.")
    return

  video_ids = load_targets()
  if not video_ids:
    print("pipeline/curated/youtube_targets.yaml에 등록된 video_id가 없습니다.")
    return

  print(f"YouTube 수집 시작 (대상 {len(video_ids)}개 영상)...")
  collect(video_ids)


if __name__ == "__main__":
  main()
