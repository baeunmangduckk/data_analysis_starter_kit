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
| 3 | Python | `public/data/*.json`(홈 2개 + 페이지 6개 + 출처 1개)으로 저장 |
| 4 | Next.js | 서버에서 JSON 파일을 읽음 (`src/lib/data.ts`) |
| 5 | React | 컴포넌트가 JSON을 받아 화면을 구성 |
| 6 | 브라우저 | 최종 대시보드 표시 |

분석가는 1~2단계의 계산 로직만 수정하면 되고, 3~6단계는 고정된 인프라로 자동 동작한다.

## 산출물 구성 (다중 페이지)

왼쪽 사이드바로 이동하는 8개 페이지다. 페이지 목록은 `src/lib/nav.ts` 한 곳에서 관리하며(사이드바·홈 링크 카드가 함께 씀), 라우트 폴더명 = JSON 파일명 = `nav.ts`의 `slug`다.

| 라우트 | JSON | 만드는 곳 | 주 데이터 |
|---|---|---|---|
| `/` 홈 | `metrics.json`, `insights.json` | `pipeline/etl.py`의 `load_*`/`build_*` | 큐레이션 KPI + DART 합산 KPI, 자동·수동 인사이트 |
| `/market` 시장 전망 | `market.json` | `pipeline/pages/market.py` | `curated/market_outlook.yaml` |
| `/concentration` 판매 집중도·양극화 | `concentration.json` | `pages/concentration.py` | `curated/sales_concentration.yaml`, `polarization.yaml` |
| `/finance` 기획사 재무 | `finance.json` | `pages/finance.py` | DART 실데이터(`raw/dart`) + `curated/agency_metrics.yaml` |
| `/fans` 팬 반응 | `fans.json` | `pages/fans.py` | YouTube 실데이터(`raw/youtube`) + `curated/artist_metrics.yaml` |
| `/global` 글로벌 확장 | `global.json` | `pages/global_expansion.py` | `curated/global_expansion.yaml` |
| `/ai-virtual` AI·버추얼 | `ai-virtual.json` | `pages/ai_virtual.py` | `curated/ai_virtual.yaml` |
| `/sources` 출처 | `sources.json` | `pages/sources.py` | `curated/sources.yaml` + 페이지의 인용 역참조 |

**페이지 JSON = 섹션 배열.** `PageData{title, summary, sections[]}`의 각 섹션은 `type`으로 구분되는 소수의 블록이다: `stats`(KPI 카드), `chart`(line/area/column/barH, 결측은 `null`), `table`, `cases`(사례 카드), `insights`, `wordcloud`, `notice`(안내·경고). 분석가는 `pipeline/pages/<slug>.py`의 `build()`에서 섹션을 추가·삭제하는 것만으로 화면을 바꾼다 — 화면 코드는 `SectionRenderer`가 알아서 그린다. 계약은 `pipeline/models.py`(Pydantic)와 `src/types/page.ts`(TypeScript, 홈용은 `dashboard.ts`)에 1:1로 정의돼 있고, 섹션 타입을 새로 추가하면 `SectionRenderer`의 `never` 체크가 누락을 컴파일 오류로 알려준다.

## 구현 시 알아둘 것 (직접 부딪혀서 확인한 함정들)

