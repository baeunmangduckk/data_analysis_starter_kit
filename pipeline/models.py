"""대시보드 JSON 데이터 계약(schema)을 정의하는 Pydantic 모델 모음.

pipeline/etl.py가 만든 결과를 이 모델로 검증한 뒤 public/data/*.json으로 저장한다.
각 모델은 src/types/dashboard.ts의 TypeScript 인터페이스와 1:1로 대응한다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TrendDirection = Literal["up", "down", "flat"]
InsightSeverity = Literal["info", "positive", "warning", "critical"]
SentimentLabel = Literal["positive", "negative", "neutral"]


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


class MetricsData(CamelModel):
  generated_at: datetime = Field(alias="generatedAt")
  metrics: list[KpiMetric]


# ---------------------------------------------------------------------------
# timeseries.json — 추이 그래프
# ---------------------------------------------------------------------------
class TimeseriesSeries(CamelModel):
  key: str
  label: str


class TimeseriesData(CamelModel):
  generated_at: datetime = Field(alias="generatedAt")
  series: list[TimeseriesSeries]
  # 날짜 + 시리즈별 값이 동적으로 섞이는 구조라 고정 필드 대신 dict로 받고,
  # 아래 검증기에서 series에 정의된 key와 실제로 일치하는지 확인한다.
  points: list[dict[str, str | float]]

  @model_validator(mode="after")
  def _validate_points_match_series(self) -> "TimeseriesData":
    expected_keys = {"date", *(s.key for s in self.series)}
    for point in self.points:
      if set(point.keys()) != expected_keys:
        raise ValueError(
          f"timeseries point 키가 series 정의와 일치하지 않습니다: {point.keys()} != {expected_keys}"
        )
    return self


# ---------------------------------------------------------------------------
# distribution.json — 비중 그래프
# ---------------------------------------------------------------------------
class DistributionCategory(CamelModel):
  category: str
  label: str
  value: float


class DistributionData(CamelModel):
  generated_at: datetime = Field(alias="generatedAt")
  title: str
  categories: list[DistributionCategory]


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
# wordcloud.json — 워드클라우드 + 감성분석
# ---------------------------------------------------------------------------
class WordCloudItem(CamelModel):
  text: str
  weight: float
  sentiment: SentimentLabel


class WordCloudData(CamelModel):
  generated_at: datetime = Field(alias="generatedAt")
  words: list[WordCloudItem]
