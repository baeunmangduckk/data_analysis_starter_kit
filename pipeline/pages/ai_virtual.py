"""AI·버추얼 아이돌 페이지(ai-virtual.json) — 버추얼 시장 규모 전망, 팬덤 플랫폼 지표, 사례.

데이터는 pipeline/curated/ai_virtual.yaml이다. 시장 규모 전망 경로는 파이프라인이
2025년 규모와 CAGR로 계산한다.
"""

from __future__ import annotations

from pipeline.common import CURATED_DIR, load_yaml, now
from pipeline.curated_schema import CaseStudy, CuratedModel, Indicator, load_rows
from pipeline.models import (
  ChartSection,
  Insight,
  InsightsSection,
  NoticeSection,
  PageData,
  Section,
  StatsSection,
  TimeseriesSeries,
)
from pipeline.pages.blocks import case_section, indicator_stat, unique

FILE = "ai_virtual.yaml"
TITLE = "AI·버추얼 아이돌"


class MarketForecast(CuratedModel):
  base_year: int
  target_year: int
  cagr_pct: float


def _forecast_chart(base_row: Indicator, forecast: MarketForecast) -> ChartSection:
  """2025년 규모에서 CAGR을 복리로 적용한 연도별 추정 경로. 실측이 아니라 전망 계산값이다."""
  base_value = base_row.value or 0.0
  years = range(forecast.base_year, forecast.target_year + 1)
  return ChartSection(
    title="버추얼 아이돌·버튜버 시장 규모 전망 경로",
    caption=f"{forecast.base_year}년 규모와 CAGR {forecast.cagr_pct:g}%를 복리로 적용한 추정 경로 (단위 {base_row.unit}). 연도별 실측값이 아닙니다",
    kind="line",
    x_key="year",
    series=[TimeseriesSeries(key="value", label="시장 규모(추정 경로)")],
    points=[
      {"year": str(year), "value": round(base_value * (1 + forecast.cagr_pct / 100) ** (year - forecast.base_year), 1)}
      for year in years
    ],
    unit=base_row.unit,
    source_ids=unique([base_row.source]),
  )


def build() -> PageData:
  indicators: list[Indicator] = load_rows(FILE, "indicators", Indicator)
  cases: list[CaseStudy] = load_rows(FILE, "cases", CaseStudy)
  forecast_raw = load_yaml(CURATED_DIR / FILE).get("virtual_market_forecast")
  forecast = MarketForecast.model_validate(forecast_raw) if forecast_raw else None

  by_key = {row.key: row for row in indicators}
  virtual = [row for row in indicators if row.category == "virtual_idol"]
  fandom = [row for row in indicators if row.category == "fandom_platform"]

  sections: list[Section] = []
  insights: list[Insight] = []

  if virtual:
    sections.append(StatsSection(title="버추얼 아이돌 시장", stats=[indicator_stat(row) for row in virtual]))
  if forecast is not None and "virtual_idol_market_2025" in by_key:
    sections.append(_forecast_chart(by_key["virtual_idol_market_2025"], forecast))
  if fandom:
    sections.append(StatsSection(title="팬덤 플랫폼 (성숙·성장 단계)", stats=[indicator_stat(row) for row in fandom]))
  if cases:
    sections.append(case_section("버추얼·AI 그룹 사례", cases))

  share = by_key.get("ai_group_revenue_share")
  if share is not None and share.value is not None:
    insights.append(
      Insight(
        id="ai_group_share",
        severity="info",
        text=f"K-pop 산업 전체 매출에서 AI 그룹이 차지하는 비중은 {share.value:g}%로 아직 초기 단계지만, 시장 규모는 연 {forecast.cagr_pct:g}% 성장이 전망됩니다."
        if forecast
        else f"K-pop 산업 전체 매출에서 AI 그룹이 차지하는 비중은 {share.value:g}%로 아직 초기 단계입니다.",
      )
    )
  if insights:
    sections.append(InsightsSection(title="핵심 포인트", insights=insights))

  if not sections:
    sections.append(NoticeSection(tone="warning", message="pipeline/curated/ai_virtual.yaml에 데이터가 없습니다."))

  return PageData(
    generated_at=now(),
    title=TITLE,
    summary="팬덤 플랫폼은 성숙 단계, 버추얼 아이돌은 아직 초기 단계",
    sections=sections,
  )
