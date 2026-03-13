# Juthoor Expansion — New Concepts, Ideas & Experiments

> A roadmap of possibilities for deepening the Arabic Genome project,
> organized by theme. Each idea includes the concept, what it would prove
> or produce, and estimated complexity.

---

## A. DEEPER ANALYSIS OF THE EXISTING GENOME

### A1. Low-Score Root Investigation (Priority: HIGH)
**Concept:** The 143 roots scoring below 0.4 in semantic validation are the most
interesting — they either reveal *limits* of the binary root theory or *gaps* in
the current methodology. A systematic investigation would classify each into:
- (a) Genuine semantic drift over time (meaning evolved away from the nucleus)
- (b) Borrowing from non-Semitic languages (loanwords)
- (c) Metaphorical extension too abstract for embedding similarity
- (d) Data quality issues (wrong binary root assignment, ambiguous Muajam entry)

**Experiment:** Build a diagnostic script that cross-references low-scoring roots
against loanword databases, historical semantic shift records, and Quran usage
frequency. Produce a typology of *why* binary → tri-root meaning weakens.

**What it proves:** Whether the theory has principled boundaries or needs refinement.

---

### A2. Third-Letter Semantic Modulation Analysis
**Concept:** The theory says the 3rd letter *modulates* the binary root's meaning.
But how exactly? For each binary root family (e.g., بت with 5 tri-roots), measure:
- How much the 3rd letter shifts meaning direction
- Whether certain 3rd letters consistently play the same role across different
  binary root families (e.g., does ر always add "extension/flow"?)

**Experiment:** For each binary root family, compute pairwise semantic distances
between tri-root axial meanings. Then cluster by the *added letter* across all
families. If ل consistently adds a similar semantic "coloring" regardless of which
binary root it attaches to, that's powerful evidence for letter-level semantics.

**What it proves:** Quantifies whether each letter has a consistent semantic
"personality" across the entire language — the strongest test of phonosemantics.

---

### A3. Binary Root Semantic Field Mapping
**Concept:** Each binary root defines a semantic field. Map these fields
geometrically using embeddings. Are they evenly distributed in meaning-space,
or do they cluster into super-families?

**Experiment:** Embed all 457 binary root meanings with BGE-M3, then:
1. Run UMAP/t-SNE to visualize the 457-point semantic landscape
2. Apply HDBSCAN to find natural super-clusters
3. Check if super-clusters correlate with shared letters (e.g., do all بx roots
   cluster together? All xر roots?)

**What it proves:** Whether the "genome" has a higher-order structure — families
of binary roots that share semantic DNA through their letters.

---

### A4. Quranic Frequency × Semantic Coherence Correlation
**Concept:** 90% of Muajam roots have Quranic examples. Do roots that appear
more frequently in the Quran show higher or lower semantic coherence with their
binary root? Hypothesis: high-frequency Quranic roots may preserve ancient
meanings better.

**Experiment:** Cross-reference with a Quranic word frequency corpus. Correlate
frequency rank with semantic_score. Plot and test for significance.

---

### A5. Inverse Binary Root Pairs (Metathesis Study)
**Concept:** Arabic has a known phenomenon of root metathesis (letter swapping).
For each binary root like بت (cutting), check if the inverse تب also exists and
what its meaning is. Are inverted pairs semantically related, opposite, or random?

**Experiment:** Systematically compare all (X,Y) vs (Y,X) binary root pairs.
Compute semantic similarity between their meanings. Test whether inversions show
statistically higher similarity than random pairs.

**What it proves:** Whether letter *order* in the binary root carries information,
or whether the two letters form an unordered semantic unit.

---

## B. AI & NLP EXPERIMENTS

### B1. LLM-Powered Root Meaning Predictor
**Concept:** Train or fine-tune a model that, given a binary root meaning + a
third letter's intrinsic meaning, *predicts* the tri-root's axial meaning. This
would be a generative test of the theory.

**Experiment:** Use the 1,938 Muajam entries as training data. Input:
`binary_root_meaning + letter3_meaning → axial_meaning`. Evaluate with held-out
roots (e.g., 80/20 split). If the model can generate plausible axial meanings
for unseen roots, the theory has predictive power.

**Models to try:** Claude/GPT-4 few-shot, fine-tuned AraBERT, or a small
sequence-to-sequence model.

---

### B2. Embedding Space Arithmetic ("King - Man + Woman = Queen" for Arabic Roots)
**Concept:** Test whether semantic arithmetic works in the root genome. For
example: if بح means "uncovering/emptiness" and بر means "vast extension"...
does subtracting ح-semantics and adding ر-semantics in embedding space land
near the right meaning?

**Experiment:** Define operations like:
`embed(binary_root_XY_meaning) - embed(letter_Y_meaning) + embed(letter_Z_meaning)`
→ does this approximate `embed(binary_root_XZ_meaning)`?

Test across all letter substitution pairs. Measure cosine similarity of predicted
vs actual.

**What it proves:** Whether letter semantics are compositional in embedding space.

---

### B3. Unsupervised Root Discovery
**Concept:** Can an AI rediscover the binary root structure from scratch? Feed
a model only the tri-root → meaning mappings (without binary root labels) and
see if it independently clusters them into groups that match the Muajam's
binary root assignments.

**Experiment:** 
1. Embed all 1,938 axial meanings
2. Cluster with k-means or HDBSCAN
3. Measure cluster purity against known binary root groups
4. Compare: does the AI's clustering agree with the Muajam's expert classification?

**What it proves:** Whether the binary root structure is an objective semantic
reality discoverable by machines, not just a human-imposed framework.

---

