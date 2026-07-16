"""Okapi BM25 lexical ranking — real information retrieval, zero dependencies.

Used by context selection to rank candidate files by relevance to the task
objective, replacing name-based heuristics with term-frequency evidence. ~50
lines of pure Python; the classic k1/b parameterization.
"""

from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9_]{2,}")
_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "not",
    "una", "los", "las", "del", "por", "para", "con", "que", "este", "esta",
}


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


class BM25:
    def __init__(self, corpus: dict[str, str], *, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._tf: dict[str, Counter] = {}
        self._doc_len: dict[str, int] = {}
        df: Counter = Counter()
        for doc_id, text in corpus.items():
            tokens = tokenize(text)
            self._tf[doc_id] = Counter(tokens)
            self._doc_len[doc_id] = len(tokens)
            df.update(set(tokens))
        self._n = len(corpus)
        self._avgdl = (sum(self._doc_len.values()) / self._n) if self._n else 0.0
        # BM25+-style floor keeps idf non-negative for very common terms.
        self._idf = {
            term: max(0.0, math.log((self._n - freq + 0.5) / (freq + 0.5) + 1.0))
            for term, freq in df.items()
        }

    def score(self, query: str, doc_id: str) -> float:
        tf = self._tf.get(doc_id)
        if not tf or not self._avgdl:
            return 0.0
        dl = self._doc_len[doc_id]
        total = 0.0
        for term in tokenize(query):
            if term not in tf:
                continue
            freq = tf[term]
            idf = self._idf.get(term, 0.0)
            total += idf * (freq * (self.k1 + 1)) / (
                freq + self.k1 * (1 - self.b + self.b * dl / self._avgdl)
            )
        return total

    def scores(self, query: str) -> dict[str, float]:
        return {doc_id: self.score(query, doc_id) for doc_id in self._tf}
