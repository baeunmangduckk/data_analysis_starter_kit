# 데이터 분석 스타터 키트

데이터 분석가가 파이썬 계산 로직만 수정하면 웹 대시보드가 자동으로 갱신되는 구조를 제공하는 프로젝트입니다.

파이썬이 계산한 결과를 JSON 파일로 저장하고, 웹 화면은 그 JSON 파일을 읽어 그래프와 카드로 표시합니다. 파이썬과 웹 화면은 JSON 파일을 통해서만 연결되므로, 분석가는 웹 화면 코드를 몰라도 작업할 수 있습니다.

## 기술 스택

| 구분 | 이름 | 역할 |
|---|---|---|
| 데이터 처리 | Python | 계산 로직 작성 (분석가 담당 영역) |
| 데이터 처리 | Polars | 표 형태 데이터 집계·가공 (pandas와 유사) |
| 데이터 처리 | Pydantic | 계산 결과의 형식(필드·타입) 검증 |
| 연결 계층 | JSON | 파이썬과 웹 화면을 잇는 계약(contract) |
| 웹 화면 | Next.js | 웹 페이지 프레임워크 |
| 웹 화면 | React | 컴포넌트 단위 화면 구성 |
| 웹 화면 | TypeScript | 값의 형식을 정의·검증 |
| 웹 화면 | Tailwind CSS / shadcn-ui | 사전 제작된 디자인 컴포넌트 |
| 웹 화면 | Recharts | 꺾은선·막대·파이 그래프 렌더링 |
| 웹 화면 | next-themes | 다크모드 / 라이트모드 전환 |

## 전체 파이프라인

데이터 파이프라인은 "수집(Stage A)"과 "변환(Stage B)" 두 단계로 나뉩니다.

- **Stage A — 수집** (`pipeline/collectors/*`, 항상 수동 실행): circlechart.kr, OpenDART, YouTube Data API 등 실제 소스를 호출해 `pipeline/raw/`에 원본 스냅샷을 저장합니다. 네트워크를 쓰는 유일한 단계이며, `npm run etl`은 이 단계를 절대 자동으로 호출하지 않습니다.
- **Stage B — 변환** (`pipeline/etl.py`, `npm run etl`): `pipeline/raw/`(수집 스냅샷)와 `pipeline/curated/`(분석가가 출처와 함께 직접 입력한 통계)만 읽어 Polars로 집계하고, Pydantic으로 형식을 검증한 뒤 `public/data/*.json` 5개로 저장합니다. 네트워크를 전혀 쓰지 않아 항상 빠르고 오프라인이며 결정적으로 동작합니다.

```
1. (수동) 수집기 실행 → pipeline/raw/**에 원본 스냅샷 저장
2. npm run etl → pipeline/raw + pipeline/curated를 Polars로 집계
3. Pydantic으로 결과 형식을 검증
4. public/data/*.json 5개 파일로 저장
5. Next.js 서버가 JSON 파일을 읽음
6. React 컴포넌트가 JSON을 받아 화면을 구성
7. 브라우저에 최종 대시보드가 표시됨
```

분석가는 `build_*` 함수의 집계 로직과 `pipeline/curated/*.yaml`의 통계만 수정하면 되고, 나머지는 고정된 인프라로 자동 동작합니다. 원본 스냅샷/큐레이션 데이터가 아직 없는 항목은 `generate_sample_events()` 예시 데이터로 자동 폴백하므로, 수집기를 한 번도 안 돌려도 `npm run etl`이 실패하지 않습니다.

### 수집기(Stage A) 목록

| 명령어 | 소스 | 비고 |
|---|---|---|
| `npm run collect:circlechart` | circlechart.kr 앨범 판매 Top100 JSON API | API 키 불필요. `distribution.json`(판매 집중도)에 반영 |
| `npm run collect:dart` | OpenDART(금융감독원 전자공시) 상장 엔터사 재무제표 | `.env`의 `DART_API_KEY` + `pipeline/curated/dart_targets.yaml`의 corp_code 필요 |
| `npm run collect:youtube` | YouTube Data API v3 (댓글/조회수) | `.env`의 `YOUTUBE_API_KEY` 필요. **쿼터 보호를 위해 이미 수집된 스냅샷이 있으면 자동으로 건너뛰며, 다시 수집하려면 `npm run collect:youtube -- --force`를 명시해야 합니다.** |