### B4. Cross-Lingual Binary Root Transfer (Semitic Family)
**Concept:** If binary roots encode deep Semitic meanings, similar patterns
should exist in Hebrew and Aramaic. Take the Arabic binary root meanings and
test whether cognate Hebrew/Aramaic roots show similar semantic fields.

**Experiment:** Build a small cognate table (Arabic ↔ Hebrew for ~100 well-known
pairs). Embed both languages' root meanings. Measure whether cognate pairs cluster
closer than non-cognate pairs in shared embedding space.

**What it proves:** Whether the binary root is a *proto-Semitic* structure, not
just Arabic.

---

### B5. Generative Adversarial Validation (Fake Root Detection)
**Concept:** Generate "fake" binary root → tri-root → meaning combinations that
follow the phonosemantic rules but are not real Arabic. Mix them with real entries.
Can a classifier tell real from fake? If not, the rules capture the pattern well.
If so, what's the distinguishing signal?

**Experiment:**
1. Use the letter meaning rules to generate plausible fake roots
2. Train a binary classifier (real vs synthetic)
3. Analyze which features the classifier uses to distinguish
4. Use misclassified fakes as candidates for "missing" roots

---

### B6. Temporal Semantic Drift Tracking
**Concept:** Arabic roots have evolved across centuries. Use diachronic corpora
(pre-Islamic poetry → Quran → Classical → Modern Standard Arabic) to track how
far each root's usage has drifted from its binary root nucleus meaning.

**Experiment:** For each era, gather contextual embeddings of root usages.
Measure cosine distance from the Muajam's axial meaning. Plot drift over time.

**What it proves:** Which roots have been semantically stable for 1500+ years,
and which have diverged — a linguistic "mutation rate."

---

### B7. Phonoarticulatory Feature Encoding
**Concept:** The letter meanings in the Muajam correlate with articulatory
phonetics (place/manner of articulation). Encode each Arabic letter as a
phonetic feature vector (e.g., [+velar, +fricative, +voiced]) and test whether
phonetic similarity predicts semantic similarity in letter meanings.

**Experiment:** Build a 28×N feature matrix (letters × phonetic features).
Compute cosine similarity between letter pairs in phonetic space and in semantic
space (from Muajam meanings). Correlate. Test whether "similar-sounding letters
have similar meanings" — the strongest form of sound symbolism.

---

### B8. GraphRAG for Root Exploration
**Concept:** Build a graph-based retrieval augmented generation system. Users
ask a question about an Arabic word, and the system traverses the genome graph
(word → root → binary root → sibling roots → related words) to provide a rich,
interconnected answer.

**Experiment:** Load the genome graph into a vector + graph store (e.g., Neo4j +
embeddings). Build a RAG pipeline that, given a query word, retrieves its
full lineage and semantically adjacent families. Use an LLM to synthesize a
narrative explanation.

---

### B9. Attention Pattern Analysis (Transformer Probing)
**Concept:** Do Arabic language models (AraBERT, CAMeLBERT) internally "know"
about binary root structure? Probe their attention patterns and hidden states
to see if words sharing a binary root activate similar neural pathways.

**Experiment:** Feed word pairs from the same binary root family into AraBERT.
Extract attention patterns and intermediate layer representations. Compare
within-family similarity vs across-family similarity. If transformers have
learned binary root structure implicitly, it validates the theory from a
completely independent angle.

---

## C. DATA ENRICHMENT

### C1. Complete Muajam Digitization Gap Closure
Currently 1,938 roots are digitized. The full Muajam likely has more. Priority:
close the 989-root coverage gap identified by the diagnosis script.

### C2. Modern Standard Arabic Extension
The genome currently focuses on Classical/Quranic Arabic. Extend to MSA by
adding modern roots and measuring how many still fit the binary root framework
vs. being true innovations or borrowings.

### C3. Dialectal Arabic Layer
Add a dialect dimension — do Egyptian, Levantine, Gulf, and Maghrebi Arabic
dialects preserve, alter, or create new binary root patterns?

---

## D. SCORING & RANKING PRIORITIES

| ID  | Idea                              | Impact | Feasibility | Priority |
|-----|-----------------------------------|--------|-------------|----------|
| A2  | Third-letter modulation analysis  | ★★★★★  | ★★★★☆       | 🔴 TOP  |
| A1  | Low-score investigation           | ★★★★☆  | ★★★★★       | 🔴 TOP  |
| B3  | Unsupervised root discovery       | ★★★★★  | ★★★★☆       | 🔴 TOP  |
| A3  | Binary root semantic field map    | ★★★★☆  | ★★★★★       | 🔴 TOP  |
| B1  | LLM meaning predictor             | ★★★★★  | ★★★☆☆       | 🟡 HIGH |
| B2  | Embedding arithmetic              | ★★★★★  | ★★★☆☆       | 🟡 HIGH |
| A5  | Metathesis study                  | ★★★★☆  | ★★★★☆       | 🟡 HIGH |
| B7  | Phonoarticulatory encoding        | ★★★★☆  | ★★★★☆       | 🟡 HIGH |
| B8  | GraphRAG explorer                 | ★★★☆☆  | ★★★☆☆       | 🟢 MED  |
| A4  | Quran frequency correlation       | ★★★☆☆  | ★★★★★       | 🟢 MED  |
| B5  | Fake root detection               | ★★★★☆  | ★★☆☆☆       | 🟢 MED  |
| B6  | Temporal drift tracking           | ★★★★★  | ★★☆☆☆       | 🟢 MED  |
| B9  | Transformer probing               | ★★★★☆  | ★★☆☆☆       | 🟢 MED  |
| B4  | Cross-lingual transfer            | ★★★★★  | ★★☆☆☆       | 🔵 LONG |

---

*Generated 2026-03-13 for Juthoor-ArabicGenome-LV1*
