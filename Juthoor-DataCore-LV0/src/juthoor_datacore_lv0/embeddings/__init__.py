"""
LV0 Embeddings Module - Data pipeline embedding utilities.

NOTE: This module contains CLI scripts for batch embedding generation.
The actual embedding models (BgeM3Embedder, ByT5Embedder) are implemented
in the LV2 cognate discovery module.

For production embeddings, use:
    from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
        BgeM3Embedder,
        ByT5Embedder,
        BgeM3Config,
        ByT5Config,
    )

The scripts in this module (embed_sonar.py, embed_canine.py) provide CLI
interfaces that delegate to the LV2 embedders for batch processing.
"""

__all__: list[str] = []
