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
        torch = self._load()
        tokenizer = self._tokenizer
        model = self._model
        assert tokenizer is not None and model is not None

        batch = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=1024,
            return_tensors="pt",
        )
        batch = {k: v.to(self.device) for k, v in batch.items()}

        with torch.no_grad():
            outputs = model(**batch)

        last = outputs.last_hidden_state  # [B, T, H]
        if self.config.pooling == "cls":
            pooled = last[:, 0, :]
        else:
            pooled = last.mean(dim=1)

        return l2_normalize(pooled.detach().cpu().numpy())


# ---------------------------------------------------------------------------
# Backward-compatibility aliases (deprecated — will be removed)
# ---------------------------------------------------------------------------

SonarConfig = BgeM3Config
SonarEmbedder = BgeM3Embedder
CanineConfig = ByT5Config
CanineEmbedder = ByT5Embedder
