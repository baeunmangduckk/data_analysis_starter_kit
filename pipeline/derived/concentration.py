"""circlechart Top100 판매 데이터에서 판매 집중도를 계산한다.

레거시 real_kpop_future의 concentration.py(Gini/Top10·20/Bottom50 점유율)
로직을 이 프로젝트의 Polars 기반 스타일로 재구현한 것이다. circlechart의
`de_nm`(유통사) 필드는 실제 소속사가 아니므로(레거시 스크래퍼 경고), 여기서는
순위(rank) 기반 판매량 집중도만 계산하고 에이전시별 분류는 시도하지 않는다.
에이전시별 매출 비중은 pipeline/collectors/dart.py가 담당한다.
"""

from __future__ import annotations

import polars as pl


def parse_album_records(raw_list: dict) -> pl.DataFrame:
  """circlechart API의 List(딕셔너리, 키가 "0","1",...인 형태)를
  rank/sales/artist/album 컬럼을 가진 DataFrame으로 정리한다."""
  rows = []
  for record in raw_list.values():
    rows.append(
      {
        "rank": int(record["SERVICE_RANKING"]),
        "sales": float(record["Album_CNT"]),
        "artist": record["ARTIST_NAME"],
        "album": record["ALBUM_NAME"],
      }
    )
  return pl.DataFrame(rows).sort("rank")


def compute_gini(sales: list[float]) -> float:
  """0(완전 균등)~1(완전 쏠림) 사이의 지니계수를 계산한다."""
  values = sorted(v for v in sales if v > 0)
  n = len(values)
  total = sum(values)
  if n == 0 or total == 0:
    return 0.0
  weighted_sum = sum((2 * i - n - 1) * v for i, v in enumerate(values, start=1))
  return weighted_sum / (n * total)


def compute_shares(albums: pl.DataFrame) -> pl.DataFrame:
  """Top10 / Top11-20 / Bottom(21위 이하) 판매 비중을 계산해
  build_distribution()이 바로 쓸 수 있는 category/label/value 형태로 반환한다."""
  top10 = albums.filter(pl.col("rank") <= 10)["sales"].sum()
  top11_20 = albums.filter((pl.col("rank") > 10) & (pl.col("rank") <= 20))["sales"].sum()
  bottom = albums.filter(pl.col("rank") > 20)["sales"].sum()

  return pl.DataFrame(
    [
      {"category": "Top10", "label": "Top 10", "value": float(top10)},
      {"category": "Top11_20", "label": "Top 11-20", "value": float(top11_20)},
      {"category": "Bottom", "label": "21위 이하", "value": float(bottom)},
    ]
  )
