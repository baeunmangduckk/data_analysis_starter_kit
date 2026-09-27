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
- 파이프라인은 "수집(Stage A, `pipeline/collectors/*`)"과 "변환(Stage B, `pipeline/etl.py`)"으로 분리돼 있다. `pipeline/etl.py`는 `pipeline/raw/`(수집 스냅샷)와 `pipeline/curated/`(큐레이션 YAML)만 읽고 네트워크/API 키(`pipeline/config.py`)를 절대 건드리지 않는다 — `npm run etl`이 항상 오프라인으로 동작해야 한다는 제약이 이 분리의 이유다. 자세한 배경은 아래 "이번 프로젝트 지침 → 실제 데이터 수집 아키텍처" 참고.
- circlechart.kr JSON API(`POST /data/api/chart/album`)는 응답에 `targetTime 파라미터 부족` ErrorMsg가 항상 따라오지만 `ResultStatus: "OK"`이고 데이터는 정상이다(2026-09-27 확인) — 무시해도 된다. 레코드 필드명은 `SERVICE_RANKING`/`Album_CNT`/`ARTIST_NAME`/`ALBUM_NAME`/`de_nm`이며, `de_nm`(유통사)은 실제 소속사가 아니므로 에이전시 분류에 쓰면 안 된다(레거시 스크래퍼 경고와 동일).
- circlechart 응답은 UTF-8이지만 Windows 콘솔(cp949)에 그대로 출력하면 한글이 깨져 보인다 — 실제 값은 정상이니 콘솔 출력만 보고 인코딩 버그로 오인하지 말 것 (파일로 저장해 확인하거나 `PYTHONIOENCODING=utf-8`로 확인).

## 검증 방법

1. `npm run collect:circlechart` 실행 → `pipeline/raw/circlechart/album_<year>.json` 생성 확인
2. `npm run etl` 실행 → `public/data/`에 JSON 5개 생성 확인 (수집기를 안 돌렸다면 예시 데이터로 자동 대체됨 — 콘솔에 안내 메시지 출력)
3. `npm run dev` 실행 → 브라우저에서 카드·그래프·인사이트·워드클라우드 정상 표시 확인
4. 파이썬 집계 함수 하나를 수정 후 재실행 → 새로고침만으로 화면에 반영되는지 확인 (별도 캐시 처리 불필요)
5. `npm run collect:youtube`를 연속 두 번 실행 → 두 번째는 API 호출 없이 건너뜀 메시지만 출력하는지, `-- --force`로만 재수집되는지 확인

## 이번 프로젝트 지침

- **프로젝트 목표**: 이 스타터킷을 실제 **K-Pop 산업 전망 및 지표 분석 대시보드**로 고도화하는 것이 목표다.
- **참고 기획/전망 문서**: `./docs/` 폴더의 문서(예: `K-POP_대시보드_핵심_인사이트_보고서.docx`)를 기획 배경과 핵심 인사이트의 근거로 참고할 것.
- **레거시 대시보드 참고**: `C:\Users\rladm\real_kpop_future`에 이미 구현된 K-pop 전망 대시보드가 있다.
  - 참고 대상: `data-pipeline/`의 집계·인사이트 계산 로직(`database.py`, `concentration.py`, `insights.py`, `export_static.py`, `scrapers/`), `data/*.json`의 주제별 데이터 형태, `src/components/charts/`의 Recharts 차트 컴포넌트 구현.
  - 원칙: 코드를 그대로 복사하지 말 것. 레거시는 Next.js 서버 컴포넌트가 SQLite→JSON export 결과를 `fs`로 직접 읽는 구조지만, 이 저장소는 "Python(Polars+Pydantic) → JSON 5개 → Next.js" 계약이 이미 확정돼 있다. 참고한 로직·차트 아이디어는 `pipeline/models.py` + `pipeline/etl.py`의 `build_*` 함수 + `src/components/dashboard/*` 컴포넌트 패턴에 맞춰 리팩토링해서 새로 작성한다.
- **실제 데이터 수집 아키텍처 (구현 완료, 2026-09-27)**: `generate_sample_events()` 목업을 걷어내고 "수집(Stage A)"과 "변환(Stage B)"으로 분리한 실데이터 파이프라인을 구축했다. 자세한 설계 배경은 `.claude/plans/pasted-content-id-ddb6-lexical-music.md` 참고.
  - **Stage A(`pipeline/collectors/*`, 항상 수동 실행)**: `circlechart.py`(circlechart.kr Top100 판매, API 키 불필요), `dart.py`(OpenDART 상장 엔터사 재무공시 — 하이브/SM/YG/JYP 매출·영업이익으로 `distribution.json`의 에이전시별 비중을 신뢰도 있게 채울 수 있는 신규 발굴 소스), `youtube.py`(YouTube Data API v3 댓글/조회수).
  - **Stage B(`pipeline/etl.py`)**: `pipeline/raw/`와 `pipeline/curated/*.yaml`만 읽고 네트워크를 전혀 쓰지 않는다. 각 항목의 실데이터가 아직 없으면 `generate_sample_events()`로 자동 폴백한다.
  - **YouTube 쿼터 보호**: `search.list`(호출당 100 units)는 쓰지 않고 `pipeline/curated/youtube_targets.yaml`에 분석가가 직접 등록한 video_id만 조회한다. **자동 주기 없이 "수동 트리거만"** 수집하며, `pipeline/raw/youtube/state.json`에 스냅샷이 이미 있으면 기본적으로 건너뛰고 `npm run collect:youtube -- --force`를 명시해야만 재수집한다 — Playwright MCP 브라우저 자동화는 검토했으나 YouTube는 공식 REST API로 충분해 채택하지 않았다(Playwright MCP는 공식 API가 없는 X/커뮤니티 등 향후 소스를 위해 남겨둔다).
  - **큐레이션 통계(`pipeline/curated/*.yaml`, git 커밋 대상)**: `docs/K-POP_대시보드_핵심_인사이트_보고서.docx`의 실제 인용 수치(글로벌 음반 매출, 지니계수 시계열, 하이브 영업이익 급감, 제작비 격차 29배 등)를 `kpi_snapshots.yaml`/`gini_series.yaml`/`manual_insights.yaml`로 옮겨 `metrics.json`/`timeseries.json`/`insights.json`을 채운다. 출처(`source_name`/`source_url`)는 YAML에만 남기고 JSON 계약(`pipeline/models.py`)에는 노출하지 않는다.
  - **`pipeline/raw/`는 `.gitignore` 처리**(YouTube 데이터 정책상 원본 댓글 장기 보관 제약 + 수집기 재실행으로 재현 가능한 캐시이기 때문). `pipeline/curated/`는 분석가가 직접 쓰는 소스이므로 커밋한다.
  - `build_insights()`는 지표별로 "증가/감소 중 무엇이 긍정적인지"(`favorable_trend`, 지니계수처럼 감소가 좋은 지표는 `higher_is_better: false`)를 받도록 확장됐다 — 이 힌트 없이 무조건 "증가=긍정"으로 판단하면 지니계수 감소가 "경고"로 잘못 표시된다.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
