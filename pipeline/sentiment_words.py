"""워드클라우드 감성 분류용 긍정/부정 단어 사전.

build_wordcloud()가 텍스트 토큰에 이 단어들이 포함되는지로 감성을 판정한다.
단어를 추가/삭제하면 바로 분류 결과에 반영된다.
"""

POSITIVE_WORDS: list[str] = [
  "친절", "만족", "빠르", "좋", "훌륭", "추천", "편리", "감사",
  # YouTube 댓글 등 팬덤 반응 텍스트 확장 어휘
  "소름", "역대급", "미쳤", "대박", "찢었", "자랑스럽", "완벽", "믿듣",
]

NEGATIVE_WORDS: list[str] = [
  "불편", "아쉽", "느리", "불만", "실망", "불친절", "비싸",
  # YouTube 댓글 등 팬덤 반응 텍스트 확장 어휘 — "조작"/"사재기"처럼
  # 차트 신뢰도 논쟁에서 자주 쓰이는 부정 표현 포함
  "조작", "사재기", "표절", "노잼", "실망스럽", "악플",
]

# 영어 댓글용 감성 사전. 한국어와 달리 "whatever"에 "hate"가 들어 있는 것처럼
# 부분 문자열 오분류가 잦아, 토큰 완전 일치(set)로만 판정한다.
POSITIVE_WORDS_EN: set[str] = {
  "love", "loved", "great", "good", "amazing", "best", "awesome", "beautiful",
  "nice", "perfect", "talented", "fantastic", "incredible", "excellent", "proud",
}

NEGATIVE_WORDS_EN: set[str] = {
  "bad", "hate", "fake", "boring", "trash", "worst", "scam", "overrated",
  "manufactured", "rigged", "problem", "toxic", "greedy", "unfair",
}

# 워드클라우드 빈도 집계에서 제외할 불용어. 감성/주제 정보가 없는 기능어와
# URL 조각이 상위 빈도를 독점하지 않도록 한다.
STOPWORDS: set[str] = {
  "the", "and", "to", "is", "a", "of", "i", "that", "they", "in", "are", "it",
  "for", "you", "not", "their", "with", "but", "or", "as", "have", "this", "just",
  "about", "so", "be", "all", "was", "if", "on", "can", "what", "there", "at",
  "do", "them", "we", "an", "more", "one", "my", "your", "from", "has", "when",
  "will", "who", "how", "because", "than", "its", "me", "he", "she", "his", "her",
  "would", "were", "been", "no", "out", "up", "don't", "it's", "i'm", "like",
  "even", "also", "only", "some", "much", "really", "get", "make", "people",
  "why", "these", "those", "by", "into", "where", "know", "see", "want", "think",
  "now", "still", "thing", "things", "never", "being", "same", "way", "which",
  "then", "too", "very", "many", "most", "other", "their", "our", "us", "had",
  "did", "does", "could", "should", "any", "over", "after", "before", "while",
  "him", "them", "say", "said", "going", "got", "let", "every", "always",
  "http", "https", "www", "com", "youtube",
  "그리고", "하지만", "그냥", "이거", "저거", "그래서", "근데", "이제",
}
