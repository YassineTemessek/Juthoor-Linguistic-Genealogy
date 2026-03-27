# Full Discovery Pipeline Report

**Timestamp:** 20260327_171534  
**Mode:** fast  
**Arabic corpus:** 1952 entries  
**English corpus:** 20526 entries  
**Runtime:** 6795.8s  

## Summary

- Total leads generated: 25590
- Leads above 0.45 threshold: 25590
- Leads above 0.70: 25590
- Leads above 0.85: 24739

## Benchmark Evaluation (ara<->eng gold)

- **gold_count:** 837
- **found_in_leads:** 85
- **coverage:** 0.1016
- **MRR:** 0.0
- **Hit@1:** 0.0
- **Hit@5:** 0.0
- **Hit@10:** 0.0
- **Hit@20:** 0.0
- **Hit@50:** 0.0
- **Hit@100:** 0.0
- **total_leads:** 25590

## Top 30 Leads

| Rank | Arabic | Root | English | IPA | Score | Method | Explanation |
|------|--------|------|---------|-----|-------|--------|-------------|
| 1 | اسْم | سمو | sipa | sipə | 1.000 | multi_hop_chain | Latin/Greek hop: 'سم' → 'sp' ↔ 'sp' |
| 2 | اسْم | سمو | soap | soʊp | 1.000 | multi_hop_chain | Latin/Greek hop: 'سم' → 'sp' ↔ 'sp' |
| 3 | اسْم | سمو | suv | ɛsjuvi | 1.000 | multi_hop_chain | Latin/Greek hop: 'سم' → 'sv' ↔ 'sv' |
| 4 | اسْم | سمو | sob | sɒb | 1.000 | multi_hop_chain | Latin/Greek hop: 'سم' → 'sb' ↔ 'sb' |
| 5 | اسْم | سمو | soup | sup | 1.000 | multi_hop_chain | Latin/Greek hop: 'سم' → 'sp' ↔ 'sp' |
| 6 | اسْم | سمو | spie | spi | 1.000 | multi_hop_chain | Latin/Greek hop: 'سم' → 'sp' ↔ 'sp' |
| 7 | اسْم | سمو | sub | sʌb | 1.000 | multi_hop_chain | Latin/Greek hop: 'سم' → 'sb' ↔ 'sb' |
| 8 | اسْم | سمو | sieve | sɪv | 1.000 | multi_hop_chain | Latin/Greek hop: 'سم' → 'sv' ↔ 'sv' |
| 9 | اسْم | سمو | semitism | sɛmɪtɪzəm | 1.000 | reverse_root | Reverse-generated 'جسم' from 'tsm', matched Arabic 'جسم' |
| 10 | اسْم | سمو | summy | sʌmi | 1.000 | ipa_scoring | IPA skeleton 'sm' matched projection 'sm' |
| 11 | اسْم | سمو | seam | sim | 1.000 | reverse_root | Reverse-generated 'سم' from 'sm', matched Arabic 'سم' |
| 12 | اسْم | سمو | summer | sʌmɝ | 1.000 | morpheme_decomposition | Stripped prefix='' suffix='er', stem 'summ' matched Arabic ' |
| 13 | اسْم | سمو | sima | simʌ | 1.000 | reverse_root | Reverse-generated 'سم' from 'sm', matched Arabic 'سم' |
| 14 | اسْم | سمو | osama | oʊsɑmə | 1.000 | reverse_root | Reverse-generated 'سم' from 'sm', matched Arabic 'سم' |
| 15 | اسْم | سمو | sameer | sɑmɪɹ | 1.000 | reverse_root | Reverse-generated 'سم' from 'sm', matched Arabic 'سم' |
| 16 | اسْم | سمو | samovar | sæmuːvɑː | 1.000 | ipa_scoring | IPA skeleton 'smv' matched projection 'smv' |
| 17 | اسْم | سمو | summary | sʌmɝi | 1.000 | morpheme_decomposition | Stripped prefix='' suffix='ary', stem 'summ' matched Arabic  |
| 18 | اسْم | سمو | sum | səm | 1.000 | reverse_root | Reverse-generated 'سم' from 'sm', matched Arabic 'سم' |
| 19 | اسْم | سمو | sohmer | soʊmɝ | 1.000 | reverse_root | Reverse-generated 'جسم' from 'shm', matched Arabic 'جسم' |
| 20 | اسْم | سمو | same | seɪm | 1.000 | reverse_root | Reverse-generated 'سم' from 'sm', matched Arabic 'سم' |
| 21 | اللَّه | أله | lecher | lɛtʃɐ | 1.000 | ipa_scoring | IPA skeleton 'ɫk' matched projection 'lk' |
| 22 | اللَّه | أله | lohner | loʊnɝ | 1.000 | direct_skeleton | Arabic skeleton 'لهله' projects to 'lhlh', matched 'lhn' |
| 23 | اللَّه | أله | alpha | ælfɐ | 1.000 | ipa_scoring | IPA skeleton 'lf' matched projection 'lʕf' |
| 24 | اللَّه | أله | laham | læhʌm | 1.000 | direct_skeleton | Arabic skeleton 'لهب' projects to 'lhb', matched 'lhm' |
| 25 | اللَّه | أله | loath | ɫoʊθ | 1.000 | direct_skeleton | Arabic skeleton 'لهث' projects to 'lhth', matched 'lth' |
| 26 | اللَّه | أله | lehn | lɛn | 1.000 | direct_skeleton | Arabic skeleton 'لهله' projects to 'lhlh', matched 'lhn' |
| 27 | اللَّه | أله | beulah | bjulʌ | 1.000 | direct_skeleton | Arabic skeleton 'برح' projects to 'brh', matched 'blh' |
| 28 | اللَّه | أله | leith | liθ | 1.000 | direct_skeleton | Arabic skeleton 'لهث' projects to 'lhth', matched 'lth' |
| 29 | اللَّه | أله | leah | liʌ | 1.000 | multi_hop_chain | Latin/Greek hop: 'له' → 'lh' ↔ 'lh' |
| 30 | اللَّه | أله | lehr | ɫɛɹ | 1.000 | direct_skeleton | Arabic skeleton 'لهله' projects to 'lhlh', matched 'lhr' |

## Method Distribution

- `direct_skeleton`: 7619
- `position_weighted`: 4612
- `morpheme_decomposition`: 3615
- `ipa_scoring`: 3575
- `reverse_root`: 3172
- `multi_hop_chain`: 1451
- `metathesis`: 830
- `emphatic_collapse`: 342
- `guttural_projection`: 323
- `article_detection`: 51
