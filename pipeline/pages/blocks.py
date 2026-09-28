"""여러 페이지가 공유하는 섹션 조립 헬퍼.

pages/*.py의 build()가 curated 행(Indicator 등)을 화면 섹션(KpiMetric, ChartSection 등)으로
바꿀 때 쓴다. 페이지마다 같은 변환을 반복하지 않도록 한 곳에 모았다.
"""

from __future__ import annotations

from pipeline.curated_schema import CaseStudy, Indicator
from pipeline.models import (
  CaseCard,
  CaseMetric,
  CasesSection,
  ChartKind,
  ChartSection,
  GoodDirection,
  KpiMetric,
  TimeseriesSeries,
  TrendDirection,
)


def unique(items: list[str]) -> list[str]:
  """순서를 유지한 채 중복을 제거한다 (출처 id 목록 등)."""
  return list(dict.fromkeys(items))


def trend_of(delta: float) -> TrendDirection:
  return "up" if delta > 0 else "down" if delta < 0 else "flat"


def indicator_stat(row: Indicator, good_direction: GoodDirection | None = None) -> KpiMetric:
  """curated 지표 한 건을 stats 섹션의 카드로 바꾼다. 값이 없는 정성 지표는 0으로 두지 않고
  호출 쪽에서 걸러야 하므로, value가 None이면 예외를 낸다."""
  if row.value is None:
    raise ValueError(f"stats로 만들 수 없는 정성 지표입니다 (value 없음): {row.key}")
  return KpiMetric(
    id=row.key,
    label=row.label,
    value=row.value,
    unit=row.unit,
    note=row.note,
    source_id=row.source,
    as_of=row.as_of,
    good_direction=good_direction,
    confidence=row.confidence,
  )


def group_chart(
  rows: list[Indicator],
  *,
  title: str,
  caption: str,
  series_label: str,
  kind: ChartKind = "barH",
) -> ChartSection:
  """지표 여러 개를 "구분(short_label) → 값" 한 시리즈 막대 차트로 만든다 (단위는 첫 행 기준)."""
  return ChartSection(
    title=title,
    caption=caption,
    kind=kind,
    x_key="group",
    series=[TimeseriesSeries(key="value", label=series_label)],
    points=[{"group": row.short_label or row.label, "value": row.value} for row in rows],
    unit=rows[0].unit,
    source_ids=unique([row.source for row in rows]),
  )


def case_section(title: str, studies: list[CaseStudy]) -> CasesSection:
  return CasesSection(
    title=title,
    cards=[
      CaseCard(
        id=study.key,
        title=study.title,
        subtitle=study.subtitle,
        body=study.body,
        badge=study.badge,
        metrics=[CaseMetric(label=metric.label, value=metric.value) for metric in study.metrics],
        source_id=study.source,
      )
      for study in studies
    ],
  )