`.env.example`을 `.env`로 복사한 뒤 API 키를 채워 넣어야 `collect:dart`/`collect:youtube`가 동작합니다 (`.env`는 git에 커밋되지 않습니다).

## 산출물 구성

| 화면 요소 | JSON 파일 | 표시 내용 | 컴포넌트 |
|---|---|---|---|
| KPI 카드 | `metrics.json` | 주요 지표 수치 및 증감 | `KpiGrid` |
| 추이 그래프 | `timeseries.json` | 시간에 따른 값 변화 | `TrendChart` |
| 비중 그래프 | `distribution.json` | 카테고리별 비중 | `DistributionChart` |
| 인사이트 박스 | `insights.json` | 정성적 코멘트 | `InsightBox` |
| 워드클라우드 | `wordcloud.json` | 단어 빈도 + 감성(긍정/부정/중립) | `SentimentWordCloud` |

각 JSON은 `pipeline/models.py`(Pydantic)와 `src/types/dashboard.ts`(TypeScript)에 필드 단위로 동일하게 정의되어 있습니다. 분석가가 실제로 손대는 지점은 `pipeline/etl.py`의 5개 `build_*` 함수와, 감성 분류에 쓰이는 `pipeline/sentiment_words.py`의 긍정/부정 단어 목록뿐입니다.

## 시작하기

### 사전 준비

- Node.js
- Python 3.12 (`.venv`에 `requirements.txt`의 패키지 설치)

### 설치 및 실행

```bash
npm install                                       # Node 의존성 설치
python -m venv .venv                              # 최초 1회
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm run etl                                       # 파이썬 ETL 실행 → public/data/*.json 생성
npm run dev                                       # 개발 서버 실행, http://localhost:3000
```

실제 데이터가 필요하면 위 명령 전에 수집기를 먼저 실행합니다(아래 "수집기 목록" 참고). 수집기를 건너뛰어도 `npm run etl`은 예시 데이터로 정상 동작합니다.

### 명령어 목록

| 명령어 | 설명 |
|---|---|
| `npm run dev` | Next.js 개발 서버(Turbopack) 실행 |
| `npm run build` | 프로덕션 빌드 |
| `npm run start` | 프로덕션 빌드 실행 |
| `npm run lint` | eslint 실행 |
| `npm run etl` | `pipeline/etl.py`를 실행해 `public/data/*.json` 재생성 (오프라인, Stage B) |
| `npm run collect:circlechart` | circlechart.kr 앨범 판매 Top100 수집 (Stage A) |
| `npm run collect:dart` | OpenDART 상장 엔터사 재무공시 수집 (Stage A) |
| `npm run collect:youtube` | YouTube 댓글/조회수 수집, 이미 수집됐으면 건너뜀 (`-- --force`로 재수집, Stage A) |
| `npx tsc --noEmit` | 타입 체크만 수행 (테스트 스위트 없음) |

> `npm run etl`은 내부적으로 `python -m pipeline.etl`(모듈 방식)로 실행됩니다. `python pipeline/etl.py`처럼 스크립트로 직접 실행하면 임포트 경로가 깨지므로 npm 스크립트를 그대로 사용해야 합니다.

## 검증 방법

1. `npm run collect:circlechart` 실행 → `pipeline/raw/circlechart/album_<year>.json` 생성 확인
2. `npm run etl` 실행 → `public/data/`에 JSON 5개 생성 확인 (수집기를 안 돌렸다면 예시 데이터로 대체됨)
3. `npm run dev` 실행 → 브라우저에서 카드·그래프·인사이트·워드클라우드 정상 표시 확인
4. 파이썬 집계 함수 하나를 수정 후 재실행 → 새로고침만으로 화면에 반영되는지 확인 (별도 캐시 처리 불필요)
5. `npm run collect:youtube`를 연속으로 두 번 실행 → 두 번째 실행이 API를 호출하지 않고 건너뛰는지 확인, `-- --force`로만 재수집되는지 확인

## 참고

자세한 아키텍처 배경과 구현 시 주의사항은 [`CLAUDE.md`](./CLAUDE.md)를 참고하세요.
