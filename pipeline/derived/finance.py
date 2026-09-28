"""DART 재무 스냅샷(pipeline/raw/dart)을 회사·연도별 long 표로 바꾸고 파생 지표를 계산한다.

홈의 DART KPI 카드(etl.load_dart_metrics)와 기획사 재무 페이지(pages/finance.py)가
같은 파싱 결과를 쓰도록 한 곳에 모아 둔다. 네트워크는 쓰지 않고 raw 파일만 읽는다.
"""

from __future__ import annotations

import json

import polars as pl

from pipeline.common import CURATED_DIR, RAW_DIR, load_yaml

# DART 손익계산서 계정명. 표기는 실제 응답으로 확인했다.
REVENUE = "매출액"
OPERATING_PROFIT = "영업이익"
ACCOUNTS = (REVENUE, OPERATING_PROFIT)

WON_PER_EOK = 1e8  # 1억 원

FINANCIALS_SCHEMA = {
  "agency": pl.String,
  "label": pl.String,
  "year": pl.Int64,
  "account": pl.String,
  "amount": pl.Float64,  # 억 원
}


def parse_dart_amount(raw: str | None) -> int | None:
  """DART 금액은 "2,363,993,529,000"처럼 쉼표가 붙은 문자열이고, 값이 없으면 "-"가 온다."""
  try:
    return int(str(raw).replace(",", ""))
  except ValueError:
    return None


def load_agency_targets() -> list[tuple[str, str]]:
  """dart_targets.yaml의 (name, label) 목록. 파일 순서가 차트 색 배정·범례 순서다."""
  companies = load_yaml(CURATED_DIR / "dart_targets.yaml").get("companies", [])
  return [(company["name"], company["label"]) for company in companies]


def load_dart_financials() -> pl.DataFrame:
  """회사·연도·계정별 금액(억 원) long 표를 만든다.

  사업보고서 한 건에는 당기(thstrm)·전기(frmtrm)·전전기(bfefrmtrm) 3개년이 들어 있어
  회사당 3개 연도를 얻는다. 연결(CFS) 손익계산서(IS)만 쓴다 — 별도(OFS)는 자회사
  실적이 빠져 있다. 스냅샷이 없는 회사는 표에서 빠진다."""
  dart_dir = RAW_DIR / "dart"
  rows: list[dict[str, str | int | float]] = []

  for agency, label in load_agency_targets():
    snapshots = sorted(dart_dir.glob(f"{agency}_*_11011.json")) if dart_dir.exists() else []
    if not snapshots:
      continue
    payload = json.loads(snapshots[-1].read_text(encoding="utf-8"))

    seen: set[str] = set()
    for row in payload.get("list", []):
      account = row.get("account_nm")
      if row.get("fs_div") != "CFS" or row.get("sj_div") != "IS":
        continue
      if account not in ACCOUNTS or account in seen:
        continue
      seen.add(account)

      base_year = int(row["bsns_year"])
      for offset, field in enumerate(("thstrm_amount", "frmtrm_amount", "bfefrmtrm_amount")):
        amount = parse_dart_amount(row.get(field))
        if amount is None:
          continue
        rows.append(
          {
            "agency": agency,
            "label": label,
            "year": base_year - offset,
            "account": account,
            "amount": amount / WON_PER_EOK,
          }
        )

  return pl.DataFrame(rows, schema=FINANCIALS_SCHEMA)


def with_operating_margin(financials: pl.DataFrame) -> pl.DataFrame:
  """회사·연도별 매출액/영업이익/영업이익률(%) wide 표. 매출이 0 이하면 이익률은 null."""
  wide = financials.pivot(on="account", index=["agency", "label", "year"], values="amount")
  if REVENUE not in wide.columns or OPERATING_PROFIT not in wide.columns:
    return pl.DataFrame(
      schema={"agency": pl.String, "label": pl.String, "year": pl.Int64, REVENUE: pl.Float64, OPERATING_PROFIT: pl.Float64, "margin": pl.Float64}
    )
  return wide.with_columns(
    pl.when(pl.col(REVENUE) > 0)
    .then(pl.col(OPERATING_PROFIT) / pl.col(REVENUE) * 100)
    .otherwise(None)
    .alias("margin")
  ).sort(["agency", "year"])


def yoy_pct(current: float | None, previous: float | None) -> float | None:
  """전년 대비 증감률(%). 전년 값이 0 이하이면(적자 등) 비율이 무의미하므로 None."""
  if current is None or previous is None or previous <= 0:
    return None
  return (current - previous) / previous * 100


def summarize_totals(financials: pl.DataFrame, expected_agencies: int) -> dict[str, tuple[float, float]] | None:
  """최신 연도 기준 계정별 (당기 합계, 전기 합계). 억 원.

  대상 회사 중 하나라도 최신·직전 연도 값이 빠져 있으면 합산이 왜곡되므로 None을
  돌려줘 호출 쪽이 KPI를 만들지 않게 한다. 결과에 "year" 키는 없고, 연도는
  latest_year()로 따로 얻는다."""
  if financials.height == 0:
    return None
  year = int(financials["year"].max())

  totals: dict[str, tuple[float, float]] = {}
  for account in ACCOUNTS:
    current = financials.filter((pl.col("account") == account) & (pl.col("year") == year))
    previous = financials.filter((pl.col("account") == account) & (pl.col("year") == year - 1))
    if current["agency"].n_unique() != expected_agencies or previous["agency"].n_unique() != expected_agencies:
      return None
    totals[account] = (float(current["amount"].sum()), float(previous["amount"].sum()))
  return totals


def latest_year(financials: pl.DataFrame) -> int | None:
  return int(financials["year"].max()) if financials.height > 0 else None
