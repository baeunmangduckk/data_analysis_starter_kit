"""기획사 재무 페이지(finance.json) — DART 사업보고서 실데이터로 상장 4사를 비교한다.

분석가는 이 파일의 build()만 보면 된다: 집계는 pipeline/derived/finance.py, 화면 구성은
아래 sections 목록이다. 섹션을 추가/삭제하면 화면이 그대로 따라 바뀐다.
"""

from __future__ import annotations

import polars as pl

from pipeline.common import now, to_wide, topic
from pipeline.derived.finance import (
  OPERATING_PROFIT,
  REVENUE,
  latest_year,
  load_agency_targets,
  load_dart_financials,
  summarize_totals,
  with_operating_margin,
  yoy_pct,
)
from pipeline.curated_schema import load_indicators
from pipeline.models import (
  ChartSection,
  Insight,
  InsightsSection,
  KpiMetric,
  NoticeSection,
  PageData,
  Section,
  StatsSection,
  TableColumn,
  TableSection,
)

from pipeline.pages.blocks import group_chart

SOURCE_ID = "opendart-fnltt"
TITLE = "기획사 재무"


def _trend(delta: float) -> str:
  return "up" if delta > 0 else "down" if delta < 0 else "flat"


def _stat(metric_id: str, label: str, value: float, previous: float, unit: str, year: int, note: str) -> KpiMetric:
  delta = value - previous
  return KpiMetric(
    id=metric_id,
    label=label,
    value=round(value, 1),
    unit=unit,
    delta=round(delta, 1),
    trend=_trend(delta),
    note=note,
    source_id=SOURCE_ID,
    as_of=str(year),
    good_direction="up",
    confidence="verified",
  )


def _build_insights(agencies: list[tuple[str, str]], lookup: dict[tuple[str, int], dict], year: int) -> list[Insight]:
  """최신 연도 기준 규칙 기반 인사이트: 매출 대비 수익성 변화와 영업이익률 1위."""
  insights: list[Insight] = []
  best: tuple[str, float] | None = None

  for agency, label in agencies:
    current, previous = lookup.get((agency, year)), lookup.get((agency, year - 1))
    if not current or not previous:
      continue
    revenue_yoy = yoy_pct(current[REVENUE], previous[REVENUE])
    margin, previous_margin = current["margin"], previous["margin"]

    if margin is not None and (best is None or margin > best[1]):
      best = (label, margin)
    if revenue_yoy is None or margin is None or previous_margin is None:
      continue

    if revenue_yoy > 0 and margin < previous_margin:
      insights.append(
        Insight(
          id=f"finance_{agency}_margin_down",
          severity="warning",
          text=f"{topic(label)} 매출이 {revenue_yoy:.1f}% 늘었지만 영업이익률은 {previous_margin:.1f}%에서 {margin:.1f}%로 낮아졌습니다 (수익성 악화).",
        )
      )
    elif revenue_yoy > 0 and margin > previous_margin:
      insights.append(
        Insight(
          id=f"finance_{agency}_margin_up",
          severity="positive",
          text=f"{topic(label)} 매출 {revenue_yoy:+.1f}% 성장과 함께 영업이익률이 {previous_margin:.1f}%에서 {margin:.1f}%로 개선됐습니다.",
        )
      )
    elif revenue_yoy < 0:
      insights.append(
        Insight(
          id=f"finance_{agency}_revenue_down",
          severity="warning",
          text=f"{label}의 매출이 전년 대비 {revenue_yoy:.1f}% 감소했습니다.",
        )
      )

  if best is not None:
    insights.append(
      Insight(id="finance_best_margin", severity="info", text=f"{year}년 영업이익률 1위는 {best[0]}({best[1]:.1f}%)입니다.")
    )
  return insights


