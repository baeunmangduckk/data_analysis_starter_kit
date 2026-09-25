# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## 개요

데이터 분석가가 파이썬 코드의 계산 로직만 수정하면, 웹 대시보드 화면이 자동으로 갱신되는 구조를 만드는 프로젝트다. 파이썬이 계산한 결과를 JSON 파일로 저장하고, 웹 화면은 그 JSON 파일을 읽어 그래프와 카드로 표시한다. 파이썬과 웹 화면은 이 JSON 파일을 통해서만 연결되므로, 분석가는 웹 화면 코드를 몰라도 작업할 수 있다.

## 명령어

```bash
npm run dev            # Next.js 개발 서버(Turbopack), http://localhost:3000
npm run build           # 프로덕션 빌드
npm run start           # 프로덕션 빌드 실행
npm run lint             # eslint
npm run etl               # pipeline/etl.py를 실행해 public/data/*.json 재생성
npx tsc --noEmit         # 타입 체크만 수행 (아직 테스트 스위트 없음)
```

## 기술 스택 및 역할

| 구분 | 이름 | 역할 |
|---|---|---|
| 데이터 처리 | Python | 계산 로직 작성 (분석가 담당 영역) |
| 데이터 처리 | Polars | 표 형태 데이터 집계·가공 (pandas와 유사) |
| 데이터 처리 | Pydantic | 계산 결과의 형식(필드·타입)을 검증 |
| 연결 계층 | JSON | 파이썬 결과물을 저장하는 파일. 파이썬과 웹 화면을 잇는 계약(contract) |
| 웹 화면 | Next.js | 웹 페이지 프레임워크 (Python의 FastAPI/Flask에 대응) |
| 웹 화면 | React | 화면을 부품(컴포넌트) 단위로 구성 |
| 웹 화면 | TypeScript | 값의 형식을 미리 정의하고 검증 (Pydantic과 같은 역할을 프론트엔드에서 수행) |
| 웹 화면 | Tailwind CSS / shadcn-ui | 사전 제작된 디자인 컴포넌트(버튼, 카드 등) |
| 웹 화면 | Recharts | 꺾은선·막대·파이 그래프 렌더링 |
| 웹 화면 | next-themes | 다크모드 / 라이트모드 전환 |

## 전체 파이프라인

| 단계 | 주체 | 내용 |
|---|---|---|
| 1 | Python | 원본 데이터를 Polars로 집계 |
| 2 | Python | Pydantic으로 결과 형식 검증 |
| 3 | Python | `public/data/*.json` 5개 파일로 저장 |
| 4 | Next.js | 서버에서 JSON 파일을 읽음 |
| 5 | React | 컴포넌트가 JSON을 받아 화면을 구성 |
| 6 | 브라우저 | 최종 대시보드 표시 |

분석가는 1~2단계의 계산 로직만 수정하면 되고, 3~6단계는 고정된 인프라로 자동 동작한다.

## 산출물 구성

| 화면 요소 | JSON 파일 | 표시 내용 | 컴포넌트 |
|---|---|---|---|
| KPI 카드 | `metrics.json` | 주요 지표 수치 및 증감 | `KpiGrid` |
| 추이 그래프 | `timeseries.json` | 시간에 따른 값 변화 | `TrendChart` |
| 비중 그래프 | `distribution.json` | 카테고리별 비중 | `DistributionChart` |
| 인사이트 박스 | `insights.json` | 정성적 코멘트 | `InsightBox` |
| 워드클라우드 | `wordcloud.json` | 단어 빈도 + 감성(긍정/부정/중립) | `SentimentWordCloud` |

각 JSON은 `pipeline/models.py`(Pydantic)와 `src/types/dashboard.ts`(TypeScript)에 필드 단위로 동일하게 정의되어 있다. 분석가가 실제로 손대는 지점은 `pipeline/etl.py`의 5개 `build_*` 함수와, 감성 분류에 쓰이는 `pipeline/sentiment_words.py`의 긍정/부정 단어 목록뿐이다.

## 구현 시 알아둘 것 (직접 부딪혀서 확인한 함정들)

- **`npm run etl`은 반드시 `-m pipeline.etl`(모듈 방식)으로 실행**해야 한다. `python pipeline/etl.py`처럼 스크립트로 직접 실행하면 `pipeline/`이 `sys.path`에 안 올라가서 `from pipeline.models import ...` 임포트가 깨진다. npm 스크립트의 Windows 백슬래시 경로(`.\.venv\Scripts\python.exe`)도 그대로 유지해야 한다 — `cmd.exe`는 슬래시로 된 상대경로를 실행 파일로 인식하지 못한다.
- `build_wordcloud`의 감성 분류는 부정 단어를 긍정 단어보다 먼저 검사한다. "불친절"처럼 부정 표현이 긍정 단어 "친절"을 부분 문자열로 포함하는 경우가 있기 때문이다.
- `TimeseriesData.points`는 필드가 고정돼 있지 않고 `series[].key`에 따라 동적으로 구성된다 — 타입 시스템이 아니라 `pipeline/models.py`의 `model_validator`가 일치 여부를 검증한다.
- `src/app/page.tsx`는 JSON을 **모듈 스코프가 아니라 async 컴포넌트 함수 내부에서** 읽는다. 모듈 스코프에서 읽으면 서버 프로세스당 한 번만 실행되어 `npm run etl` 재실행 후에도 갱신되지 않는다.
- shadcn `base-nova` 스타일은 Radix가 아니라 **`@base-ui/react`**를 쓴다. `Badge`/`Button`은 `asChild` 대신 `render` prop을, `Tabs`는 `data-state` 대신 `data-active`/`value` 방식을 쓴다.
- `public/data/*.json`은 의도적으로 git에 커밋한다 — clone 직후 `npm run dev`만으로 바로 확인 가능하게 하기 위함.
- 차트 색상(`--chart-1`~`--chart-5`)은 현재 라이트/다크 모두 동일한 그레이스케일이라 다중 시리즈 구분력이 약하다 — 카테고리컬 팔레트 교체는 아직 안 한 후속 과제.

## 검증 방법

1. `npm run etl` 실행 → `public/data/`에 JSON 5개 생성 확인
2. `npm run dev` 실행 → 브라우저에서 카드·그래프·인사이트·워드클라우드 정상 표시 확인
3. 파이썬 집계 함수 하나를 수정 후 재실행 → 새로고침만으로 화면에 반영되는지 확인 (별도 캐시 처리 불필요)
