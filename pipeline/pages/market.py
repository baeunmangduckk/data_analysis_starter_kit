"""시장 전망 페이지(market.json) — 글로벌 음반 매출, 앨범 수출 추이, 콘서트 시장 전망.

데이터는 pipeline/curated/market_outlook.yaml(레거시 이관, 출처·기준시점 필수)이다.
분석가는 build()의 sections 목록만 보면 된다.
"""

from __future__ import annotations

from pipeline.common import now
from pipeline.curated_schema import ConcertForecast, Indicator, YearSeries, load_document, load_rows
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
from pipeline.pages.blocks import indicator_stat

FILE = "market_outlook.yaml"
TITLE = "시장 전망"


def _export_charts(exports: YearSeries) -> tuple[list[ChartSection], list[int]]:
  """앨범 수출액과 증감률 차트. 원자료에 없는 연도는 None(결측)으로 채워 선이 끊기게 한다."""
  by_year = {row.year: row for row in exports.rows}
  years = range(min(by_year), max(by_year) + 1)
  missing = [year for year in years if year not in by_year]

  level = ChartSection(
    title="K팝 음반·DVD 수출액 추이",
    caption="관세청 통계 기반, 단위 백만 달러. 원자료에 없는 연도는 끊김으로 표시",
    kind="line",
    x_key="year",
    series=[TimeseriesSeries(key="value", label="수출액")],
    points=[{"year": str(year), "value": by_year[year].value if year in by_year else None} for year in years],
    unit=exports.unit,
    source_ids=[exports.source],
  )
  growth = ChartSection(
    title="음반·DVD 수출 증가율",
    caption="전년 대비 %. 증가 폭이 빠르게 둔화되는 흐름",
    kind="column",
    x_key="year",
    series=[TimeseriesSeries(key="yoy", label="전년 대비 증가율")],
    points=[{"year": str(year), "yoy": by_year[year].yoy_pct if year in by_year else None} for year in years],
    unit="%",
    source_ids=[exports.source],
  )
  return [level, growth], missing


def _export_insights(exports: YearSeries) -> list[Insight]:
  with_yoy = [row for row in exports.rows if row.yoy_pct is not None]
  if len(with_yoy) < 2:
    return []
  first, last = with_yoy[0], with_yoy[-1]
  return [
    Insight(
      id="market_export_slowdown",
      severity="warning",
      text=f"음반·DVD 수출 증가율이 {first.year}년 {first.yoy_pct:+.1f}%에서 {last.year}년 {last.yoy_pct:+.1f}%로 급격히 둔화됐습니다 (앨범 수출 성장의 정체 신호).",
    )
  ]


def _forecast_chart(forecasts: list[ConcertForecast]) -> tuple[ChartSection, Insight]:
  detail = " · ".join(
    f"{item.label} {item.base_year}→{item.target_year} (CAGR {item.cagr_pct:g}%)" for item in forecasts
  )
  chart = ChartSection(
    title="K팝 이벤트(공연) 시장 전망",
    caption=f"조사기관별 기준 연도 규모와 전망 연도 규모, 단위 {forecasts[0].unit}. {detail}",
    kind="column",
    x_key="org",
    series=[
      TimeseriesSeries(key="base", label="기준 연도 규모"),
      TimeseriesSeries(key="target", label="전망 연도 규모"),
    ],
    points=[{"org": item.label, "base": item.base_value, "target": item.target_value} for item in forecasts],
    unit=forecasts[0].unit,
    source_ids=[item.source for item in forecasts],
  )
  low, high = min(item.cagr_pct for item in forecasts), max(item.cagr_pct for item in forecasts)
  insight = Insight(
    id="market_concert_cagr",
    severity="info",
    text=f"조사기관 {len(forecasts)}곳 모두 K팝 공연 시장이 연평균 {low:g}~{high:g}% 성장할 것으로 전망합니다.",
  )
  return chart, insight


def build() -> PageData:
  kpis: list[Indicator] = load_rows(FILE, "kpis", Indicator)
  exports = load_document(FILE, "album_exports", YearSeries)
  forecasts: list[ConcertForecast] = load_rows(FILE, "concert_forecasts", ConcertForecast)

  sections: list[Section] = []
  insights: list[Insight] = []

  if kpis:
    sections.append(StatsSection(title="시장 핵심 지표", stats=[indicator_stat(kpi) for kpi in kpis]))

  if exports is not None:
    charts, missing = _export_charts(exports)
    if missing:
      sections.append(
        NoticeSection(tone="warning", message=f"{', '.join(map(str, missing))}년 수출액은 원자료에 없어 차트에서 끊김으로 표시됩니다.")
      )
    sections.extend(charts)
    insights.extend(_export_insights(exports))

  if forecasts:
    chart, insight = _forecast_chart(forecasts)
    sections.append(chart)
    insights.append(insight)

  if insights:
    sections.append(InsightsSection(title="핵심 포인트", insights=insights))

  return PageData(
    generated_at=now(),
    title=TITLE,
    summary="사상 최고 실적과 앨범 수출 성장 둔화가 동시에 나타나는 시장",
    sections=sections,
  )
