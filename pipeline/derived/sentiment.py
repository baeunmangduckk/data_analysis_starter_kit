"""댓글 텍스트의 토큰화·단어 빈도·감성 분류.

홈의 워드클라우드(etl.build_wordcloud)와 팬 반응 페이지(pages/fans.py)가 같은 규칙을 쓰도록
한 곳에 모았다. 감성 사전은 pipeline/sentiment_words.py에서 관리한다.
"""

from __future__ import annotations

import re
from collections import Counter

from pipeline.models import SentimentLabel, WordCloudItem
from pipeline.sentiment_words import (
  NEGATIVE_WORDS,
  NEGATIVE_WORDS_EN,
  POSITIVE_WORDS,
  POSITIVE_WORDS_EN,
  STOPWORDS,
)


def tokenize(comment: str) -> list[str]:
  """영단어/한글 덩어리만 추출해 구두점·이모지를 제거하고, 1글자와 불용어는 뺀다."""
  return [
    token
    for token in re.findall(r"[a-z']+|[가-힣]+", comment.lower())
    if len(token) > 1 and token not in STOPWORDS
  ]


def classify_token(token: str) -> SentimentLabel:
  # 부정 단어를 먼저 검사한다 — "불친절"처럼 부정 표현이 긍정 단어("친절")를
  # 부분 문자열로 포함하는 경우가 있어, 순서를 바꾸면 오분류가 발생한다.
  # 영어는 부분 문자열 오분류를 피하려고 완전 일치로만 판정한다.
  if token in NEGATIVE_WORDS_EN or any(word in token for word in NEGATIVE_WORDS):
    return "negative"
  if token in POSITIVE_WORDS_EN or any(word in token for word in POSITIVE_WORDS):
    return "positive"
  return "neutral"


def top_words(comments: list[str], limit: int = 30) -> list[WordCloudItem]:
  """전체 댓글의 단어 빈도 상위 limit개와 단어별 감성."""
  counts = Counter(token for comment in comments for token in tokenize(comment))
  return [
    WordCloudItem(text=text, weight=float(weight), sentiment=classify_token(text))
    for text, weight in counts.most_common(limit)
  ]


def comment_sentiment(comment: str) -> SentimentLabel:
  """댓글 한 개의 감성: 긍정/부정 단어 수를 비교해 많은 쪽으로, 같으면 중립으로 본다."""
  labels = [classify_token(token) for token in tokenize(comment)]
  positive, negative = labels.count("positive"), labels.count("negative")
  if positive > negative:
    return "positive"
  if negative > positive:
    return "negative"
  return "neutral"


def sentiment_counts(comments: list[str]) -> dict[SentimentLabel, int]:
  """댓글 단위 감성 분포 (긍정/부정/중립 댓글 수)."""
  counts: dict[SentimentLabel, int] = {"positive": 0, "negative": 0, "neutral": 0}
  for comment in comments:
    counts[comment_sentiment(comment)] += 1
  return counts
