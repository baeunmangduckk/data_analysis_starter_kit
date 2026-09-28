"""출처 레지스트리(pipeline/curated/sources.yaml) 로드, 참조 검증, sources.json 생성.

원칙: 화면에 나가는 모든 수치는 출처를 가져야 한다. 그래서 페이지가 인용한 sourceId가
레지스트리에 없으면 조용히 넘어가지 않고 etl 전체를 중단한다(저장은 검증이 모두 끝난
뒤에만 하므로 기존 public/data/*.json은 손상되지 않는다).
"""

from __future__ import annotations

import re

from pipeline.common import CURATED_DIR, load_yaml, now
from pipeline.models import (
  CasesSection,
  ChartSection,
  PageData,
  Source,
  SourcesData,
  StatsSection,
  TableSection,
)

# 화면 라벨이 아니라 코드 키이므로 소문자·숫자·하이픈만 허용한다 (예: ifpi-gmr-2026).
SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class SourceRegistryError(ValueError):
  """출처 레지스트리 정의나 참조가 잘못됐을 때 발생한다."""


def load_sources() -> dict[str, Source]:
  """sources.yaml을 읽어 id → Source 사전으로 돌려준다. 순서는 파일 순서를 유지한다."""
  data = load_yaml(CURATED_DIR / "sources.yaml")
  registry: dict[str, Source] = {}
  for row in data.get("sources", []):
    source = Source.model_validate(row)  # legacy_id 같은 참고용 필드는 무시된다
    if not SOURCE_ID_PATTERN.match(source.id):
      raise SourceRegistryError(f"출처 id는 소문자·숫자·하이픈 slug여야 합니다: {source.id!r}")
    if source.id in registry:
      raise SourceRegistryError(f"출처 id가 중복됩니다: {source.id!r}")
    registry[source.id] = source
  return registry


def collect_source_ids(page: PageData) -> set[str]:
  """한 페이지의 섹션들이 인용한 sourceId를 모두 모은다."""
  ids: set[str] = set()
  for section in page.sections:
    if isinstance(section, StatsSection):
      ids.update(stat.source_id for stat in section.stats if stat.source_id)
    elif isinstance(section, (ChartSection, TableSection)):
      ids.update(section.source_ids)
    elif isinstance(section, CasesSection):
      ids.update(card.source_id for card in section.cards if card.source_id)
  return ids


def validate_refs(pages: dict[str, PageData], registry: dict[str, Source]) -> None:
  """페이지가 인용한 모든 sourceId가 레지스트리에 있는지 확인한다."""
  problems = [
    f"  - {slug}: {sorted(missing)}"
    for slug, page in pages.items()
    if (missing := collect_source_ids(page) - registry.keys())
  ]
  if problems:
    raise SourceRegistryError(
      "sources.yaml에 없는 sourceId를 인용한 페이지가 있습니다:\n" + "\n".join(problems)
    )


def build_sources(pages: dict[str, PageData], registry: dict[str, Source]) -> SourcesData:
  """레지스트리 전체에 "어느 페이지가 인용했는지(usedBy)"를 역참조로 채워 sources.json을 만든다."""
  used_by: dict[str, list[str]] = {source_id: [] for source_id in registry}
  for slug, page in pages.items():
    for source_id in collect_source_ids(page):
      used_by[source_id].append(slug)

  sources = [
    source.model_copy(update={"used_by": sorted(used_by[source.id])}) for source in registry.values()
  ]
  return SourcesData(generated_at=now(), sources=sources)
