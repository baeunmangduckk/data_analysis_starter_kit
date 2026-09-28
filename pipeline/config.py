"""환경 변수 및 경로 설정을 한 곳에서 관리한다.

pipeline/etl.py(Stage B, 변환)는 이 모듈을 가져오지 않는다 — API 키와
네트워크 관련 설정은 pipeline/collectors/*(Stage A, 수집)에서만 다룬다.
이렇게 분리해 두면 `npm run etl`이 자격증명 유무와 무관하게 항상
오프라인으로 동작함을 코드 구조로 보장할 수 있다.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from pipeline.common import CURATED_DIR, PIPELINE_DIR, RAW_DIR, ROOT_DIR  # noqa: F401 — 수집기가 여기서 가져다 쓴다

load_dotenv(ROOT_DIR / ".env")

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
DART_API_KEY = os.environ.get("DART_API_KEY", "")