- **`npm run etl`은 반드시 `-m pipeline.etl`(모듈 방식)으로 실행**해야 한다. `python pipeline/etl.py`처럼 스크립트로 직접 실행하면 `pipeline/`이 `sys.path`에 안 올라가서 `from pipeline.models import ...` 임포트가 깨진다. npm 스크립트의 Windows 백슬래시 경로(`.\.venv\Scripts\python.exe`)도 그대로 유지해야 한다 — `cmd.exe`는 슬래시로 된 상대경로를 실행 파일로 인식하지 못한다.
- 감성 분류(`pipeline/derived/sentiment.py`)는 부정 단어를 긍정 단어보다 먼저 검사한다. "불친절"처럼 부정 표현이 긍정 단어 "친절"을 부분 문자열로 포함하는 경우가 있기 때문이다. 영어 단어는 `whatever`에 `hate`가 들어 있는 것 같은 오분류를 피하려고 부분 문자열이 아니라 완전 일치로만 판정한다.
- chart 섹션의 `points`는 필드가 고정돼 있지 않고 `xKey` + `series[].key`에 따라 동적으로 구성된다 — 타입 시스템이 아니라 `pipeline/models.py`의 `validate_points_match_series`(공용 `model_validator`)가 일치 여부를 검증한다. table 섹션도 `rows` 키와 `columns` 정의가 일치해야 한다.
- **JSON은 반드시 요청 시점에 읽는다.** `src/lib/data.ts`의 `readData()`가 `await connection()`을 호출해 프로덕션 빌드에서도 정적으로 굳지 않게 하고, 파일이 없으면 `null`을 돌려 `<DataMissing>`(“`npm run etl` 실행” 안내)을 보여준다. 페이지 컴포넌트 **함수 안에서** 호출해야 하며, 모듈 스코프에서 읽으면 `npm run etl` 재실행 후에도 갱신되지 않는다. 이 Next.js 16 버전은 학습 데이터와 API가 다르므로 라우팅·레이아웃은 `node_modules/next/dist/docs/01-app/`을 먼저 확인할 것.
- shadcn `base-nova` 스타일은 Radix가 아니라 **`@base-ui/react`**를 쓴다. `Badge`/`Button`/`SidebarMenuButton`은 `asChild` 대신 `render` prop을, `Tabs`는 `data-state` 대신 `data-active`/`value` 방식을 쓴다. `npx shadcn add`가 만든 코드가 React 19 린트에 걸릴 수 있다(`use-mobile.ts`는 `useSyncExternalStore`로 교체함).
- `public/data/*.json`은 의도적으로 git에 커밋한다 — clone 직후 `npm run dev`만으로 바로 확인 가능하게 하기 위함.
- 차트 색상(`--chart-1`~`--chart-5`)은 blue·orange·aqua·yellow·magenta 카테고리 팔레트다(라이트/다크 각각 `dataviz` 검증기 통과). **시리즈 배정 순서를 바꾸지 말 것.** 라이트 모드의 aqua·yellow·magenta는 대비 3:1 미만이라 범례·표 보기가 반드시 함께 있어야 한다(`ChartCard`가 "표로 보기"를 제공). Recharts `Legend`는 기본적으로 이름순 정렬이라 `itemSorter={null}`을 써야 시리즈 순서와 맞는다.
- **출처는 JSON 계약에 노출한다.** (이전에는 "YAML에만 둔다"였으나 출처 페이지를 위해 변경) `pipeline/curated/sources.yaml`이 유일한 레지스트리이고, 다른 curated YAML의 모든 행은 `source`(레지스트리 id)와 `as_of`(기준 시점)가 필수다. `pipeline/curated_schema.py`가 읽는 즉시 검증(`extra="forbid"`로 키 오타 차단)하고, 페이지가 인용한 sourceId가 레지스트리에 없으면 `npm run etl`이 **전체 중단**한다. 저장은 모든 모델을 직렬화한 뒤 한꺼번에 하므로 실패해도 기존 JSON이 반쪽만 갱신되지 않는다.
- `confidence`: `verified`(자동 수집·기획 문서와 대조 완료) / `estimated`(보정·추정) / `legacy_unverified`(레거시 웹 리서치 값을 원문 재확인 없이 이관, 화면에 "미검증" 배지). curated 값을 옮길 때는 **단위를 화면 단위(억 원·억 달러·조 원)로 환산해 적는다** — 레거시가 USD Billion/KRW Billion을 그대로 써서 10배 틀린 값이 두 건 있었다(글로벌 음반 매출 31.7 → 317억 달러, 기획사 1분기 매출은 "100억 원" 단위로 보정해 `estimated`).
- 원자료에 없는 연도(예: 앨범 수출 2024)는 `0`이 아니라 `null`로 두면 차트에서 선이 끊기고 표에는 `–`로 나온다. 값이 정확히 `1.0`으로 적힌 사례 수치(PLAVE 구독자 등)는 자리표시자로 보고 옮기지 않았다.
- 파이프라인은 "수집(Stage A, `pipeline/collectors/*`)"과 "변환(Stage B, `pipeline/etl.py`)"으로 분리돼 있다. `pipeline/etl.py`는 `pipeline/raw/`(수집 스냅샷)와 `pipeline/curated/`(큐레이션 YAML)만 읽고 네트워크/API 키(`pipeline/config.py`)를 절대 건드리지 않는다 — `npm run etl`이 항상 오프라인으로 동작해야 한다는 제약이 이 분리의 이유다. 자세한 배경은 아래 "이번 프로젝트 지침 → 실제 데이터 수집 아키텍처" 참고.
- circlechart.kr JSON API(`POST /data/api/chart/album`)는 응답에 `targetTime 파라미터 부족` ErrorMsg가 항상 따라오지만 `ResultStatus: "OK"`이고 응답 자체는 온다(2026-09-27 확인) — 에러 문구는 무시해도 된다. **다만 값이 큐레이션 계열과 크게 다르다**: 수집기가 저장한 `raw/circlechart/album_2025.json`을 직접 집계하면 총 판매량 약 3,530만 장·Top10 38.9%·Gini 0.518인데, 레거시·기획 문서의 2025 값은 6,462만 장·29.8%·0.4007이다. 요청 파라미터(`yearTime: "1"` 등)가 연간 전체가 아닌 일부 기간을 가리킬 가능성이 있으나 **원인은 미확인**이다. 그래서 집중도 페이지는 큐레이션 계열(`sales_concentration.yaml`)을 쓰고, raw 스냅샷을 직접 소비하는 화면은 현재 없다(`derived/concentration.py`의 집계 함수만 남아 있다). 레코드 필드명은 `SERVICE_RANKING`/`Album_CNT`/`ARTIST_NAME`/`ALBUM_NAME`/`de_nm`이며, `de_nm`(유통사)은 실제 소속사가 아니므로 에이전시 분류에 쓰면 안 된다(레거시 스크래퍼 경고와 동일).
- circlechart 응답은 UTF-8이지만 Windows 콘솔(cp949)에 그대로 출력하면 한글이 깨져 보인다 — 실제 값은 정상이니 콘솔 출력만 보고 인코딩 버그로 오인하지 말 것 (파일로 저장해 확인하거나 `PYTHONIOENCODING=utf-8`로 확인).

