"""분석가가 직접 수정하는 대시보드 집계 파이프라인 — Stage B(변환).

실행: .venv/Scripts/python.exe pipeline/etl.py (또는 npm run etl)
public/data/*.json 5개를 생성한다. 분석가는 build_* 함수들의 집계
로직만 수정하면 된다 — 나머지(검증/저장)는 건드리지 않아도 된다.

이 파일은 pipeline/raw/**(pipeline/collectors/*가 저장한 원본 스냅샷)와
pipeline/curated/**(분석가가 출처와 함께 직접 입력한 통계)만 읽으며,
네트워크나 API 키를 절대 건드리지 않는다 — 그래야 `npm run etl`이 언제나
빠르고 오프라인이며 결정적으로 동작한다. 원본 스냅샷/큐레이션 데이터가
아직 없는 항목은 generate_sample_events()로 폴백해, 최초 clone 직후
수집기를 한 번도 안 돌렸어도 `npm run etl`이 죽지 않게 한다.
"""

from __future__ import annotations

import json
import random
import re
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import polars as pl

from pipeline.common import CURATED_DIR, RAW_DIR, load_yaml, now
from pipeline.derived.concentration import compute_shares, parse_album_records
from pipeline.models import (
  CamelModel,
  DistributionCategory,
  DistributionData,
  GoodDirection,
  Insight,
  InsightSeverity,
  InsightsData,
  KpiMetric,
  MetricsData,
  PageData,
  SentimentLabel,
  TimeseriesData,
  TimeseriesSeries,
  TrendDirection,
  WordCloudData,
  WordCloudItem,
)
from pipeline.pages.sources import build_sources, load_sources, validate_refs
from pipeline.sentiment_words import (
  NEGATIVE_WORDS,
  NEGATIVE_WORDS_EN,
  POSITIVE_WORDS,
  POSITIVE_WORDS_EN,
  STOPWORDS,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "public" / "data"


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


# ---------------------------------------------------------------------------
# 실데이터 로더 — pipeline/raw(수집기 스냅샷)/pipeline/curated(큐레이션 통계)만
# 읽는다. 데이터가 아직 없으면 None/빈 값을 돌려줘 main()이 폴백하게 한다.
# ---------------------------------------------------------------------------
def load_curated_metrics() -> tuple[MetricsData, dict[str, TrendDirection]]:
  """pipeline/curated/kpi_snapshots.yaml에서 홈 화면 KPI를 읽는다.

  두 번째 반환값(favorable_trend)은 지표 id별로 "증가가 좋은지 감소가
  좋은지"를 build_insights()에 알려주는 힌트다. 지니계수처럼 감소가
  긍정적인 지표는 YAML에 `higher_is_better: false`로 표시한다.
  """
  data = load_yaml(CURATED_DIR / "kpi_snapshots.yaml")
  metrics: list[KpiMetric] = []
  favorable_trend: dict[str, TrendDirection] = {}

  for row in data.get("metrics", []):
    value = float(row["value"])
    prev_value = row.get("prev_value")
    delta: float | None = None
    trend: TrendDirection | None = None
    if prev_value is not None:
      delta = value - float(prev_value)
      trend = "up" if delta > 0 else "down" if delta < 0 else "flat"

    good_direction: GoodDirection = "down" if row.get("higher_is_better") is False else "up"
    metrics.append(
      KpiMetric(
        id=row["id"],
        label=row["label"],
        value=value,
        unit=row.get("unit") or None,
        delta=delta,
        trend=trend,
        good_direction=good_direction,
      )
    )
    favorable_trend[row["id"]] = good_direction

  return MetricsData(generated_at=now(), metrics=metrics), favorable_trend


DART_AGENCIES = ["hybe", "sm", "yg", "jyp"]

# DART 손익계산서 계정명 → (KPI id, 라벨). 계정명 표기는 실제 응답으로 확인했다.
DART_ACCOUNTS: dict[str, tuple[str, str]] = {
  "매출액": ("dart_revenue", "상장 4사 합산 매출액"),
  "영업이익": ("dart_operating_profit", "상장 4사 합산 영업이익"),
}


def _parse_dart_amount(raw: str | None) -> int | None:
  """DART 금액은 "2,363,993,529,000"처럼 쉼표가 붙은 문자열이고, 값이 없으면 "-"가 온다."""
  try:
    return int(str(raw).replace(",", ""))
  except ValueError:
    return None


def load_dart_metrics() -> list[KpiMetric]:
  """pipeline/raw/dart의 사업보고서 스냅샷에서 상장 4사(하이브·SM·YG·JYP)의
  연결 매출액·영업이익을 합산해 전년 대비 증감이 붙은 KPI 카드로 만든다.

  4사 중 하나라도 스냅샷이나 계정 값이 없으면 합산이 왜곡되므로 빈 리스트를
  돌려줘 KPI를 추가하지 않는다. 단위는 억 원이다."""
  dart_dir = RAW_DIR / "dart"
  # 계정명 → [당기 합계, 전기 합계]
  sums: dict[str, list[int]] = {name: [0, 0] for name in DART_ACCOUNTS}
  year = ""

  for agency in DART_AGENCIES:
    snapshots = sorted(dart_dir.glob(f"{agency}_*_11011.json")) if dart_dir.exists() else []
    if not snapshots:
      return []
    payload = json.loads(snapshots[-1].read_text(encoding="utf-8"))

    found: set[str] = set()
    for row in payload.get("list", []):
      account = row.get("account_nm")
      # 연결(CFS) 손익계산서(IS)만 쓴다. 별도(OFS)는 자회사 실적이 빠져 있다.
      if row.get("fs_div") != "CFS" or row.get("sj_div") != "IS":
        continue
      if account not in DART_ACCOUNTS or account in found:
        continue
      current = _parse_dart_amount(row.get("thstrm_amount"))
      previous = _parse_dart_amount(row.get("frmtrm_amount"))
      if current is None or previous is None:
        return []
      sums[account][0] += current
      sums[account][1] += previous
      found.add(account)
      year = row.get("bsns_year", year)

    if found != set(DART_ACCOUNTS):
      return []

  metrics: list[KpiMetric] = []
  for account, (metric_id, label) in DART_ACCOUNTS.items():
    current, previous = sums[account]
    delta = (current - previous) / 1e8
    metrics.append(
      KpiMetric(
        id=metric_id,
        label=f"{label} ({year})",
        value=round(current / 1e8, 1),
        unit="억 원",
        delta=round(delta, 1),
        trend="up" if delta > 0 else "down" if delta < 0 else "flat",
        good_direction="up",
      )
    )
  return metrics


def load_gini_timeseries() -> pl.DataFrame:
  """pipeline/curated/gini_series.yaml을 build_timeseries()가 바로 pivot할 수
  있는 date/category/value long-format으로 변환한다."""
  data = load_yaml(CURATED_DIR / "gini_series.yaml")
  rows = []
  for point in data.get("points", []):
    year = int(point["year"])
    # Gini(0~1)는 Top10 점유율(%)과 한 축에 그리면 바닥에 붙어 안 보이므로 ×100으로
    # 환산해 같은 스케일에 놓는다 (축을 둘로 나누는 이중축은 쓰지 않는다).
    rows.append(
      {"date": date(year, 12, 31), "category": "Gini계수(×100)", "value": round(float(point["gini"]) * 100, 2)}
    )
    rows.append(
      {
        "date": date(year, 12, 31),
        "category": "Top10_점유율",
        "value": float(point["top10_share_pct"]),
      }
    )
  return pl.DataFrame(rows) if rows else pl.DataFrame({"date": [], "category": [], "value": []})


def load_manual_insights() -> list[Insight]:
  """docx 등 기획 문서에서 옮긴, 숫자만으로는 자동 생성되지 않는 서사적 인사이트."""
  data = load_yaml(CURATED_DIR / "manual_insights.yaml")
  return [
    Insight(id=row["id"], severity=row["severity"], text=row["text"])
    for row in data.get("insights", [])
  ]


def load_circlechart_distribution() -> DistributionData | None:
  """가장 최근 circlechart 원본 스냅샷에서 판매 집중도 분포를 계산한다.
  수집기(npm run collect:circlechart)를 아직 실행하지 않았다면 None을
  돌려줘 main()이 generate_sample_events()로 폴백하게 한다."""
  circlechart_dir = RAW_DIR / "circlechart"
  snapshots = sorted(circlechart_dir.glob("album_*.json")) if circlechart_dir.exists() else []
  if not snapshots:
    return None

  latest = snapshots[-1]
  payload = json.loads(latest.read_text(encoding="utf-8"))
  albums = parse_album_records(payload["List"])
  shares = compute_shares(albums)
  categories = [
    DistributionCategory(category=row["category"], label=row["label"], value=row["value"])
    for row in shares.to_dicts()
  ]
  year = latest.stem.replace("album_", "")
  return DistributionData(
    generated_at=now(),
    title=f"{year}년 앨범 판매 집중도 (Circle Chart Top100)",
    categories=categories,
  )


def load_youtube_comments() -> pl.DataFrame:
  """가장 최근 YouTube 원본 스냅샷에서 댓글 텍스트만 뽑아, build_wordcloud()가
  기대하는 "comment 컬럼이 있는 표" 계약과 동일한 단일 컬럼 DataFrame으로
  평탄화한다. 수집기(npm run collect:youtube)를 아직 실행하지 않았다면
  빈 DataFrame을 돌려줘 main()이 generate_sample_events()로 폴백하게 한다."""
  youtube_dir = RAW_DIR / "youtube"
  snapshot_dirs = (
    sorted(p for p in youtube_dir.iterdir() if p.is_dir()) if youtube_dir.exists() else []
  )
  if not snapshot_dirs:
    return pl.DataFrame({"comment": []})

  comments_path = snapshot_dirs[-1] / "comments.json"
  if not comments_path.exists():
    return pl.DataFrame({"comment": []})

  payload = json.loads(comments_path.read_text(encoding="utf-8"))
  texts: list[str] = []
  for threads in payload.values():
    for thread in threads:
      snippet = thread["snippet"]["topLevelComment"]["snippet"]
      texts.append(snippet["textDisplay"])
  return pl.DataFrame({"comment": texts})


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

  return MetricsData(generated_at=now(), metrics=metrics)


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

  return TimeseriesData(generated_at=now(), series=series, points=points)


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
  return DistributionData(generated_at=now(), title="카테고리별 비중", categories=categories)


def _format_delta(delta: float) -> str:
  """증감폭을 천 단위 쉼표와 부호로 표기한다. 1 미만의 작은 값(예: Gini -0.0073)이
  "-0.0"으로 뭉개지지 않도록 소수 4자리까지 보여준다."""
  digits = 1 if abs(delta) >= 1 else 4
  return f"{delta:+,.{digits}f}"


def build_insights(
  metrics: MetricsData,
  favorable_trend: dict[str, TrendDirection] | None = None,
) -> InsightsData:
  """지표 증감 추세를 규칙 기반으로 문장화한다.

  favorable_trend: 지표 id별로 "up"(증가가 긍정적, 기본값) 또는 "down"(감소가
  긍정적)을 지정한다. 예: 판매량 집중도(Gini)는 감소가 긍정적이므로
  {"sales_concentration_gini": "down"}처럼 넘기면 severity가 뒤집힌다
  (load_curated_metrics()가 kpi_snapshots.yaml의 higher_is_better로 이 값을 만든다).
  이 함수가 "커스터마이징 지점" — 조건/문구를 분석가가 원하는 규칙으로 바꾸면 된다.
  """
  favorable_trend = favorable_trend or {}
  insights: list[Insight] = []
  for metric in metrics.metrics:
    if metric.trend in (None, "flat") or metric.delta is None:
      continue
    good_direction = favorable_trend.get(metric.id, "up")
    severity: InsightSeverity = "positive" if metric.trend == good_direction else "warning"
    verb = "증가" if metric.trend == "up" else "감소"
    unit = f" {metric.unit}" if metric.unit else ""
    insights.append(
      Insight(
        id=f"insight_{metric.id}",
        severity=severity,
        text=f"{metric.label} 지표가 직전 시점 대비 {verb}했습니다 ({_format_delta(metric.delta)}{unit}).",
        related_metric_id=metric.id,
      )
    )

  if not insights:
    insights.append(
      Insight(id="insight_default", severity="info", text="변동 없는 안정적인 지표 흐름입니다.")
    )

  return InsightsData(generated_at=now(), insights=insights)


def build_wordcloud(events: pl.DataFrame) -> WordCloudData:
  """comment 텍스트의 단어 빈도를 세고, 긍정/부정 단어 사전으로 감성을 분류한다."""
  tokens: list[str] = []
  for comment in events["comment"].to_list():
    # 영단어/한글 덩어리만 추출해 구두점·이모지를 제거하고, 1글자와 불용어는 뺀다.
    for token in re.findall(r"[a-z']+|[가-힣]+", comment.lower()):
      if len(token) > 1 and token not in STOPWORDS:
        tokens.append(token)

  counts = Counter(tokens)
  words: list[WordCloudItem] = []
  for text, weight in counts.most_common(30):
    # 부정 단어를 먼저 검사한다 — "불친절"처럼 부정 표현이 긍정 단어("친절")를
    # 부분 문자열로 포함하는 경우가 있어, 순서를 바꾸면 오분류가 발생한다.
    # 영어는 부분 문자열 오분류를 피하려고 완전 일치로만 판정한다.
    if text in NEGATIVE_WORDS_EN or any(word in text for word in NEGATIVE_WORDS):
      sentiment: SentimentLabel = "negative"
    elif text in POSITIVE_WORDS_EN or any(word in text for word in POSITIVE_WORDS):
      sentiment = "positive"
    else:
      sentiment = "neutral"
    words.append(WordCloudItem(text=text, weight=float(weight), sentiment=sentiment))

  return WordCloudData(generated_at=now(), words=words)


def build_pages() -> dict[str, PageData]:
  """slug → PageData. 페이지를 추가하면 pipeline/pages/<slug>.py의 build()를 여기에 등록한다.
  slug는 라우트 폴더명이자 public/data/<slug>.json 파일명이다."""
  return {}


def main() -> None:
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

  _sample_cache: pl.DataFrame | None = None

  def sample() -> pl.DataFrame:
    nonlocal _sample_cache
    if _sample_cache is None:
      print("실데이터가 아직 없어 generate_sample_events() 예시 데이터로 대체합니다.")
      _sample_cache = generate_sample_events()
    return _sample_cache

  curated_metrics, favorable_trend = load_curated_metrics()
  metrics = curated_metrics if curated_metrics.metrics else build_metrics(sample())

  # DART 실적 KPI는 매출·영업이익 모두 "증가가 긍정"이라 favorable_trend를 up으로 등록한다.
  dart_metrics = load_dart_metrics()
  if dart_metrics:
    metrics = MetricsData(generated_at=metrics.generated_at, metrics=[*metrics.metrics, *dart_metrics])
    favorable_trend.update({metric.id: "up" for metric in dart_metrics})

  gini_events = load_gini_timeseries()
  timeseries = build_timeseries(gini_events if gini_events.height > 0 else sample())

  distribution = load_circlechart_distribution()
  if distribution is None:
    print("circlechart 원본 스냅샷이 없습니다 (npm run collect:circlechart 먼저 실행).")
    distribution = build_distribution(sample())

  base_insights = build_insights(metrics, favorable_trend)
  manual_insights = load_manual_insights()
  insights = InsightsData(generated_at=now(), insights=[*base_insights.insights, *manual_insights])

  comments = load_youtube_comments()
  if comments.height > 0:
    wordcloud = build_wordcloud(comments)
  else:
    print("YouTube 원본 스냅샷이 없습니다 (npm run collect:youtube 먼저 실행).")
    wordcloud = build_wordcloud(sample())

  # 페이지 JSON과 출처 레지스트리. 인용한 sourceId가 sources.yaml에 없으면 여기서 중단된다.
  pages = build_pages()
  registry = load_sources()
  validate_refs(pages, registry)

  outputs: dict[str, CamelModel] = {
    "metrics.json": metrics,
    "timeseries.json": timeseries,
    "distribution.json": distribution,
    "insights.json": insights,
    "wordcloud.json": wordcloud,
    "sources.json": build_sources(pages, registry),
  }
  outputs.update({f"{slug}.json": page for slug, page in pages.items()})

  # 모든 모델의 직렬화를 끝낸 뒤에 한꺼번에 저장한다 — 중간에 실패해도 기존 JSON이
  # 반쪽만 갱신된 상태로 남지 않는다.
  rendered = {
    filename: json.dumps(model.model_dump(mode="json", by_alias=True), ensure_ascii=False, indent=2)
    for filename, model in outputs.items()
  }
  for filename, text in rendered.items():
    path = OUTPUT_DIR / filename
    path.write_text(text, encoding="utf-8")
    print(f"저장 완료: {path}")


if __name__ == "__main__":
  main()
