from __future__ import annotations

from dataclasses import dataclass


def _require(module: str, *, install_hint: str) -> None:
    try:
        __import__(module)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Missing dependency `{module}`. {install_hint}\nOriginal error: {exc}") from exc


def l2_normalize(vectors):
    import numpy as np

    vectors = np.asarray(vectors, dtype="float32")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


# ---------------------------------------------------------------------------
# Cost estimation helpers (for API backend)
# ---------------------------------------------------------------------------

_GEMINI_FREE_TIER_TOKENS = 3_500_000
_GEMINI_PRICE_PER_MILLION = 0.15  # USD, paid tier


def estimate_tokens(texts: list[str]) -> int:
    """Rough token count for short lexeme strings (~1.2 tokens per word)."""
    return max(1, int(sum(max(1, len(t.split()) * 1.2) for t in texts)))


def estimate_cost(
    n_tokens: int,
    *,
    price_per_million: float = _GEMINI_PRICE_PER_MILLION,
    free_tier: int = _GEMINI_FREE_TIER_TOKENS,
) -> tuple[float, bool]:
    """Return (cost_usd, is_free). Cost is 0.0 when within free tier."""
    if n_tokens <= free_tier:
        return 0.0, True
    return round(n_tokens * price_per_million / 1_000_000, 4), False


# ---------------------------------------------------------------------------
# Semantic embeddings: BGE-M3 (replaces Meta SONAR)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BgeM3Config:
    model_id: str = "BAAI/bge-m3"
    use_fp16: bool = True
    max_length: int = 8192


class BgeM3Embedder:
    """Multilingual semantic embedder using BGE-M3 (dense retrieval mode).

    BGE-M3 is language-agnostic: no language code required.
    Output: L2-normalized 1024-dim vectors (same as former SONAR output).
    """

    def __init__(self, *, config: BgeM3Config | None = None):
        self.config = config or BgeM3Config()
        self._model = None

    def _get_model(self):
        _require(
            "FlagEmbedding",
            install_hint="Install: `pip install FlagEmbedding`.",
        )
        from FlagEmbedding import BGEM3FlagModel

        if self._model is None:
            self._model = BGEM3FlagModel(
                self.config.model_id,
                use_fp16=self.config.use_fp16,
            )
        return self._model

    def embed(self, texts: list[str]) -> "np.ndarray":
        import numpy as np

        model = self._get_model()
        output = model.encode(
            texts,
            batch_size=12,
            max_length=self.config.max_length,
        )
        vecs = np.asarray(output["dense_vecs"], dtype="float32")
        return l2_normalize(vecs)


# ---------------------------------------------------------------------------
# Form/character-level embeddings: ByT5 (replaces Google CANINE)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ByT5Config:
    model_id: str = "google/byt5-small"
    pooling: str = "mean"  # "mean" | "cls"
    batch_size: int = 16


class ByT5Embedder:
    """Byte-level form embedder using ByT5 encoder (tokenizer-free).

    ByT5 processes raw bytes without tokenization, making it ideal for
    multilingual orthographic similarity across scripts.
    Output: L2-normalized vectors (1472-dim for byt5-small).
    """

    def __init__(self, *, config: ByT5Config | None = None, device: str = "cpu"):
        self.config = config or ByT5Config()
        self.device = device
        self._tokenizer = None
        self._model = None

    def _load(self):
        _require(
            "transformers",
            install_hint="Install: `pip install transformers torch`.",
        )
        _require(
            "torch",
            install_hint="Install: `pip install torch`.",
        )
        import torch
        from transformers import AutoTokenizer, T5EncoderModel

        if self._tokenizer is None:
            self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_id)
        if self._model is None:
            self._model = T5EncoderModel.from_pretrained(self.config.model_id)
            self._model.eval()
            self._model.to(self.device)
        return torch

    def embed(self, texts: list[str]) -> "np.ndarray":
        import numpy as np

        torch = self._load()
        tokenizer = self._tokenizer
        model = self._model
        assert tokenizer is not None and model is not None

        all_vecs: list["np.ndarray"] = []
        bs = self.config.batch_size
        for i in range(0, len(texts), bs):
            chunk = tokenizer(
                texts[i : i + bs],
                padding=True,
                truncation=True,
                max_length=1024,
                return_tensors="pt",
            )
            chunk = {k: v.to(self.device) for k, v in chunk.items()}

            with torch.no_grad():
                outputs = model(**chunk)

            last = outputs.last_hidden_state  # [B, T, H]
            if self.config.pooling == "cls":
                pooled = last[:, 0, :]
            else:
                pooled = last.mean(dim=1)
            all_vecs.append(pooled.detach().cpu().numpy())

        return l2_normalize(np.concatenate(all_vecs, axis=0))


# ---------------------------------------------------------------------------
# API embeddings: Gemini embedding-001 (no local GPU needed)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GeminiConfig:
    """Configuration for Gemini embedding-001 API."""

    model_id: str = "gemini-embedding-001"
    dimensions: int = 1024  # flexible; matches BGE-M3 default
    task_type: str = "SEMANTIC_SIMILARITY"  # or "RETRIEVAL_DOCUMENT"
    batch_size: int = 100


_PINNED_GEMINI_MODEL = "gemini-embedding-001"


class GeminiEmbedder:
    """Gemini embedding-001 via Google GenAI API (no local GPU needed).

    Requires ``google-genai`` package and ``GOOGLE_API_KEY`` env var.
    Output: L2-normalized vectors of configurable dimensionality.
    """

    def __init__(self, *, config: GeminiConfig | None = None):
        self.config = config or GeminiConfig()
        if self.config.model_id != _PINNED_GEMINI_MODEL:
            import warnings
            warnings.warn(
                f"Non-default Gemini model '{self.config.model_id}' selected. "
                f"The pinned model is '{_PINNED_GEMINI_MODEL}'. "
                f"Different models may have different pricing.",
                UserWarning,
                stacklevel=2,
            )
        self._client = None

    def _get_client(self):
        _require(
            "google.genai",
            install_hint="Install: `pip install google-genai`.",
        )
        if self._client is None:
            from google import genai

            self._client = genai.Client()
        return self._client

    def embed(self, texts: list[str]) -> "np.ndarray":
        import numpy as np
        from google.genai import types

        client = self._get_client()
        cfg = self.config
        all_vecs: list[list[float]] = []

        for i in range(0, len(texts), cfg.batch_size):
            batch = texts[i : i + cfg.batch_size]
            result = client.models.embed_content(
                model=cfg.model_id,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=cfg.task_type,
                    output_dimensionality=cfg.dimensions,
                ),
            )
            for emb in result.embeddings:
                all_vecs.append(emb.values)

        vecs = np.asarray(all_vecs, dtype="float32")
        return l2_normalize(vecs)


# ---------------------------------------------------------------------------
# Backward-compatibility aliases (deprecated — will be removed)
# ---------------------------------------------------------------------------

SonarConfig = BgeM3Config
SonarEmbedder = BgeM3Embedder
CanineConfig = ByT5Config
CanineEmbedder = ByT5Embedder
