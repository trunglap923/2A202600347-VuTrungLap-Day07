from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
            
        parts = re.split(r'(\. |\! |\? |\.\n)', text)
        sentences = []
        current = ""
        for p in parts:
            current += p
            if p in {". ", "! ", "? ", ".\n"}:
                sentences.append(current.strip())
                current = ""
        if current.strip():
            sentences.append(current.strip())
            
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[i:i + self.max_sentences_per_chunk])
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size or not remaining_separators:
            if len(current_text) > self.chunk_size:
                return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
            return [current_text]

        sep = remaining_separators[0]
        splits = current_text.split(sep) if sep else list(current_text)
        
        good_splits = []
        for s in splits:
            if len(s) > self.chunk_size:
                good_splits.extend(self._split(s, remaining_separators[1:]))
            else:
                if s:
                    good_splits.append(s)

        merged_chunks = []
        current_chunk = good_splits[0] if good_splits else ""
        for i in range(1, len(good_splits)):
            s = good_splits[i]
            merged_len = len(current_chunk) + len(sep) + len(s) if current_chunk else len(s)
            
            if merged_len <= self.chunk_size:
                current_chunk = current_chunk + sep + s if current_chunk else s
            else:
                if current_chunk:
                    merged_chunks.append(current_chunk)
                current_chunk = s
                
        if current_chunk:
            merged_chunks.append(current_chunk)
            
        return merged_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0
    dot_prod = _dot(vec_a, vec_b)
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_prod / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fix_c = FixedSizeChunker(chunk_size=chunk_size, overlap=20)
        fix_res = fix_c.chunk(text)
        
        sent_c = SentenceChunker(max_sentences_per_chunk=max(1, chunk_size // 50))
        sent_res = sent_c.chunk(text)
        
        rec_c = RecursiveChunker(chunk_size=chunk_size)
        rec_res = rec_c.chunk(text)
        
        def stats(chunks):
            return {
                "count": len(chunks),
                "avg_length": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                "chunks": chunks
            }
            
        return {
            "fixed_size": stats(fix_res),
            "by_sentences": stats(sent_res),
            "recursive": stats(rec_res)
        }

class MarkdownChunker:
    """
    Split text by Markdown headings (## or ###).
    Falls back to RecursiveChunker if a chunk is still too long.
    """
    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
            
        splits = re.split(r'(?=\n#{2,3} )', text)
        
        final_chunks = []
        for s in splits:
            s_clean = s.strip()
            if not s_clean:
                continue
                
            if len(s_clean) <= self.chunk_size:
                final_chunks.append(s_clean)
            else:
                final_chunks.extend(self.fallback.chunk(s_clean))
                
        return final_chunks
