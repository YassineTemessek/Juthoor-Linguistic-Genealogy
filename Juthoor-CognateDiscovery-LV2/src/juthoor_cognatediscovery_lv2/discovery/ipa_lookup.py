"""IPA lookup for English words. Loads from the english_ipa_lookup.json compact corpus.

The compact corpus is built by scripts/build_ipa_lookup.py from the full
english_ipa_merged_pos.jsonl (88MB) and produces a ~4MB JSON keyed by lemma.
Loading is lazy — the file is only read on the first lookup call.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# IPA character sets
# ---------------------------------------------------------------------------

# IPA vowel symbols (broad set — covers most Latin-script IPA)
_IPA_VOWELS: frozenset[str] = frozenset(
    "aeiouɪɛæʌɒɔʊəɑɜɐɵøœɶɯɤɨʉ"
    # length marker, stress, syllable break are also stripped
)
_IPA_STRIP_RE = re.compile(
    r"[aeiouɪɛæʌɒɔʊəɑɜɐɵøœɶɯɤɨʉˈˌː\.ʔ̃]"
)

# IPA diphthong / affricate sequences that should be treated as single consonants
# We preserve these as two-char sequences when extracting the skeleton.
# (not strictly required for matching but good to know)
_AFFRICATES = {"tʃ", "dʒ", "ts", "dz"}


def _default_path() -> Path:
    """Return the default path for the compact IPA lookup JSON."""
    here = Path(__file__).resolve()
    # src/juthoor_cognatediscovery_lv2/discovery/ipa_lookup.py
    # parents: [0]=discovery, [1]=juthoor_cognate..., [2]=src, [3]=LV2_ROOT
    lv2_root = here.parents[3]
    return lv2_root / "data" / "processed" / "english_ipa_lookup.json"


class IPALookup:
    """Lazy-loading IPA lookup table for English lemmas.

    Parameters
    ----------
    corpus_path:
        Path to the compact ``english_ipa_lookup.json`` file. Defaults to the
        standard location inside the LV2 data directory.
    """

    def __init__(self, corpus_path: Optional[Path] = None) -> None:
        self._cache: dict[str, str] = {}
        self._loaded: bool = False
        self._path: Path = Path(corpus_path) if corpus_path is not None else _default_path()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if self._path.exists():
            with self._path.open("r", encoding="utf-8") as f:
                self._cache = json.load(f)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_ipa(self, lemma: str) -> Optional[str]:
        """Return the IPA transcription for an English *lemma*, or ``None``.

        Lookup is case-insensitive; the lemma is lowercased before lookup.
        """
        self._ensure_loaded()
        key = lemma.lower().strip()
        result = self._cache.get(key)
        if result is not None:
            return result
        # Try without leading apostrophe / hyphen (e.g. "'bout" -> "bout")
        stripped = key.lstrip("'-")
        if stripped != key:
            return self._cache.get(stripped)
        return None

    def ipa_consonant_skeleton(self, lemma: str) -> Optional[str]:
        """Return the IPA consonant skeleton for an English *lemma*, or ``None``.

        The skeleton strips all IPA vowel symbols, leaving only consonant
        characters. This gives a better consonant fingerprint than the
        orthographic skeleton for words with silent letters (e.g. "knight"
        → IPA /naɪt/ → skeleton "nt", not "knght").

        IPA vowels stripped: a e i o u ɪ ɛ æ ʌ ɒ ɔ ʊ ə ɑ ɜ ɐ ɵ ø œ ɶ ɯ ɤ ɨ ʉ
        Also strips stress markers (ˈ ˌ), length (ː), syllable break (.), glottal (ʔ),
        nasalisation (̃).
        """
        ipa = self.get_ipa(lemma)
        if ipa is None:
            return None
        skeleton = _IPA_STRIP_RE.sub("", ipa)
        # Remove any remaining whitespace
        skeleton = skeleton.strip()
        return skeleton if skeleton else None

    def __len__(self) -> int:
        self._ensure_loaded()
        return len(self._cache)

    def __contains__(self, lemma: str) -> bool:
        self._ensure_loaded()
        return lemma.lower().strip() in self._cache
