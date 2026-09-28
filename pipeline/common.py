"""etl.py와 pipeline/pages/*.py가 함께 쓰는 작은 공용 유틸.

이 모듈도 etl.py처럼 네트워크/API 키(pipeline/config.py)를 import하지 않는다 —
`npm run etl`이 항상 오프라인으로 동작해야 하기 때문이다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

# 경로 상수는 API 키를 읽는 pipeline/config.py(.env 로드)가 아니라 여기서 정의한다.
# config.py도 이 값을 가져다 쓰므로 경로는 한 곳에서만 관리된다.
PIPELINE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PIPELINE_DIR.parent
RAW_DIR = PIPELINE_DIR / "raw"
CURATED_DIR = PIPELINE_DIR / "curated"


def now() -> datetime:
  return datetime.now().astimezone()


def load_yaml(path: Path) -> dict:
  """YAML을 읽어 dict로 돌려준다. 파일이 없으면 빈 dict (호출 쪽이 폴백/빈 섹션 처리)."""
  if not path.exists():
    return {}
  return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
