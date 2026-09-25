"""분석가가 직접 수정하는 대시보드 집계 파이프라인.

실행: .venv/Scripts/python.exe pipeline/etl.py (또는 npm run etl)
public/data/*.json 5개를 생성한다. 분석가는 build_* 함수들의 집계
로직만 수정하면 된다 — 나머지(검증/저장)는 건드리지 않아도 된다.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

import polars as pl

from pipeline.models import (
  DistributionCategory,
  DistributionData,
  Insight,
  InsightsData,
  KpiMetric,
  MetricsData,
  SentimentLabel,
  TimeseriesData,
  TimeseriesSeries,
  TrendDirection,
  WordCloudData,
  WordCloudItem,
)
from pipeline.sentiment_words import NEGATIVE_WORDS, POSITIVE_WORDS

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "public" / "data"


def _now() -> datetime:
  return datetime.now().astimezone()


def generate_sample_events() -> pl.DataFrame:
  """실제 데이터 연동 전까지 쓰는 예시 원본 데이터.

  분석가는 이 함수를 실제 데이터 로드 코드(DB/CSV 읽기 등)로 교체하면 되고,
  아래 build_* 함수들은 "category/value/date/comment 컬럼이 있는 표"를
  받는다는 계약만 유지하면 그대로 재사용할 수 있다.
  """
  rng = random.Random(42)
  start = date(2026, 8, 1)
  categories = ["카테고리 A", "카테고리 B", "카테고리 C"]
  comments = [
    "서비스가 친절하고 빨라서 만족합니다",
    "대기 시간이 너무 길어서 불편했어요",
    "가격 대비 괜찮은 편입니다",
    "품질이 기대보다 아쉬웠습니다",
    "다시 이용하고 싶은 좋은 경험이었습니다",
    "직원이 불친절해서 실망했습니다",
  ]

  rows = []
  for day_offset in range(30):
    current_date = start + timedelta(days=day_offset)
    for base, category in zip([100, 160, 130], categories):
      value = base + day_offset * rng.uniform(0.5, 3.0) + rng.uniform(-15, 15)
      rows.append({
        "date": current_date,
        "category": category,
        "value": round(max(value, 0), 1),
        "comment": rng.choice(comments),
      })
  return pl.DataFrame(rows)


def build_metrics(events: pl.DataFrame) -> MetricsData:
  """카테고리별 최근 7일 합계와 그 직전 7일 합계를 비교해 KPI 카드를 만든다."""
  last_date = events["date"].max()
  recent_start = last_date - timedelta(days=6)
  prev_start = recent_start - timedelta(days=7)
  prev_end = recent_start - timedelta(days=1)

  recent = (
    events.filter(pl.col("date") >= recent_start)
    .group_by("category")
    .agg(pl.col("value").sum().alias("value"))
  )
  previous = (
    events.filter(pl.col("date").is_between(prev_start, prev_end))
    .group_by("category")
    .agg(pl.col("value").sum().alias("prev_value"))
  )
  merged = recent.join(previous, on="category", how="left").fill_null(0).sort("category")

  metrics: list[KpiMetric] = []
  for row in merged.to_dicts():
    delta = row["value"] - row["prev_value"]
    trend: TrendDirection = "up" if delta > 0 else "down" if delta < 0 else "flat"
    metrics.append(
      KpiMetric(
        id=row["category"].replace(" ", "_"),
        label=row["category"],
        value=float(row["value"]),
        delta=float(delta),
        trend=trend,
      )
    )

  return MetricsData(generated_at=_now(), metrics=metrics)


def build_timeseries(events: pl.DataFrame) -> TimeseriesData:
  """날짜 x 카테고리 합계를 recharts가 바로 쓸 수 있는 wide format으로 변환한다."""
  daily = events.group_by(["date", "category"]).agg(pl.col("value").sum().alias("value"))
  wide = daily.pivot(on="category", index="date", values="value").sort("date").fill_null(0)

  category_columns = sorted(c for c in wide.columns if c != "date")
  series = [TimeseriesSeries(key=c.replace(" ", "_"), label=c) for c in category_columns]

  points = []
  for row in wide.to_dicts():
    point: dict[str, str | float] = {"date": row["date"].isoformat()}
    for column in category_columns:
      point[column.replace(" ", "_")] = float(row[column])
    points.append(point)

  return TimeseriesData(generated_at=_now(), series=series, points=points)


def build_distribution(events: pl.DataFrame) -> DistributionData:
  """전체 기간 카테고리별 합계 비중을 계산한다."""
  totals = events.group_by("category").agg(pl.col("value").sum().alias("value")).sort("category")
  categories = [
    DistributionCategory(
      category=row["category"].replace(" ", "_"),
      label=row["category"],
      value=float(row["value"]),
    )
    for row in totals.to_dicts()
  ]
  return DistributionData(generated_at=_now(), title="카테고리별 비중", categories=categories)


def build_insights(metrics: MetricsData) -> InsightsData:
  """지표 증감 추세를 규칙 기반으로 문장화한다.

  이 함수가 "커스터마이징 지점" — 조건/문구를 분석가가 원하는 규칙으로 바꾸면 된다.
  """
  insights: list[Insight] = []
  for index, metric in enumerate(metrics.metrics):
    if metric.trend == "down":
      insights.append(
        Insight(
          id=f"insight_{index}",
          severity="warning",
          text=f"{metric.label} 지표가 전주 대비 감소했습니다 ({metric.delta:+.1f}).",
          related_metric_id=metric.id,
        )
      )
    elif metric.trend == "up":
      insights.append(
        Insight(
          id=f"insight_{index}",
          severity="positive",
          text=f"{metric.label} 지표가 전주 대비 증가했습니다 ({metric.delta:+.1f}).",
          related_metric_id=metric.id,
        )
      )

  if not insights:
    insights.append(
      Insight(id="insight_default", severity="info", text="변동 없는 안정적인 지표 흐름입니다.")
    )

  return InsightsData(generated_at=_now(), insights=insights)


def build_wordcloud(events: pl.DataFrame) -> WordCloudData:
  """comment 텍스트의 단어 빈도를 세고, 긍정/부정 단어 사전으로 감성을 분류한다."""
  tokens: list[str] = []
  for comment in events["comment"].to_list():
    tokens.extend(comment.split())

  counts = Counter(tokens)
  words: list[WordCloudItem] = []
  for text, weight in counts.most_common(30):
    # 부정 단어를 먼저 검사한다 — "불친절"처럼 부정 표현이 긍정 단어("친절")를
    # 부분 문자열로 포함하는 경우가 있어, 순서를 바꾸면 오분류가 발생한다.
    if any(word in text for word in NEGATIVE_WORDS):
      sentiment: SentimentLabel = "negative"
    elif any(word in text for word in POSITIVE_WORDS):
      sentiment = "positive"
    else:
      sentiment = "neutral"
    words.append(WordCloudItem(text=text, weight=float(weight), sentiment=sentiment))

  return WordCloudData(generated_at=_now(), words=words)


def main() -> None:
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  events = generate_sample_events()

  metrics = build_metrics(events)
  outputs: dict[str, MetricsData | TimeseriesData | DistributionData | InsightsData | WordCloudData] = {
    "metrics.json": metrics,
    "timeseries.json": build_timeseries(events),
    "distribution.json": build_distribution(events),
    "insights.json": build_insights(metrics),
    "wordcloud.json": build_wordcloud(events),
  }

  for filename, model in outputs.items():
    path = OUTPUT_DIR / filename
    payload = model.model_dump(mode="json", by_alias=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장 완료: {path}")


if __name__ == "__main__":
  main()
