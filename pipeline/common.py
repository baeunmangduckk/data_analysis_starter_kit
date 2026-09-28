"""etl.py와 pipeline/pages/*.py가 함께 쓰는 작은 공용 유틸.

이 모듈도 etl.py처럼 네트워크/API 키(pipeline/config.py)를 import하지 않는다 —
`npm run etl`이 항상 오프라인으로 동작해야 하기 때문이다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import polars as pl
import yaml

from pipeline.models import TimeseriesSeries

# 경로 상수는 API 키를 읽는 pipeline/config.py(.env 로드)가 아니라 여기서 정의한다.
# config.py도 이 값을 가져다 쓰므로 경로는 한 곳에서만 관리된다.
PIPELINE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PIPELINE_DIR.parent
RAW_DIR = PIPELINE_DIR / "raw"
CURATED_DIR = PIPELINE_DIR / "curated"


def to_wide(
  long: pl.DataFrame,
  x_col: str,
  series_col: str,
  value_col: str,
  series_order: list[tuple[str, str]],
) -> tuple[list[TimeseriesSeries], list[dict[str, str | float | None]]]:
  """long 표(x, 시리즈, 값)를 차트 섹션이 바로 쓰는 (series, wide points)로 바꾼다.

  series_order는 [(key, label)] 목록이며 색 배정 순서이자 범례 순서다. 표에 없는
  시리즈는 빠지고, 값이 없는 칸은 None(결측)으로 남겨 화면에서 선이 끊기게 한다."""
  wide = long.pivot(on=series_col, index=x_col, values=value_col).sort(x_col)
  present = [(key, label) for key, label in series_order if key in wide.columns]

  points: list[dict[str, str | float | None]] = []
  for row in wide.to_dicts():
    point: dict[str, str | float | None] = {x_col: str(row[x_col])}
    for key, _ in present:
      value = row[key]
      point[key] = None if value is None else round(float(value), 2)
    points.append(point)

  return [TimeseriesSeries(key=key, label=label) for key, label in present], points


def topic(word: str) -> str:
  """주제 조사 은/는을 붙인 문자열 ("하이브" → "하이브는", "출판" → "출판은").
  마지막 글자가 한글이 아니면 발음을 알 수 없어 "는"으로 통일한다."""
  last = word.strip()[-1]
  if "가" <= last <= "힣" and (ord(last) - 0xAC00) % 28 != 0:
    return f"{word}은"
  return f"{word}는"


def now() -> datetime:
  return datetime.now().astimezone()


def load_yaml(path: Path) -> dict:
  """YAML을 읽어 dict로 돌려준다. 파일이 없으면 빈 dict (호출 쪽이 폴백/빈 섹션 처리)."""
  if not path.exists():
    return {}
  return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