def build() -> PageData:
  financials = load_dart_financials()
  year = latest_year(financials)

  if year is None:
    return PageData(
      generated_at=now(),
      title=TITLE,
      summary="DART 사업보고서 기반 상장 4사 실적 비교",
      sections=[NoticeSection(tone="warning", message="DART 수집 데이터가 없습니다. npm run collect:dart를 먼저 실행하세요.")],
    )

  targets = load_agency_targets()
  present = set(financials["agency"].unique().to_list())
  agencies = [(name, label) for name, label in targets if name in present]
  margins = with_operating_margin(financials)
  lookup = {(row["agency"], row["year"]): row for row in margins.to_dicts()}

  sections: list[Section] = []

  missing = [label for name, label in targets if name not in present]
  if missing:
    sections.append(
      NoticeSection(tone="warning", message=f"수집되지 않은 회사가 있습니다: {', '.join(missing)}. npm run collect:dart를 실행하세요.")
    )

  # 1) 합산 KPI — 대상 회사가 모두 있을 때만 (일부만 합치면 왜곡된다)
  totals = summarize_totals(financials, expected_agencies=len(targets))
  if totals is not None:
    revenue, previous_revenue = totals[REVENUE]
    profit, previous_profit = totals[OPERATING_PROFIT]
    sections.append(
      StatsSection(
        title=f"{year}년 상장 {len(targets)}사 합산 (연결)",
        stats=[
          _stat("finance_revenue", "합산 매출액", revenue, previous_revenue, "억 원", year, "전년 대비 증감"),
          _stat("finance_operating_profit", "합산 영업이익", profit, previous_profit, "억 원", year, "전년 대비 증감"),
          _stat(
            "finance_operating_margin",
            "합산 영업이익률",
            profit / revenue * 100,
            previous_profit / previous_revenue * 100,
            "%",
            year,
            "합산 영업이익 ÷ 합산 매출액, 증감은 %p",
          ),
        ],
      )
    )

  # 2) 회사별 추이 차트 — 사업보고서 한 건의 3개년(당기·전기·전전기)
  series_order = agencies
  revenue_series, revenue_points = to_wide(
    financials.filter(pl.col("account") == REVENUE), "year", "agency", "amount", series_order
  )
  profit_series, profit_points = to_wide(
    financials.filter(pl.col("account") == OPERATING_PROFIT), "year", "agency", "amount", series_order
  )
  margin_series, margin_points = to_wide(
    margins.filter(pl.col("margin").is_not_null()), "year", "agency", "margin", series_order
  )

  sections.extend(
    [
      ChartSection(
        title="회사별 매출액",
        caption="연결 기준, 단위 억 원",
        kind="column",
        x_key="year",
        series=revenue_series,
        points=revenue_points,
        unit="억 원",
        source_ids=[SOURCE_ID],
      ),
      ChartSection(
        title="회사별 영업이익",
        caption="연결 기준, 단위 억 원 (적자는 음수)",
        kind="column",
        x_key="year",
        series=profit_series,
        points=profit_points,
        unit="억 원",
        source_ids=[SOURCE_ID],
      ),
      ChartSection(
        title="회사별 영업이익률",
        caption="영업이익 ÷ 매출액, 단위 %",
        kind="line",
        x_key="year",
        series=margin_series,
        points=margin_points,
        unit="%",
        source_ids=[SOURCE_ID],
      ),
    ]
  )

  # 3) 최신 연도 요약 표
  rows: list[dict[str, str | float | None]] = []
  for agency, label in agencies:
    current, previous = lookup.get((agency, year)), lookup.get((agency, year - 1))
    if not current:
      continue

    def rounded(value: float | None) -> float | None:
      return None if value is None else round(value, 1)

    rows.append(
      {
        "agency": label,
        "revenue": rounded(current[REVENUE]),
        "operating_profit": rounded(current[OPERATING_PROFIT]),
        "margin": rounded(current["margin"]),
        "revenue_yoy": rounded(yoy_pct(current[REVENUE], previous[REVENUE]) if previous else None),
        "operating_profit_yoy": rounded(yoy_pct(current[OPERATING_PROFIT], previous[OPERATING_PROFIT]) if previous else None),
      }
    )

  sections.append(
    TableSection(
      title=f"{year}년 실적 요약",
      caption="금액은 억 원, 증감률·영업이익률은 %. 전년 영업이익이 적자이면 증감률은 표시하지 않습니다.",
      columns=[
        TableColumn(key="agency", label="회사"),
        TableColumn(key="revenue", label="매출액(억 원)", align="right"),
        TableColumn(key="operating_profit", label="영업이익(억 원)", align="right"),
        TableColumn(key="margin", label="영업이익률(%)", align="right"),
        TableColumn(key="revenue_yoy", label="매출 증감(%)", align="right"),
        TableColumn(key="operating_profit_yoy", label="영업이익 증감(%)", align="right"),
      ],
      rows=rows,
      source_ids=[SOURCE_ID],
    )
  )

  # 4) 큐레이션 지표(시가총액·1분기 매출) — DART가 다루지 않는 시장 평가와 최신 분기 격차
  extras = load_indicators("agency_metrics.yaml")
  market_cap = [row for row in extras if row.category == "market_cap"]
  q1_revenue = [row for row in extras if row.category == "q1_revenue"]
  if market_cap:
    sections.append(
      group_chart(market_cap, title="상장 4사 시가총액", caption="2025-10-23 기준, 단위 억 원", series_label="시가총액")
    )
  if q1_revenue:
    sections.append(
      group_chart(
        q1_revenue,
        title="2026년 1분기 상장 기획사 매출",
        caption="대형과 중소 기획사의 격차, 단위 억 원. 레거시 단위 표기를 보정한 추정치입니다",
        series_label="1분기 매출",
      )
    )

  insights = _build_insights(agencies, lookup, year)
  if insights:
    sections.append(InsightsSection(title="핵심 포인트", insights=insights))

  return PageData(
    generated_at=now(),
    title=TITLE,
    summary=f"{year}년 사업보고서 기준 상장 {len(targets)}사 연결 실적 (하이브·SM·YG·JYP)",
    sections=sections,
  )
