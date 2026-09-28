"""대시보드 JSON 데이터 계약(schema)을 정의하는 Pydantic 모델 모음.

pipeline/etl.py가 만든 결과를 이 모델로 검증한 뒤 public/data/*.json으로 저장한다.
홈용 모델은 src/types/dashboard.ts, 페이지 섹션 모델은 src/types/page.ts와 1:1로 대응한다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

TrendDirection = Literal["up", "down", "flat"]
InsightSeverity = Literal["info", "positive", "warning", "critical"]
SentimentLabel = Literal["positive", "negative", "neutral"]
# 증가/감소 중 무엇이 좋은 변화인지 (예: Gini는 "down")
GoodDirection = Literal["up", "down"]
# 큐레이션 수치의 신뢰도 — 화면에서 배지로 구분해 보여준다
Confidence = Literal["verified", "estimated", "legacy_unverified"]
ChartKind = Literal["line", "area", "column", "barH"]


class CamelModel(BaseModel):
  """snake_case 속성을 camelCase JSON으로 직렬화하기 위한 공통 베이스."""

  model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# metrics.json — KPI 카드
# ---------------------------------------------------------------------------
class KpiMetric(CamelModel):
  id: str
  label: str
  value: float
  unit: str | None = None
  delta: float | None = None
  trend: TrendDirection | None = None
  # 아래 필드는 페이지 stats 섹션에서 쓰는 선택 필드다 (홈 metrics.json은 생략해도 된다)
  note: str | None = None
  source_id: str | None = Field(default=None, alias="sourceId")
  as_of: str | None = Field(default=None, alias="asOf")
  good_direction: GoodDirection | None = Field(default=None, alias="goodDirection")
  confidence: Confidence | None = None


class MetricsData(CamelModel):
  generated_at: datetime = Field(alias="generatedAt")
  metrics: list[KpiMetric]


# ---------------------------------------------------------------------------
# 시계열 계열 정의 — 페이지 chart 섹션과 공용 검증
# ---------------------------------------------------------------------------
class TimeseriesSeries(CamelModel):
  key: str
  label: str


def validate_points_match_series(
  series: list[TimeseriesSeries],
  points: list[dict[str, str | float | None]],
  x_key: str,
) -> None:
  """wide 포맷 points의 키가 x축 키 + series 정의와 정확히 일치하는지 확인한다.
  TimeseriesData와 페이지 chart 섹션이 함께 쓰는 공용 검증이다."""
  expected_keys = {x_key, *(s.key for s in series)}
  for point in points:
    if set(point.keys()) != expected_keys:
      raise ValueError(
        f"point 키가 series 정의와 일치하지 않습니다: {set(point.keys())} != {expected_keys}"
      )


# ---------------------------------------------------------------------------
# insights.json — 정성적 인사이트
# ---------------------------------------------------------------------------
class Insight(CamelModel):
  id: str
  severity: InsightSeverity
  text: str
  related_metric_id: str | None = Field(default=None, alias="relatedMetricId")


class InsightsData(CamelModel):
  generated_at: datetime = Field(alias="generatedAt")
  insights: list[Insight]


# ---------------------------------------------------------------------------
# 워드클라우드 + 감성분석 (페이지 wordcloud 섹션이 사용)
# ---------------------------------------------------------------------------
class WordCloudItem(CamelModel):
  text: str
  weight: float
  sentiment: SentimentLabel


# ---------------------------------------------------------------------------
# 페이지 JSON(market/concentration/finance/fans/global/ai-virtual.json)
# 페이지 = 섹션 배열. 새 화면 요소는 섹션 블록을 추가하는 것으로 만들고, 블록 종류는
# 아래 소수(stats/chart/table/cases/insights/wordcloud/notice)로 제한한다.
# src/types/page.ts와 1:1로 대응한다.
# ---------------------------------------------------------------------------
class StatsSection(CamelModel):
  type: Literal["stats"] = "stats"
  title: str | None = None
  stats: list[KpiMetric]


class ChartSection(CamelModel):
  type: Literal["chart"] = "chart"
  title: str
  caption: str | None = None
  kind: ChartKind
  x_key: str = Field(alias="xKey")
  series: list[TimeseriesSeries]
  # None은 결측(예: 2024년 수치 없음)이며 화면에서 선을 끊거나 막대를 생략한다.
  points: list[dict[str, str | float | None]]
  unit: str | None = None
  source_ids: list[str] = Field(default_factory=list, alias="sourceIds")

  @model_validator(mode="after")
  def _validate_points_match_series(self) -> "ChartSection":
    validate_points_match_series(self.series, self.points, self.x_key)
    return self


class TableColumn(CamelModel):
  key: str
  label: str
  align: Literal["left", "right"] = "left"


class TableSection(CamelModel):
  type: Literal["table"] = "table"
  title: str
  caption: str | None = None
  columns: list[TableColumn]
  rows: list[dict[str, str | float | None]]
  source_ids: list[str] = Field(default_factory=list, alias="sourceIds")

  @model_validator(mode="after")
  def _validate_rows_match_columns(self) -> "TableSection":
    expected_keys = {column.key for column in self.columns}
    for row in self.rows:
      if set(row.keys()) != expected_keys:
        raise ValueError(f"table row 키가 columns 정의와 일치하지 않습니다: {set(row.keys())} != {expected_keys}")
    return self


class CaseMetric(CamelModel):
  label: str
  value: str


class CaseCard(CamelModel):
  id: str
  title: str
  subtitle: str | None = None
  body: str
  badge: str | None = None
  metrics: list[CaseMetric] = Field(default_factory=list)
  source_id: str | None = Field(default=None, alias="sourceId")


class CasesSection(CamelModel):
  type: Literal["cases"] = "cases"
  title: str
  cards: list[CaseCard]


class InsightsSection(CamelModel):
  type: Literal["insights"] = "insights"
  title: str | None = None
  insights: list[Insight]


class WordCloudSection(CamelModel):
  type: Literal["wordcloud"] = "wordcloud"
  title: str
  words: list[WordCloudItem]


class NoticeSection(CamelModel):
  """데이터가 아직 없거나 표본이 작을 때 화면에 안내를 띄우는 섹션.
  가짜 데이터로 채우는 대신 이 섹션으로 "무엇을 실행하면 채워지는지"를 알려준다."""

  type: Literal["notice"] = "notice"
  tone: Literal["info", "warning"] = "info"
  message: str


Section = Annotated[
  Union[
    StatsSection,
    ChartSection,
    TableSection,
    CasesSection,
    InsightsSection,
    WordCloudSection,
    NoticeSection,
  ],
  Field(discriminator="type"),
]


class PageData(CamelModel):
  generated_at: datetime = Field(alias="generatedAt")
  title: str
  summary: str | None = None
  sections: list[Section]


# ---------------------------------------------------------------------------
# sources.json — 출처 레지스트리 (모든 지표의 sourceId가 가리키는 대상)
# ---------------------------------------------------------------------------
class Source(CamelModel):
  id: str
  org: str
  title: str
  url: str | None = None
  year: int | None = None
  note: str | None = None
  # 이 출처를 인용한 페이지 slug 목록 — 파이프라인이 역참조로 채운다
  used_by: list[str] = Field(default_factory=list, alias="usedBy")


class SourcesData(CamelModel):
  generated_at: datetime = Field(alias="generatedAt")
  sources: list[Source]
