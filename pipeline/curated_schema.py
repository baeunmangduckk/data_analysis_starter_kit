"""pipeline/curated/*.yaml의 행을 검증하는 Pydantic 모델과 로더.

분석가가 손으로 입력하는 YAML은 오타와 누락이 가장 흔한 오류 원인이라, 읽는 즉시 검증해
문제가 있으면 etl 전체를 중단한다(조용히 넘어가 잘못된 수치가 화면에 나가는 것보다 낫다).

- extra="forbid": 키 오타(예: `sorce:`)를 잡아낸다.
- source(출처 id)와 as_of(기준 시점)는 모든 행에서 필수다. source가 sources.yaml에 실제로
  있는지는 pipeline/pages/sources.py의 validate_refs()가 페이지 조립 후 확인한다.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from pipeline.common import CURATED_DIR, load_yaml
from pipeline.models import Confidence


class CuratedDataError(ValueError):
  """curated YAML이 스키마에 맞지 않을 때 발생한다 (어느 파일의 몇 번째 행인지 포함)."""


class CuratedModel(BaseModel):
  # YAML의 2025 같은 숫자를 as_of(str)에 넣어도 통과시킨다.
  model_config = ConfigDict(extra="forbid", coerce_numbers_to_str=True)


class Indicator(CuratedModel):
  """카테고리별로 묶이는 단일 수치 (양극화 지표 등)."""

  key: str
  category: str
  label: str
  short_label: str | None = None  # 차트 축에 쓰는 짧은 이름 (없으면 label)
  value: float | None = None
  unit: str | None = None
  as_of: str
  source: str
  note: str | None = None
  confidence: Confidence | None = None


RiskLevel = Literal["high", "medium", "low", "positive"]


class Risk(CuratedModel):
  """지속가능성 리스크/기회 신호. value가 없는 정성 지표도 허용한다."""

  key: str
  label: str
  value: float | None = None
  unit: str | None = None
  as_of: str
  risk_level: RiskLevel
  source: str
  note: str
  confidence: Confidence | None = None


class ConcentrationYear(CuratedModel):
  """Circle Chart 연간 Top100 전수 집계 결과 (한 해 한 행)."""

  year: int
  top10_share_pct: float
  top20_share_pct: float
  bottom50_share_pct: float
  gini: float
  number1_sales: float
  rank100_sales: float
  total_top100_sales: float


class ConcentrationSeries(CuratedModel):
  source: str
  as_of: str
  confidence: Confidence | None = None
  years: list[ConcentrationYear]


class YearValue(CuratedModel):
  """연도별 단일 수치. value가 None이면 그 해는 결측(예: 2024년 통계 없음)이다."""

  year: int
  value: float | None = None
  yoy_pct: float | None = None


class YearSeries(CuratedModel):
  """한 출처에서 온 연도별 시계열 (파일 단위로 source/as_of/unit을 공유한다)."""

  source: str
  as_of: str
  unit: str | None = None
  confidence: Confidence | None = None
  rows: list[YearValue]


class RegionExport(CuratedModel):
  region: str
  year: int
  value: float


class RegionExportSeries(CuratedModel):
  source: str
  as_of: str
  unit: str | None = None
  confidence: Confidence | None = None
  rows: list[RegionExport]


class ConcertForecast(CuratedModel):
  """조사기관별 시장 전망 (기준 연도 → 전망 연도)."""

  label: str
  base_year: int
  base_value: float
  target_year: int
  target_value: float
  cagr_pct: float
  unit: str
  as_of: str
  source: str
  confidence: Confidence | None = None


class CaseMetricRow(CuratedModel):
  label: str
  value: str


class CaseStudy(CuratedModel):
  key: str
  title: str
  subtitle: str | None = None
  body: str
  badge: str | None = None
  metrics: list[CaseMetricRow] = []
  source: str
  as_of: str
  confidence: Confidence | None = None


def _validate_rows(filename: str, model: type[CuratedModel], rows: list[dict]) -> list:
  validated = []
  for index, row in enumerate(rows):
    try:
      validated.append(model.model_validate(row))
    except ValidationError as error:
      raise CuratedDataError(f"{filename} {index + 1}번째 항목이 잘못되었습니다:\n{error}") from error
  return validated


def load_indicators(filename: str) -> list[Indicator]:
  data = load_yaml(CURATED_DIR / filename)
  return _validate_rows(filename, Indicator, data.get("indicators", []))


def load_risks(filename: str) -> list[Risk]:
  data = load_yaml(CURATED_DIR / filename)
  return _validate_rows(filename, Risk, data.get("risks", []))


def load_concentration_series(filename: str = "sales_concentration.yaml") -> ConcentrationSeries | None:
  """파일이 없으면 None. 있으면 연도 오름차순으로 정렬해 돌려준다."""
  data = load_yaml(CURATED_DIR / filename)
  if not data:
    return None
  try:
    series = ConcentrationSeries.model_validate(data)
  except ValidationError as error:
    raise CuratedDataError(f"{filename}이 잘못되었습니다:\n{error}") from error
  series.years.sort(key=lambda row: row.year)
  return series


def load_rows(filename: str, key: str, model: type[CuratedModel]) -> list:
  """`<key>:` 아래의 행 목록을 model로 검증해 돌려준다. 파일이나 키가 없으면 빈 목록."""
  data = load_yaml(CURATED_DIR / filename)
  return _validate_rows(filename, model, data.get(key, []))


def load_document(filename: str, key: str, model: type[CuratedModel]):
  """`<key>:` 아래의 파일 단위 객체(source/as_of를 공유하는 시계열 등)를 검증해 돌려준다. 없으면 None."""
  data = load_yaml(CURATED_DIR / filename).get(key)
  if data is None:
    return None
  try:
    return model.model_validate(data)
  except ValidationError as error:
    raise CuratedDataError(f"{filename}의 {key}가 잘못되었습니다:\n{error}") from error
