"""판매 집중도·양극화 페이지(concentration.json).

- 판매 집중도 15년 시계열: pipeline/curated/sales_concentration.yaml (Circle Chart Top100 전수 집계)
- 양극화(제작비·해외공연·판매 티어·생존율)와 지속가능성 리스크: pipeline/curated/polarization.yaml

분석가는 build()의 sections 목록만 보면 된다. 섹션을 추가/삭제하면 화면이 그대로 따라 바뀐다.
"""

from __future__ import annotations

import polars as pl

from pipeline.common import now, to_wide
from pipeline.curated_schema import (
  ConcentrationSeries,
  Indicator,
  Risk,
  load_concentration_series,
  load_indicators,
  load_risks,
)
from pipeline.pages.blocks import group_chart, indicator_stat, trend_of
from pipeline.models import (
  CaseCard,
  CaseMetric,
  CasesSection,
  ChartSection,
  Insight,
  InsightsSection,
  KpiMetric,
  NoticeSection,
  PageData,
  Section,
  StatsSection,
)

TITLE = "판매 집중도·양극화"
POLARIZATION_FILE = "polarization.yaml"

RISK_LABEL = {"high": "위험", "medium": "주의", "low": "낮음", "positive": "긍정"}


def _year_chart(
  series: ConcentrationSeries,
  *,
  title: str,
  caption: str,
  kind: str,
  metrics: list[tuple[str, str]],
  unit: str | None,
) -> ChartSection:
  """연도별 시계열 차트. metrics는 [(ConcentrationYear 필드명, 범례 라벨)] — 색 배정 순서."""
  rows = [
    {"year": year.year, "metric": field, "value": getattr(year, field)}
    for year in series.years
    for field, _ in metrics
  ]
  chart_series, points = to_wide(pl.DataFrame(rows), "year", "metric", "value", metrics)
  return ChartSection(
    title=title,
    caption=caption,
    kind=kind,
    x_key="year",
    series=chart_series,
    points=points,
    unit=unit,
    source_ids=[series.source],
  )


def _concentration_insights(series: ConcentrationSeries) -> list[Insight]:
  """최신 연도의 점유율·Gini·총 판매량 변화를 규칙 기반으로 문장화한다."""
  years = series.years
  if len(years) < 2:
    return []
  current, previous = years[-1], years[-2]
  insights: list[Insight] = []

  # 점유율이 낮아질수록 여러 앨범에 고르게 분산된 것이므로 "하락=긍정"이다.
  diff = current.top10_share_pct - previous.top10_share_pct
  insights.append(
    Insight(
      id="concentration_top10_change",
      severity="positive" if diff < 0 else "warning",
      text=f"{current.year}년 Top 10 점유율은 {current.top10_share_pct:.1f}%로 전년({previous.top10_share_pct:.1f}%) 대비 {abs(diff):.1f}%p {'하락' if diff < 0 else '상승'}했습니다.",
    )
  )

  lowest_gini = min(years, key=lambda row: row.gini)
  if lowest_gini.year == current.year:
    insights.append(
      Insight(
        id="concentration_gini_lowest",
        severity="positive",
        text=f"Gini 계수 {current.gini:.3f}는 {years[0].year}년 이후 관측 기간 중 가장 낮아, 판매 쏠림이 완화되는 추세입니다.",
      )
    )

  peak = max(years, key=lambda row: row.top10_share_pct)
  insights.append(
    Insight(
      id="concentration_top10_peak",
      severity="info",
      text=f"Top 10 점유율 최고치는 {peak.year}년의 {peak.top10_share_pct:.1f}%였고, 현재는 그보다 {peak.top10_share_pct - current.top10_share_pct:.1f}%p 낮습니다.",
    )
  )

  total_change = (current.total_top100_sales - previous.total_top100_sales) / previous.total_top100_sales * 100
  insights.append(
    Insight(
      id="concentration_total_sales",
      severity="warning" if total_change < 0 else "positive",
      text=f"{current.year}년 Top100 총 판매량은 {current.total_top100_sales / 10000:,.0f}만 장으로 전년 대비 {total_change:+.1f}%였습니다.",
    )
  )
  return insights


def _risk_cards(risks: list[Risk]) -> CasesSection:
  cards = []
  for risk in risks:
    metrics = [CaseMetric(label="수치", value=f"{risk.value:,g} {risk.unit or ''}".strip())] if risk.value is not None else []
    cards.append(
      CaseCard(
        id=risk.key,
        title=risk.label,
        subtitle=f"기준 {risk.as_of}",
        body=risk.note,
        badge=RISK_LABEL[risk.risk_level],
        metrics=metrics,
        source_id=risk.source,
      )
    )
  return CasesSection(title="지속가능성 리스크·기회 신호", cards=cards)


