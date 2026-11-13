import enum
import re
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChunkStrategy(str, enum.Enum):
    FIXED_SIZE = "FIXED_SIZE"
    SEMANTIC = "SEMANTIC"
    CODE_AWARE = "CODE_AWARE"
    SENTENCE = "SENTENCE"


class ChunkResult(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    strategy: str


def estimate_token_count(text: str) -> int:
    """Estimates token count: max of words * 1.3 or chars / 4."""
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    return max(1, int(max(words * 1.3, chars / 4)))


class TextChunker:
    """
    Production-grade text chunker implementing 4 strategies:
    - FIXED_SIZE: 512 tokens with 50-token overlap
    - SEMANTIC: Paragraph and markdown heading splits (100-800 tokens)
    - CODE_AWARE: Function/class splits preserving module imports
    - SENTENCE: 3-5 sentence grouped chunks
    """

    @classmethod
    def chunk_fixed_size(
        cls,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ChunkResult]:
        if not text or not text.strip():
            return []

        base_meta = metadata or {}
        # Use word-level chunks for realistic token approximation
        words = text.split()
        if not words:
            return []

        # Target words roughly chunk_size / 1.3
        target_words = max(10, int(chunk_size / 1.3))
        overlap_words = max(1, int(overlap / 1.3))

        chunks: List[ChunkResult] = []
        start_idx = 0
        chunk_idx = 0

        while start_idx < len(words):
            end_idx = min(start_idx + target_words, len(words))
            chunk_words = words[start_idx:end_idx]
            content = " ".join(chunk_words)

            tokens = estimate_token_count(content)
            chunk_meta = {
                **base_meta,
                "chunk_index": chunk_idx,
                "strategy": ChunkStrategy.FIXED_SIZE.value,
                "word_count": len(chunk_words),
            }

            chunks.append(
                ChunkResult(
                    chunk_id=str(uuid.uuid4()),
                    content=content,
                    token_count=tokens,
                    metadata=chunk_meta,
                    strategy=ChunkStrategy.FIXED_SIZE.value,
                )
            )

            chunk_idx += 1
            if end_idx >= len(words):
                break
            start_idx += max(1, target_words - overlap_words)

        return chunks

    @classmethod
    def chunk_semantic(
        cls,
        text: str,
        min_tokens: int = 20,
        max_tokens: int = 800,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ChunkResult]:
        if not text or not text.strip():
            return []

        base_meta = metadata or {}
        # Split on markdown headings or double newlines
        sections = re.split(r"(?=\n#{1,4}\s)|(?:\n\s*\n)", text)
        sections = [s.strip() for s in sections if s.strip()]

        chunks: List[ChunkResult] = []
        current_buffer: List[str] = []
        current_tokens = 0
        current_heading = "General"
        chunk_idx = 0

        for section in sections:
            heading_match = re.match(r"^(#{1,4}\s+[^\n]+)", section)
            new_heading = heading_match.group(1).lstrip("#").strip() if heading_match else None

            sec_tokens = estimate_token_count(section)

            # If section starts a new heading and buffer already has min_tokens, flush current chunk
            if heading_match and current_buffer and current_tokens >= min_tokens:
                content = "\n\n".join(current_buffer)
                chunks.append(
                    ChunkResult(
                        chunk_id=str(uuid.uuid4()),
                        content=content,
                        token_count=estimate_token_count(content),
                        metadata={
                            **base_meta,
                            "chunk_index": chunk_idx,
                            "section": current_heading,
                            "strategy": ChunkStrategy.SEMANTIC.value,
                        },
                        strategy=ChunkStrategy.SEMANTIC.value,
                    )
                )
                chunk_idx += 1
                current_buffer = [section]
                current_tokens = sec_tokens
                current_heading = new_heading or current_heading
                continue

            if new_heading:
                current_heading = new_heading

            # If section itself exceeds max_tokens, split it fixed-size
            if sec_tokens > max_tokens:
                # Flush existing buffer first
                if current_buffer:
                    content = "\n\n".join(current_buffer)
                    chunks.append(
                        ChunkResult(
                            chunk_id=str(uuid.uuid4()),
                            content=content,
                            token_count=estimate_token_count(content),
                            metadata={
                                **base_meta,
                                "chunk_index": chunk_idx,
                                "section": current_heading,
                                "strategy": ChunkStrategy.SEMANTIC.value,
                            },
                            strategy=ChunkStrategy.SEMANTIC.value,
                        )
                    )
                    chunk_idx += 1
                    current_buffer = []
                    current_tokens = 0

                sub_chunks = cls.chunk_fixed_size(
                    section,
                    chunk_size=max_tokens,
                    overlap=50,
                    metadata={**base_meta, "section": current_heading},
                )
                for sc in sub_chunks:
                    sc.strategy = ChunkStrategy.SEMANTIC.value
                    sc.metadata["chunk_index"] = chunk_idx
                    chunks.append(sc)
                    chunk_idx += 1
                continue

            if current_tokens + sec_tokens > max_tokens and current_tokens >= min_tokens:
                # Flush buffer
                content = "\n\n".join(current_buffer)
                chunks.append(
                    ChunkResult(
                        chunk_id=str(uuid.uuid4()),
                        content=content,
                        token_count=estimate_token_count(content),
                        metadata={
                            **base_meta,
                            "chunk_index": chunk_idx,
                            "section": current_heading,
                            "strategy": ChunkStrategy.SEMANTIC.value,
                        },
                        strategy=ChunkStrategy.SEMANTIC.value,
                    )
                )
                chunk_idx += 1
                current_buffer = [section]
                current_tokens = sec_tokens
            else:
                current_buffer.append(section)
                current_tokens += sec_tokens

        if current_buffer:
            content = "\n\n".join(current_buffer)
            chunks.append(
                ChunkResult(
                    chunk_id=str(uuid.uuid4()),
                    content=content,
                    token_count=estimate_token_count(content),
                    metadata={
                        **base_meta,
                        "chunk_index": chunk_idx,
                        "section": current_heading,
                        "strategy": ChunkStrategy.SEMANTIC.value,
                    },
                    strategy=ChunkStrategy.SEMANTIC.value,
                )
            )

        return chunks

    @classmethod
    def chunk_code_aware(
        cls,
        code: str,
        language: str = "python",
        max_tokens: int = 600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ChunkResult]:
        if not code or not code.strip():
            return []

        base_meta = metadata or {}
        lines = code.splitlines()

        # Separate top-level imports and comments
        import_lines: List[str] = []
        body_lines: List[str] = []
        is_import_block = True

        for line in lines:
            stripped = line.strip()
            if is_import_block and (
                stripped.startswith("import ")
                or stripped.startswith("from ")
                or stripped.startswith("export * from")
                or stripped.startswith("export {")
                or stripped.startswith("//")
                or stripped.startswith("#")
                or stripped == ""
            ):
                import_lines.append(line)
            else:
                is_import_block = False
                body_lines.append(line)

        header_prefix = "\n".join(import_lines).strip()
        body_code = "\n".join(body_lines)

        # Regex for function / class definitions
        # Python: def / class, TS/JS: function / class / const ... = () =>
        def_pattern = re.compile(
            r"(?m)^(?=[ \t]*(?:def\s+[A-Za-z0-9_]+|class\s+[A-Za-z0-9_]+|export\s+(?:function|class|interface|type|const\s+[A-Za-z0-9_]+\s*=)|function\s+[A-Za-z0-9_]+))"
        )

        raw_blocks = def_pattern.split(body_code)
        blocks = [b.strip() for b in raw_blocks if b.strip()]

        if not blocks:
            # Fallback to fixed size if no distinct function/class definitions
            return cls.chunk_fixed_size(code, chunk_size=max_tokens, metadata=base_meta)

        chunks: List[ChunkResult] = []
        for idx, block in enumerate(blocks):
            # Include imports in the very first chunk
            if idx == 0 and header_prefix:
                block_content = f"{header_prefix}\n\n{block}"
            else:
                block_content = block

            # Extract entity name if found
            entity_match = re.search(
                r"(?:def|class|function|interface|type|const)\s+([A-Za-z0-9_]+)",
                block,
            )
            entity_name = entity_match.group(1) if entity_match else "code_block"

            chunk_meta = {
                **base_meta,
                "chunk_index": idx,
                "entity": entity_name,
                "language": language,
                "strategy": ChunkStrategy.CODE_AWARE.value,
            }

            chunks.append(
                ChunkResult(
                    chunk_id=str(uuid.uuid4()),
                    content=block_content,
                    token_count=estimate_token_count(block_content),
                    metadata=chunk_meta,
                    strategy=ChunkStrategy.CODE_AWARE.value,
                )
            )

        return chunks

    @classmethod
    def chunk_sentence(
        cls,
        text: str,
        sentences_per_chunk: int = 4,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ChunkResult]:
        if not text or not text.strip():
            return []

        base_meta = metadata or {}
        # Split on sentence boundaries: (. | ! | ?) followed by space, newline, or end
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        chunks: List[ChunkResult] = []
        for i in range(0, len(sentences), sentences_per_chunk):
            group = sentences[i : i + sentences_per_chunk]
            content = " ".join(group)
            chunk_idx = i // sentences_per_chunk

            chunk_meta = {
                **base_meta,
                "chunk_index": chunk_idx,
                "sentence_count": len(group),
                "strategy": ChunkStrategy.SENTENCE.value,
            }

            chunks.append(
                ChunkResult(
                    chunk_id=str(uuid.uuid4()),
                    content=content,
                    token_count=estimate_token_count(content),
                    metadata=chunk_meta,
                    strategy=ChunkStrategy.SENTENCE.value,
                )
            )

        return chunks

    @classmethod
    def chunk(
        cls,
        text: str,
        strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE,
        doc_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ChunkResult]:
        """Auto-dispatches to the optimal strategy based on strategy param or doc_type."""
        if not text or not text.strip():
            return []

        meta = metadata or {}
        dt = doc_type.lower()

        if strategy == ChunkStrategy.CODE_AWARE or dt in ("code", "python", "typescript", "ts", "py", "js"):
            lang = "python" if dt in ("py", "python") else "typescript"
            return cls.chunk_code_aware(text, language=lang, metadata=meta)
        elif strategy == ChunkStrategy.SEMANTIC or dt in ("markdown", "md", "adr"):
            return cls.chunk_semantic(text, metadata=meta)
        elif strategy == ChunkStrategy.SENTENCE:
            return cls.chunk_sentence(text, metadata=meta)
        else:
            return cls.chunk_fixed_size(text, metadata=meta)
