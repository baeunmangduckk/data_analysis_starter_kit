---
description: '새 KPI 카드를 pipeline과 대시보드 화면에 추가합니다'
argument-hint: '[metric_key] [MetricLabel]'
allowed-tools:
  [
    'Read',
    'Edit',
    'Grep',
    'Glob',
    'Bash(.\.venv\Scripts\python.exe -m pipeline.etl)',
    'Bash(npx tsc --noEmit)',
  ]
---

# Claude 명령어: Add KPI

$1(지표 키)과 $2(표시 라벨)로 새 KPI 카드를 추가한다.

## 사용법

```
/add-kpi conversion_rate 전환율
```

## 프로세스

1. **현황 파악**: `pipeline/models.py`의 `KpiMetric`/`MetricsData`와 `pipeline/etl.py`의 `build_metrics` 함수를 먼저 읽는다.
   - `build_metrics`는 현재 `events` 데이터의 카테고리별로 `KpiMetric`을 동적으로 생성한다. 새 지표가 기존 카테고리 집계와 동일한 방식(합계/증감 비교)이면 별도 코드 없이 데이터만 추가해도 될 수 있으니, 정말 새로운 계산 로직이 필요한 경우에만 아래 단계를 진행한다.

2. **모델 확장 (필요한 경우에만)**: `KpiMetric`에 없는 새 필드가 필요하면
   - `pipeline/models.py`의 `KpiMetric`에 필드 추가
   - `src/types/dashboard.ts`의 `KpiMetric` 인터페이스에 동일한 필드를 동일한 이름(camelCase)으로 추가
   - 두 파일의 필드 이름·타입이 정확히 일치해야 한다.

3. **계산 로직 추가**: `pipeline/etl.py`의 `build_metrics` 함수(또는 필요시 헬퍼 함수)에 `id="$1"`, `label="$2"`인 `KpiMetric`을 계산해 `metrics` 리스트에 추가하는 로직을 작성한다.

4. **ETL 실행**: `.\.venv\Scripts\python.exe -m pipeline.etl`을 실행해 `public/data/metrics.json`을 갱신하고, 새 지표가 포함됐는지 확인한다.
   - 반드시 `-m pipeline.etl` 모듈 방식으로 실행할 것 (스크립트 직접 실행 시 `pipeline.models` import가 깨짐).

5. **화면 반영 확인**: `src/components/dashboard/kpi-grid.tsx`는 `metrics` 배열을 순회하며 카드를 범용적으로 렌더링하므로, 3단계에서 새 필드를 추가하지 않았다면 보통 컴포넌트 수정이 필요 없다. 새 필드(예: 특수 단위 표시, 별도 아이콘 등)를 화면에 반영해야 하는 경우에만 `kpi-grid.tsx`를 수정한다.

6. **타입 검증**: `npx tsc --noEmit`을 실행해 타입 오류가 없는지 확인한다.

## 참고사항

- `pipeline/models.py`와 `src/types/dashboard.ts`는 필드 단위로 1:1 대응해야 한다 (`CLAUDE.md` 계약).
- Pydantic 쪽은 `model_validator`로, TypeScript 쪽은 타입 시스템으로 검증하는 지점이 다르므로 두 파일을 함께 수정했는지 항상 재확인한다.