## 검증 방법

1. `npm run collect:dart` / `npm run collect:youtube` 실행 → `pipeline/raw/dart/`, `pipeline/raw/youtube/<날짜>/` 생성 확인 (수집기를 안 돌리면 해당 섹션은 "수집 먼저 실행" 안내로 나온다)
2. `npm run etl` 실행 → `public/data/`에 JSON 9개(metrics, insights, sources, 페이지 6개) 생성 확인. curated YAML의 키 오타·출처 누락·없는 sourceId는 여기서 오류로 중단된다.
3. `npx tsc --noEmit`, `npm run lint` 통과 확인
4. `npm run dev` 실행 → 사이드바의 8개 페이지가 모두 뜨는지, 라이트/다크·모바일 폭(시트)에서 깨지지 않는지, 콘솔 오류가 없는지 확인. Recharts는 진입 애니메이션이 있어 캡처가 비어 보이면 잠시 기다렸다 다시 찍는다(`fullPage` 캡처는 리사이즈로 애니메이션이 재시작되니 뷰포트를 키워서 찍는다).
5. 파이썬 집계 함수 하나를 수정 후 재실행 → 새로고침만으로 화면에 반영되는지 확인 (별도 캐시 처리 불필요)
6. `npm run collect:youtube`를 연속 두 번 실행 → 두 번째는 API 호출 없이 건너뜀 메시지만 출력하는지, `-- --force`로만 재수집되는지 확인

## 이번 프로젝트 지침

- **프로젝트 목표**: 이 스타터킷을 실제 **K-Pop 산업 전망 및 지표 분석 대시보드**로 고도화하는 것이 목표다.
- **참고 기획/전망 문서**: `./docs/` 폴더의 문서(예: `K-POP_대시보드_핵심_인사이트_보고서.docx`)를 기획 배경과 핵심 인사이트의 근거로 참고할 것.
- **레거시 대시보드 참고**: `C:\Users\rladm\real_kpop_future`에 이미 구현된 K-pop 전망 대시보드가 있다.
  - 참고 대상: `data-pipeline/`의 집계·인사이트 계산 로직(`database.py`, `concentration.py`, `insights.py`, `export_static.py`, `scrapers/`), `data/*.json`의 주제별 데이터 형태, `src/components/charts/`의 Recharts 차트 컴포넌트 구현.
  - 원칙: 코드를 그대로 복사하지 말 것. 레거시는 Next.js 서버 컴포넌트가 SQLite→JSON export 결과를 `fs`로 직접 읽는 구조지만, 이 저장소는 "Python(Polars+Pydantic) → JSON → Next.js" 계약이 이미 확정돼 있다. 참고한 로직·차트 아이디어는 `pipeline/models.py` + `pipeline/pages/*.py`의 `build()` + `src/components/dashboard/*` 컴포넌트 패턴에 맞춰 리팩토링해서 새로 작성한다. (레거시의 6페이지 구성은 이미 이 방식으로 이관을 마쳤다 — 위 "산출물 구성" 참고.)