def build() -> PageData:
  series = load_concentration_series()
  indicators = load_indicators(POLARIZATION_FILE)
  risks = load_risks(POLARIZATION_FILE)
  by_category: dict[str, list[Indicator]] = {}
  for row in indicators:
    by_category.setdefault(row.category, []).append(row)

  sections: list[Section] = []

  if series is None:
    sections.append(NoticeSection(tone="warning", message="pipeline/curated/sales_concentration.yaml이 없어 집중도 시계열을 만들 수 없습니다."))
  else:
    current, previous = series.years[-1], series.years[-2]
    sections.append(
      NoticeSection(
        tone="info",
        message=f"판매량 지표는 Circle Chart 연간 앨범 판매량 Top100 전수 집계({series.years[0].year}~{current.year})입니다. "
        "유통사(de_nm) 정보는 실제 소속사가 아니어서 소속사별 분석은 하지 않습니다.",
      )
    )
    sections.append(
      StatsSection(
        title=f"{current.year}년 판매 집중도",
        stats=[
          _concentration_stat("concentration_top10", "Top 10 앨범 판매 점유율", current.top10_share_pct, previous.top10_share_pct, "%", series, "down", "낮을수록 판매가 여러 앨범에 분산"),
          _concentration_stat("concentration_gini", "판매량 집중도 (Gini)", current.gini, previous.gini, None, series, "down", "0=완전 균등, 1=완전 쏠림"),
          _concentration_stat("concentration_total", "Top100 총 판매량", current.total_top100_sales, previous.total_top100_sales, "장", series, "up", "Top100 앨범 판매량 합계"),
        ],
      )
    )
    sections.extend(
      [
        _year_chart(
          series,
          title="Top 앨범 판매 점유율 추이",
          caption="Top100 총 판매량 대비 비중(%). Top 10·20이 낮아지고 하위 50위 비중이 오르면 분산되는 것",
          kind="line",
          metrics=[("top10_share_pct", "Top 10"), ("top20_share_pct", "Top 20"), ("bottom50_share_pct", "하위 50 (51~100위)")],
          unit="%",
        ),
        _year_chart(
          series,
          title="판매량 지니계수 추이",
          caption="0에 가까울수록 고르게 분산, 1에 가까울수록 소수 앨범에 쏠림",
          kind="line",
          metrics=[("gini", "Gini 계수")],
          unit=None,
        ),
        _year_chart(
          series,
          title="1위 vs 100위 앨범 판매량",
          caption="단위 장. 1위와 100위의 격차가 곧 양극화의 크기",
          kind="line",
          metrics=[("number1_sales", "1위"), ("rank100_sales", "100위")],
          unit="장",
        ),
        _year_chart(
          series,
          title="Top100 총 판매량",
          caption="단위 장",
          kind="column",
          metrics=[("total_top100_sales", "Top100 총 판매량")],
          unit="장",
        ),
      ]
    )
    insights = _concentration_insights(series)
    if insights:
      sections.append(InsightsSection(title="집중도 핵심 포인트", insights=insights))

  # ── 양극화: 대기업 vs 중소기업 ──
  polarization_stats = [
    indicator_stat(row)
    for key in ("gov_support", "survival_summary")
    for row in by_category.get(key, [])
  ] + [indicator_stat(row) for row in by_category.get("album_cost", [])]
  if polarization_stats:
    sections.append(StatsSection(title="양극화·지원 지표", stats=polarization_stats))

  group_charts = [
    ("production_cost", "연평균 음악 제작비 (대기업 vs 중소기업)", "단위 억 원, 2023년 기준", "제작비"),
    ("overseas_concerts", "연평균 해외 공연 횟수 (대기업 vs 중소기업)", "단위 회/년, 2023년 기준", "공연 횟수"),
    ("sales_tier", "판매 티어별 그룹 비율", "1996~2025년 데뷔 아이돌 그룹 1,182개 중 해당 판매량 이상 도달 비율(%)", "그룹 비율"),
  ]
  for category, title, caption, series_label in group_charts:
    rows = by_category.get(category, [])
    if rows:
      sections.append(group_chart(rows, title=title, caption=caption, series_label=series_label))

  survival = by_category.get("survival", [])
  if survival:
    sections.append(
      group_chart(survival, title="데뷔 후 그룹 생존율", caption="1996~2025년 데뷔 그룹 기준, 데뷔 N년 뒤에도 활동 중인 비율(%)", series_label="생존율", kind="column")
    )

  if risks:
    sections.append(_risk_cards(risks))

  return PageData(
    generated_at=now(),
    title=TITLE,
    summary="판매량은 분산되는데 기획사·그룹 간 격차는 여전히 극심합니다",
    sections=sections,
  )


def _concentration_stat(
  metric_id: str,
  label: str,
  value: float,
  previous: float,
  unit: str | None,
  series: ConcentrationSeries,
  good_direction: str,
  note: str,
) -> KpiMetric:
  delta = value - previous
  return KpiMetric(
    id=metric_id,
    label=label,
    value=value,
    unit=unit,
    delta=round(delta, 4),
    trend=trend_of(delta),
    note=note,
    source_id=series.source,
    as_of=str(series.years[-1].year),
    good_direction=good_direction,
    confidence=series.confidence,
  )
