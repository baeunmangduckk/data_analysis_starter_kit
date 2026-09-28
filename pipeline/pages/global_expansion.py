"""글로벌 확장 페이지(global.json) — 중화권에서 북미로의 지역 재편과 신흥시장(중남미) 성장.

데이터는 pipeline/curated/global_expansion.yaml이다. 원자료가 4행뿐이라 소규모 페이지이며,
KOFICE 원자료를 확보하면 이 YAML을 넓혀 갱신한다.
"""

from __future__ import annotations

import polars as pl

from pipeline.common import now, to_wide
from pipeline.curated_schema import CaseStudy, Indicator, RegionExportSeries, load_document, load_rows
from pipeline.models import (
  ChartSection,
  Insight,
  InsightsSection,
  NoticeSection,
  PageData,
  Section,
  StatsSection,
)
from pipeline.pages.blocks import case_section, indicator_stat

FILE = "global_expansion.yaml"
TITLE = "글로벌 확장"


def _regional_chart(exports: RegionExportSeries) -> tuple[ChartSection, list[Insight]]:
  years = sorted({row.year for row in exports.rows})
  regions = list(dict.fromkeys(row.region for row in exports.rows))

  long = pl.DataFrame([{"region": row.region, "year": str(row.year), "value": row.value} for row in exports.rows])
  series, points = to_wide(long, "region", "year", "value", [(str(year), f"{year}년") for year in years])
  chart = ChartSection(
    title="지역별 방송콘텐츠 수출액 재편",
    caption=f"단위 {exports.unit}. 음악 직접 통계가 없어 방송콘텐츠 수출액을 프록시로 사용",
    kind="column",
    x_key="region",
    series=series,
    points=points,
    unit=exports.unit,
    source_ids=[exports.source],
  )

  # 첫 해 대비 마지막 해 증감률로 재편 방향을 문장화한다.
  values = {(row.region, row.year): row.value for row in exports.rows}
  insights: list[Insight] = []
  for region in regions:
    start, end = values.get((region, years[0])), values.get((region, years[-1]))
    if start and end:
      change = (end - start) / start * 100
      insights.append(
        Insight(
          id=f"global_{region}_change",
          severity="positive" if change > 0 else "warning",
          text=f"{region} 수출액은 {years[0]}년 {start:,.1f}에서 {years[-1]}년 {end:,.1f}(백만 달러)로 {change:+.1f}% 변했습니다.",
        )
      )
  return chart, insights


def build() -> PageData:
  exports = load_document(FILE, "regional_exports", RegionExportSeries)
  indicators: list[Indicator] = load_rows(FILE, "indicators", Indicator)
  cases: list[CaseStudy] = load_rows(FILE, "cases", CaseStudy)

  sections: list[Section] = [
    NoticeSection(
      tone="info",
      message="지역별 수치는 KOSIS 방송콘텐츠 수출 통계를 음악 수출의 프록시로 쓴 것이며, 데이터가 적어 소규모로 제공합니다. KOFICE 원자료를 확보하면 확장할 예정입니다.",
    )
  ]
  insights: list[Insight] = []

  if indicators:
    sections.append(StatsSection(title="신흥시장: 중남미 Weverse 성장", stats=[indicator_stat(row, "up") for row in indicators]))

  if exports is not None:
    chart, region_insights = _regional_chart(exports)
    sections.append(chart)
    insights.extend(region_insights)

  if cases:
    sections.append(case_section("유망 권역", cases))

  if insights:
    sections.append(InsightsSection(title="핵심 포인트", insights=insights))

  return PageData(
    generated_at=now(),
    title=TITLE,
    summary="중화권 편중에서 북미·신흥시장으로 무게중심이 옮겨가는 중",
    sections=sections,
  )
