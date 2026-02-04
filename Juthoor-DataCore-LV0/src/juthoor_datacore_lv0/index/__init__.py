"""
LV0 Index Module - FAISS index building utilities.

This module provides scripts for building FAISS vector indexes from embeddings.

NOTE: For runtime index operations in cognate discovery, prefer using the
LV2 module which has a more complete API:

    from juthoor_cognatediscovery_lv2.lv3.discovery.index import (
        FaissIndex,
        build_flat_ip,
    )

The build_faiss.py script in this module is for batch index generation
during the data pipeline.
"""

__all__: list[str] = []
