"""Stage A(수집) — 실제 외부 소스를 호출해 pipeline/raw/**에 원본 스냅샷을 저장한다.

이 패키지의 모듈들은 항상 분석가가 수동으로(`python -m pipeline.collectors.<name>`)
실행하며, `npm run etl`(Stage B, 변환)이 자동으로 호출하는 일은 없다.
"""