- **실제 데이터 수집 아키텍처 (구현 완료, 2026-09-27)**: `generate_sample_events()` 목업을 걷어내고 "수집(Stage A)"과 "변환(Stage B)"으로 분리한 실데이터 파이프라인을 구축했다. 자세한 설계 배경은 `.claude/plans/pasted-content-id-ddb6-lexical-music.md` 참고.
  - **Stage A(`pipeline/collectors/*`, 항상 수동 실행)**: `circlechart.py`(circlechart.kr Top100 판매, API 키 불필요), `dart.py`(OpenDART 상장 엔터사 재무공시 — `dart_targets.yaml`의 종목코드로 `corp_code`를 자동 조회해 하이브/SM/YG/JYP 연결 매출·영업이익 3개년을 수집, 홈 합산 KPI와 `/finance` 페이지의 근거), `youtube.py`(YouTube Data API v3 댓글/조회수, `/fans` 페이지의 근거).
  - **Stage B(`pipeline/etl.py` + `pipeline/pages/*.py`)**: `pipeline/raw/`와 `pipeline/curated/*.yaml`만 읽고 네트워크를 전혀 쓰지 않는다(`pipeline/common.py`가 경로 상수를 갖고 있어 `.env`를 읽는 `config.py`를 import하지 않는다). 홈 KPI의 큐레이션 데이터가 비었을 때만 `generate_sample_events()`로 폴백하고, 페이지들은 가짜 데이터로 채우지 않고 `notice` 섹션("collect 먼저 실행")을 낸다.
  - **YouTube 쿼터 보호**: `search.list`(호출당 100 units)는 쓰지 않고 `pipeline/curated/youtube_targets.yaml`에 분석가가 직접 등록한 video_id만 조회한다. **자동 주기 없이 "수동 트리거만"** 수집하며, `pipeline/raw/youtube/state.json`에 스냅샷이 이미 있으면 기본적으로 건너뛰고 `npm run collect:youtube -- --force`를 명시해야만 재수집한다 — Playwright MCP 브라우저 자동화는 검토했으나 YouTube는 공식 REST API로 충분해 채택하지 않았다(Playwright MCP는 공식 API가 없는 X/커뮤니티 등 향후 소스를 위해 남겨둔다).
  - **큐레이션 통계(`pipeline/curated/*.yaml`, git 커밋 대상)**: `docs/K-POP_대시보드_핵심_인사이트_보고서.docx`의 실제 인용 수치(글로벌 음반 매출, 지니계수 시계열, 하이브 영업이익 급감, 제작비 격차 29배 등)를 `kpi_snapshots.yaml`/`manual_insights.yaml`(홈)과 `sales_concentration.yaml` 등 페이지별 YAML로 옮겨 `metrics.json`/`insights.json`과 각 페이지 JSON을 채운다. 출처는 `sources.yaml`의 id로 참조하며 `sources.json`/출처 페이지로 노출한다(위 "출처는 JSON 계약에 노출한다" 참고). 홈의 `kpi_snapshots.yaml`·`manual_insights.yaml`은 아직 `source_name` 방식이라 레지스트리 id로 옮기는 것이 후속 과제다.
  - **알려진 수치 불일치**: 기획 문서(`manual_insights.yaml`)의 하이브 2025 영업이익은 499억 원(YoY -72.9%)인데 DART 연결 손익계산서로 계산하면 493.2억 원(-73.2%)이다. 기준이 다른 것으로 보이며 원인은 미확인 — DART 값이 1차 출처다.
  - **`pipeline/raw/`는 `.gitignore` 처리**(YouTube 데이터 정책상 원본 댓글 장기 보관 제약 + 수집기 재실행으로 재현 가능한 캐시이기 때문). `pipeline/curated/`는 분석가가 직접 쓰는 소스이므로 커밋한다.
  - `build_insights()`는 지표별로 "증가/감소 중 무엇이 긍정적인지"(`favorable_trend`, 지니계수처럼 감소가 좋은 지표는 `higher_is_better: false`)를 받도록 확장됐다 — 이 힌트 없이 무조건 "증가=긍정"으로 판단하면 지니계수 감소가 "경고"로 잘못 표시된다.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
