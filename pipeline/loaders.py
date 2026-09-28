"""pipeline/raw의 수집기 스냅샷을 읽는 로더.

etl.py(홈)와 pipeline/pages/*.py가 함께 쓴다. 스냅샷이 아직 없으면 빈 값을 돌려줘
호출 쪽이 폴백하거나 "수집 먼저 실행" 안내 섹션을 내게 한다. 네트워크는 쓰지 않는다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from pipeline.common import RAW_DIR


def _latest_youtube_dir() -> Path | None:
  youtube_dir = RAW_DIR / "youtube"
  snapshots = sorted(p for p in youtube_dir.iterdir() if p.is_dir()) if youtube_dir.exists() else []
  return snapshots[-1] if snapshots else None


def load_youtube_comments() -> pl.DataFrame:
  """가장 최근 YouTube 원본 스냅샷에서 댓글 텍스트만 뽑아, "comment 컬럼이 있는 표"로
  평탄화한다. 수집기(npm run collect:youtube)를 아직 실행하지 않았다면 빈 DataFrame을
  돌려줘 호출 쪽이 폴백하게 한다."""
  snapshot = _latest_youtube_dir()
  if snapshot is None or not (snapshot / "comments.json").exists():
    return pl.DataFrame({"comment": []})

  payload = json.loads((snapshot / "comments.json").read_text(encoding="utf-8"))
  texts: list[str] = []
  for threads in payload.values():
    for thread in threads:
      texts.append(thread["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
  return pl.DataFrame({"comment": texts})


@dataclass(frozen=True)
class YoutubeVideo:
  video_id: str
  title: str
  channel: str
  published_at: str
  views: int
  likes: int
  comment_count: int  # 영상 전체 댓글 수 (수집한 표본 수와 다를 수 있다)


def load_youtube_videos() -> tuple[str, list[YoutubeVideo]]:
  """가장 최근 스냅샷의 (수집 일자, 영상 통계 목록). 스냅샷이 없으면 ("", [])."""
  snapshot = _latest_youtube_dir()
  if snapshot is None or not (snapshot / "videos.json").exists():
    return "", []

  payload = json.loads((snapshot / "videos.json").read_text(encoding="utf-8"))
  videos = [
    YoutubeVideo(
      video_id=item["id"],
      title=item["snippet"]["title"],
      channel=item["snippet"]["channelTitle"],
      published_at=item["snippet"]["publishedAt"],
      views=int(item["statistics"].get("viewCount", 0)),
      likes=int(item["statistics"].get("likeCount", 0)),
      comment_count=int(item["statistics"].get("commentCount", 0)),
    )
    for item in payload.get("items", [])
  ]
  return snapshot.name, videos
