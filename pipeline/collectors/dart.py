"""OpenDART(금융감독원 전자공시시스템) 상장 엔터사 재무공시 수집기.

하이브·SM·YG·JYP 등 상장 엔터사는 분기/사업보고서를 의무 공시하므로,
Circle Chart의 "판매량"이나 YouTube의 "댓글 반응"과 달리 실제 매출·영업이익
숫자를 무료 공개 API로 얻을 수 있다. 공시 자체가 출처라 별도 인용 관리도
필요 없다. 무료 API이고 일일 한도가 넉넉해(수 만 건 단위) YouTube처럼
별도의 1회성 가드는 두지 않고 circlechart 수집기와 같은 흐름으로 다룬다.

사전 준비:
  1. https://opendart.fss.or.kr 에서 API 키 발급 → .env의 DART_API_KEY에 저장
  2. pipeline/curated/dart_targets.yaml에 추적할 회사의 corp_code(DART 고유번호)를
     채워 넣기 — 개발가이드의 고유번호 전체 목록(zip)에서 회사명으로 검색

주의: 아직 실제 API 키로 응답 형식을 검증하지 못했다. fnlttSinglAcnt.json
엔드포인트의 파라미터/응답 필드는 OpenDART 공식 문서 기준으로 작성했으니,
최초 실행 시 반환된 계정 목록(account_nm)에 "매출액"/"영업이익" 표기가
정확히 일치하는지 확인할 것.

실행: python -m pipeline.collectors.dart [--year 2025] [--reprt-code 11011]
"""

from __future__ import annotations

import argparse
import json
from datetime import date

import httpx
import yaml

from pipeline.config import CURATED_DIR, DART_API_KEY, RAW_DIR

API_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"

# 1분기(11013) / 반기(11012) / 3분기(11014) / 사업보고서(11011)
DEFAULT_REPRT_CODE = "11011"


def load_targets() -> list[dict]:
  path = CURATED_DIR / "dart_targets.yaml"
  data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
  return data.get("companies", [])


def fetch_financials(corp_code: str, year: int, reprt_code: str) -> dict:
  if not DART_API_KEY:
    raise RuntimeError("DART_API_KEY가 설정되지 않았습니다 (.env 확인)")
  params = {
    "crtfc_key": DART_API_KEY,
    "corp_code": corp_code,
    "bsns_year": str(year),
    "reprt_code": reprt_code,
  }
  response = httpx.get(API_URL, params=params, timeout=15.0)
  response.raise_for_status()
  return response.json()


def save_snapshot(agency: str, year: int, reprt_code: str, data: dict) -> None:
  dart_dir = RAW_DIR / "dart"
  dart_dir.mkdir(parents=True, exist_ok=True)
  path = dart_dir / f"{agency}_{year}_{reprt_code}.json"
  path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
  print(f"저장 완료: {path}")


def main() -> None:
  parser = argparse.ArgumentParser(description="OpenDART 상장 엔터사 재무공시 수집")
  parser.add_argument("--year", type=int, default=date.today().year - 1)
  parser.add_argument("--reprt-code", default=DEFAULT_REPRT_CODE)
  args = parser.parse_args()

  targets = load_targets()
  if not targets:
    print("pipeline/curated/dart_targets.yaml에 등록된 회사가 없습니다.")
    return

  for company in targets:
    agency = company["name"]
    corp_code = company.get("corp_code", "")
    if not corp_code:
      print(f"{company['label']}: corp_code가 비어 있어 건너뜁니다.")
      continue
    print(f"{company['label']} ({args.year}년, reprt_code={args.reprt_code}) 수집 중...")
    data = fetch_financials(corp_code, args.year, args.reprt_code)
    if data.get("status") not in (None, "000"):
      print(f"  경고: {data.get('message')}")
      continue
    save_snapshot(agency, args.year, args.reprt_code, data)


if __name__ == "__main__":
  main()
