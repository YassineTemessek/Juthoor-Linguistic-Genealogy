"""
Juthoor CognateDiscovery LV2: Cross-lingual similarity scoring and retrieval.

This module provides tools for discovering cognates across languages using:
- SONAR: Multilingual semantic embeddings (meaning-based)
- CANINE: Character-level form embeddings (orthography-based)
- Hybrid scoring: Combines multiple similarity signals

Main Components:
    - lv3.discovery.embeddings: SonarEmbedder, CanineEmbedder
    - lv3.discovery.hybrid_scoring: HybridWeights, compute_hybrid
    - lv3.discovery.index: FAISS index utilities
    - lv3.discovery.jsonl: JSONL I/O utilities
    - lv3.discovery.lang: Language code mapping

Usage:
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import SonarEmbedder
    from juthoor_cognatediscovery_lv2.lv3.discovery.hybrid_scoring import compute_hybrid
"""

__version__ = "0.1.0"
