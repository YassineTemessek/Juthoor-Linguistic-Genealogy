param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "LV2 no longer owns ingest. Fetch/build processed data via LV0, then run graph export with an explicit input path."
Write-Host "Example: $Python scripts/graph/export_binary_root_graph.py --input <binary_root_lexicon.jsonl>"
