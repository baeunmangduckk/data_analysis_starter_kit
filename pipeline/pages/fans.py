"""팬 반응 페이지(fans.json) — YouTube 댓글 감성·워드클라우드 실데이터와 아티스트 팬덤 지표.

- 실데이터: pipeline/raw/youtube (npm run collect:youtube, 등록 영상은 curated/youtube_targets.yaml)
- 큐레이션: pipeline/curated/artist_metrics.yaml (소셜 팔로워·Spotify·유튜브 구독자)

표본이 영상 1개로 작을 수 있어, 페이지 상단에 표본 크기를 항상 명시한다.
"""

from __future__ import annotations

from pipeline.common import now
from pipeline.curated_schema import load_indicators
from pipeline.derived.sentiment import sentiment_counts, top_words
from pipeline.loaders import load_youtube_comments, load_youtube_videos
from pipeline.models import (
  ChartSection,
  Insight,
  InsightsSection,
  KpiMetric,
  NoticeSection,
  PageData,
  Section,
  StatsSection,
  TimeseriesSeries,
  WordCloudSection,
)
from pipeline.pages.blocks import group_chart

TITLE = "팬 반응"
SOURCE_ID = "youtube-data-api"
SENTIMENT_LABEL = {"positive": "긍정", "negative": "부정", "neutral": "중립"}


def _video_stats(snapshot_date: str, total_views: int, total_likes: int, total_comments: int) -> StatsSection:
  common = {"source_id": SOURCE_ID, "as_of": snapshot_date, "good_direction": "up", "confidence": "verified"}
  return StatsSection(
    title="등록 영상 반응 (YouTube Data API)",
    stats=[
      KpiMetric(id="fans_views", label="조회수", value=float(total_views), unit="회", **common),
      KpiMetric(id="fans_likes", label="좋아요", value=float(total_likes), unit="개", **common),
      KpiMetric(
        id="fans_like_rate",
        label="좋아요 비율",
        value=round(total_likes / total_views * 100, 2) if total_views else 0.0,
        unit="%",
        note="좋아요 ÷ 조회수",
        **common,
      ),
      KpiMetric(id="fans_comments", label="전체 댓글 수", value=float(total_comments), unit="개", **common),
    ],
  )


def build() -> PageData:
  snapshot_date, videos = load_youtube_videos()
  comments = load_youtube_comments()["comment"].to_list()

  sections: list[Section] = []
  insights: list[Insight] = []

  if not videos or not comments:
    sections.append(
      NoticeSection(tone="warning", message="YouTube 수집 데이터가 없습니다. npm run collect:youtube를 먼저 실행하세요.")
    )
  else:
    titles = " / ".join(f'"{video.title}"' for video in videos)
    sections.append(
      NoticeSection(
        tone="warning",
        message=f"표본 안내: 등록 영상 {len(videos)}개({titles}), 수집한 댓글 {len(comments):,}개 기준입니다 (수집일 {snapshot_date}). "
        "영상을 더 등록하려면 pipeline/curated/youtube_targets.yaml에 video_id를 추가하고 npm run collect:youtube -- --force를 실행하세요.",
      )
    )
    sections.append(
      _video_stats(
        snapshot_date,
        total_views=sum(video.views for video in videos),
        total_likes=sum(video.likes for video in videos),
        total_comments=sum(video.comment_count for video in videos),
      )
    )

    counts = sentiment_counts(comments)
    total = sum(counts.values())
    sections.append(
      ChartSection(
        title="댓글 감성 분포",
        caption=f"수집한 댓글 {total:,}개를 긍정·부정 단어 사전으로 분류한 결과입니다 (사전 기반 단순 분류라 중립 비중이 큽니다)",
        kind="barH",
        x_key="sentiment",
        series=[TimeseriesSeries(key="count", label="댓글 수")],
        points=[{"sentiment": SENTIMENT_LABEL[label], "count": float(counts[label])} for label in ("positive", "negative", "neutral")],
        unit="개",
        source_ids=[SOURCE_ID],
      )
    )
    share = {label: counts[label] / total * 100 for label in counts}
    insights.append(
      Insight(
        id="fans_sentiment_share",
        severity="info",
        text=f"수집 댓글 중 긍정 {share['positive']:.1f}%, 부정 {share['negative']:.1f}%, 중립 {share['neutral']:.1f}%입니다 (표본 {total:,}개).",
      )
    )
    sections.append(WordCloudSection(title="댓글 상위 단어", words=top_words(comments)))

  # ── 아티스트 팬덤 지표 (큐레이션) ──
  metrics = load_indicators("artist_metrics.yaml")
  by_category = {}
  for row in metrics:
    by_category.setdefault(row.category, []).append(row)

  fandom_charts = [
    ("social_followers", "소셜 팔로워 합산 Top 8", "Soundcharts 소셜 팔로워 합산 기준, 단위 백만 명", "팔로워"),
    ("spotify_listeners", "Spotify 월간 청취자 Top 7", "2026-09 기준, 단위 백만 명", "월간 청취자"),
    ("youtube_subscribers", "유튜브 구독자 Top 10", "2026-01 기준, 단위 백만 명", "구독자"),
  ]
  for category, title, caption, series_label in fandom_charts:
    rows = by_category.get(category, [])
    if rows:
      sections.append(group_chart(rows, title=title, caption=caption, series_label=series_label))

  youtube = by_category.get("youtube_subscribers", [])
  if len(youtube) >= 2 and youtube[0].value and youtube[1].value:
    insights.append(
      Insight(
        id="fans_youtube_top",
        severity="info",
        text=f"유튜브 구독자 1위 {youtube[0].short_label}({youtube[0].value:g}백만 명)와 2위 {youtube[1].short_label}({youtube[1].value:g}백만 명)가 3위 이하와 큰 격차를 보입니다.",
      )
    )

  if insights:
    sections.append(InsightsSection(title="핵심 포인트", insights=insights))

  return PageData(
    generated_at=now(),
    title=TITLE,
    summary="영상 댓글 반응과 아티스트 팬덤 규모",
    sections=sections,
  )
