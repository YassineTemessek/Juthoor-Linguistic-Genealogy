# Reverse Pair Analysis: Anbar's Reversal Hypothesis

**Dataset:** 166 reversible binary nucleus pairs from Jabal's 456 Arabic nuclei
**Date:** 2026-03-26
**Status:** Empirical analysis — hypothesis tested and refined

---

## 1. Introduction

One of the oldest hypotheses in Arabic morphology is that the consonant order of a root carries systematic semantic information — specifically, that reversing a binary nucleus inverts its meaning. Anbar (1997) proposed this in explicit form: if a nucleus XY carries a core meaning M, then nucleus YX carries meaning ¬M, its semantic opposite.

Examples that appear to confirm the hypothesis are striking. بث "النشر والتفريق" (spreading and scattering) reverses to ثب "التجمع والتماسك" (gathering and cohesion): the motion goes from outward dispersal to inward consolidation. حل "التسيب والتفكك" (dissolution and loosening) reverses to لح "الالتحام" (fusion and joining): the state shifts from coming apart to coming together. These are clean semantic inversions, and their elegance is what made the hypothesis compelling.

This analysis tests Anbar's reversal hypothesis systematically against all 166 reversible pairs in our dataset. Each pair contains Jabal al-Muhtashim's meaning descriptions for both orientations (XY and YX), along with the semantic features extracted from those descriptions. We apply Jaccard similarity and feature polarity detection to classify each pair, then examine what the full distribution actually shows.

The result is not that the hypothesis is simply wrong. It is that the hypothesis is too simple — a first approximation that captures a real phenomenon but misses the full range of what reversal does.

---

## 2. Method

For each of the 166 pairs (XY ↔ YX), we compared Jabal's semantic feature sets for the forward and reverse nucleus:

1. **Extract features.** Both XY and YX receive semantic feature sets from Jabal's meaning descriptions via `decompose_semantic_text()`. Features are Arabic semantic primitives such as: تجمع (gathering), تفرق (dispersal), باطن (interior/inner), ظاهر (exterior/surface), امتداد (extension), نفاذ (penetration), غلظ (thickness), رخاوة (softness), etc.

2. **Classify each pair** into one of four categories:

   - **Empty (8 pairs):** One or both nuclei lack extractable features — typically because Jabal's description is too sparse, abstract, or refers to grammatical/numerical meaning (e.g., تس "nine"). These are excluded from percentage calculations.

   - **Similar (14 pairs, 9%):** Forward and reverse feature sets overlap at Jaccard ≥ 0.3 — i.e., reversal preserves rather than inverts the semantic domain.

   - **Inversion (19 pairs, 12%):** No similarity by Jaccard, but the feature sets contain opposite features according to `FEATURE_POLARITIES` — the system of semantic oppositions defined in `feature_decomposition.py` (e.g., تجمع ↔ تفرق, باطن ↔ ظاهر, امتداد ↔ انحسار, غلظ ↔ رقة).

   - **Unrelated (125 pairs, 79%):** Neither similar nor inverting — the two nuclei occupy different semantic territory with no detectable systematic relationship in feature space.

The polarity system `FEATURE_POLARITIES` covers 30 opposition pairs. `SEMANTIC_OPPOSITES` in `scoring.py` extends this with additional pairs. Both were used in classification.

---

## 3. Results

### 3.1 Summary Table

| Category | Count | % of non-empty |
|----------|-------|---------------|
| Empty (excluded) | 8 | — |
| Similar (J ≥ 0.3) | 14 | 8.9% |
| Inversion (opposite features) | 19 | 12.0% |
| Unrelated | 125 | 79.1% |
| **Total non-empty** | **158** | **100%** |

### 3.2 Primary Finding

**Anbar's reversal hypothesis, understood as simple inversion, is not confirmed.**

Only 12% of reversible pairs show the predicted inversion pattern. A further 9% show the opposite of inversion — reversal actually *preserves* the semantic domain. The dominant outcome, at 79%, is that reversal moves the meaning into a different, unrelated semantic field.

This does not mean reversal is random. The 12% inversion rate is not negligible — in a truly random system, we would expect the polarity overlap rate to be much lower, given the limited size of the polarity vocabulary relative to the full feature space. The inversions that exist are genuine and linguistically significant. But they are the exception, not the rule.

---

## 4. Examples by Category

### 4.1 True Inversion (12% of pairs)

These are the cases that motivated the hypothesis. The meaning of YX is the semantic complement of XY — the action runs in the opposite direction.

**بث ↔ ثب**
- بث: النشر والتفريق — features: انتشار، تفرق (spreading, dispersal)
- ثب: التجمع والتماسك — features: تجمع، تماسك (gathering, cohesion)
- The motion reverses: outward scatter becomes inward consolidation. This is the paradigm case.

**ءم ↔ مء**
- ءم: النقص والانفراد — features: نقص، استقلال (diminishment, isolation)
- مء: الاتساع والامتداد — features: اتساع، تلاصق، امتداد (expansion, extension)
- Diminishment/isolation inverts to expansion/extension. A clean semantic inversion across quantity and spatial dimensions.

**ثن ↔ نث**
- ثن: التبطن والكثرة في الداخل — features: كثافة (interior density)
- نث: الانتثار أو النشر بتفشٍّ واندفاع — features: انتشار، تفشي، اندفاع (scattering, diffusion, propulsion outward)
- Interior density becomes outward scattering. The direction of the action reverses: inward → outward.

**حل ↔ لح**
- حل: التسيب والتفكك — features: تخلخل، امتداد (loosening, dissolution with extension)
- لح: الالتحام وما يلزمه من عرض وامتداد — features: التحام، امتداد (fusion, joining)
- Dissolution/unfastening inverts to fusion/joining. The state of matter reverses: loose → fused.

**ضف ↔ فض**
- ضف: التجمع على الشيء أو حوله — features: تجمع (gathering around)
- فض: الكسر والتفريق بقوة وغلظ — features: كسر، تفرق، قوة، غلظ (breaking, dispersal, force)
- Gathering around becomes violent dispersal. Convergence inverts to disintegration.

**Additional confirmed inversions:** بر ↔ رب (خلوص/فراغ vs غلظ/تماسك), جل ↔ لج (اتساع/ظهور vs تماسك/كثافة/قوة), حض ↔ ضح (انحدار/نقص/غلظ vs انبساط/ظهور), حط ↔ طح (انضغاط إلى أسفل vs انبساط عن ضغط), صع ↔ عص (تسيب/تفرق vs صلابة/اشتداد), ذك ↔ كذ (حدة/صلابة/غلظ vs رخاوة).

### 4.2 Similar Meanings (9% of pairs) — Reversal Preserves

These cases falsify the hypothesis in the opposite direction: the reversed nucleus does not invert but stays within the same semantic domain, or overlaps substantially.

**تح ↔ حت**
- تح: الاحتكاك من أسفل — features: احتكاك، باطن (friction, from below)
- حت: تفتت الرقيق الجاف حكًا أو تسيبه — features: رقة، جفاف، احتكاك، تخلخل (friction, dry, loosening)
- Both involve احتكاك (friction). The action is similar; what changes is the emphasis — from the pressure vector to the resultant crumbling.

**ثج ↔ جث**
- ثج: غزارة المائع وتجمعه — features: غزارة، تجمع (abundance of fluid, gathering)
- جث: تجمع الكتلة الكثيفة — features: تجمع، كثافة (gathering, density)
- Both involve تجمع (gathering). One emphasizes fluidity and abundance; the other emphasizes solid mass. The domain is the same: accumulation.

**رش ↔ شر**
- رش: انتشار الأشياء الدقيقة الطرية — features: انتشار، دقة (spread of fine, tender things)
- شر: الانتشار أو صورة منه — features: انتشار (spreading)
- Both share انتشار (spreading). This is near-identity of meaning — reversal changes nothing essential.

**جح ↔ حج**
- جح: الغلظ والحدة في الباطن — features: غلظ، حدة، باطن (thickness, sharpness, interior)
- حج: الحيلولة بصلب أو شديد — features: صلابة، غلظ، قوة (hardness, thickness, force)
- Both feature غلظ. The semantic field — hard, thick, resistant — is shared across the reversal.

**حش ↔ شح**
- حش: الجفاف والخشونة مع الانتشار — features: جفاف، انتشار (dryness, spread)
- شح: جفاف الجرم أو حدته مع عرض أو تجسم — features: جفاف (dryness)
- Shared feature: جفاف. Both describe dryness of substance; the reversal adds or subtracts secondary qualities but does not invert the core meaning.

### 4.3 Unrelated Meanings (79% of pairs) — The Dominant Pattern

The majority of reversals do not invert and do not preserve — they produce a semantically distinct meaning in a different area. These represent cases where the reversal hypothesis simply does not hold.

**ءب ↔ بء**
- ءب: الغَذْو والتهيؤ والامتناع — features: تلاصق، احتباس (nourishment, preparation, restraint)
- بء: الاستقرار والرجوع — features: استقرار، رجوع (stability, return)
- Restraint/nourishment vs. stability/return. Different semantic domains, no obvious polarity.

**بج ↔ جب**
- بج: التفتق والتفجر الرخو — features: خروج، رخاوة (soft bursting open)
- جب: التجسم والبروز مع القطع أو الاستواء — features: بروز، قطع، استواء (protrusion, cutting, flatness)
- Soft rupture vs. solid protrusion with cutting. Related to surface emergence but the mechanisms and textures are entirely different.

**بد ↔ دب**
- بد: الظهور والتكوين الأول — features: ظهور (appearance, first formation)
- دب: الثقل أو الضغط والحركة البطيئة — features: ثقل، ضغط، انتقال (heaviness, slow movement)
- First emergence vs. heavy, slow movement. Nothing systematic connects these meanings.

**بغ ↔ غب**
- بغ: التزايد والفوران الداخلي — features: امتداد، خروج، فوران (internal surging outward)
- غب: الغئور والغياب أو الاستتار — features: عمق، باطن (sinking inward, disappearance)
- This looks like an inversion (outward vs. inward), but the feature polarity does not trigger: فوران has no defined opposite in FEATURE_POLARITIES, and عمق/باطن are not the formal opposites of امتداد/خروج in the system. It illustrates the limits of mechanical polarity detection — semantically suggestive but not confirmed by the classifier.

**در ↔ رد**
- در: الجريان باسترسال، أو الامتداد بتوال — features: استرسال، باطن، تلاصق، امتداد (flowing continuously)
- رد: التراكم المترتب على صدّ الشيء المسترسل — features: تماسك، إمساك، باطن (accumulation from blocking that which flows)
- This is perhaps the most interesting "unrelated" case. Jabal himself notes that رد is what happens when flow (در) is stopped — the meaning is causally connected, not polar. Reversal here encodes the *consequence* of blocking, not the *opposite* of flowing. This is a different kind of semantic relationship entirely.

---

## 5. A More Nuanced Pattern: What Reversal Actually Does

When we read across all 166 pairs rather than looking only at the 12% that invert cleanly, a more complex picture emerges. Several distinct patterns appear in the majority:

### 5.1 Direction Change Without Full Inversion

In several pairs, reversal changes the *direction* of an action without inverting the action itself. The same physical mechanism operates, but the vector flips.

- حن ↔ نح: The hollow interior of something strong (جوف الشيء القوي) vs. penetration outward from the interior with force (النفاذ من الباطن بقوة). Interior-containment becomes outward-escape from the same interior. The cavity is common; what changes is the orientation of force: inward holding vs. outward breaking.

- طم ↔ مط: Full covering and occlusion (الملء والتغطية حتى الإخفاء) vs. extension and flowing out (الامتداد والانسكاب). Containment inward vs. spilling outward from containment.

- دن ↔ ند: Something embedded in the interior (اندساس الشيء في أثناء أو ثباته فيه) vs. movement away and separation (الإبعاد امتدادًا أو مفارقة). Insertion into vs. withdrawal from.

These are not clean inversions because the feature sets do not contain formal polarity pairs. But the underlying spatial logic is that of reversal: what enters now exits; what covers now extends.

### 5.2 Texture or Quality Change Within the Same Process

Some pairs share a process domain but reverse the texture or quality of that process.

- در ↔ رد: Flowing → blocking of flow (accumulation). Same process domain; reversal encodes the obstructed state.
- خر ↔ رخ: Internal looseness and hollowing (تخلخل الأثناء) vs. the softness of a formed body that has been moistened (طراءة الشيء المتجسم). Both are states of reduced internal density, but one is structural failure (خر) and the other is pliability (رخ).
- رم ↔ مر: Gathering what is soft or changeable into the interior (ضمّ غَضّ) vs. continuous flowing movement with qualities (الاسترسال والحركة مع صفة). Both involve interior motion; reversal changes whether the motion is centripetal or centrifugal.

### 5.3 Domain Shift: Physical → Abstract or Cross-Domain

A subset of pairs show the two nuclei operating in different registers — one physical, one social or perceptual — with no systematic semantic link.

- بت ↔ تب: Cutting and separation (القطع والانفصال) vs. weakening of what was gathered (ضعف الشيء المتجمع). Different targets, different agents.
- سك ↔ كس: A passage so narrow it nearly closes (ضيق المنفذ ضيقًا شديدًا) vs. diminishment by grinding or peeling (النقص بالدق أو القشر). Both involve reduction but through entirely different mechanisms.
- حو ↔ وح: Full possession with vital force (الامتلاء والحيازة بقوة وحياة) vs. delicate but strong acquisition (التحصيل اللطيف والقوي). These share قوة but otherwise describe different modalities of possession.

### 5.4 The Reversal as Modification, Not Opposition

Perhaps the most accurate general description of what reversal does is this: it takes the semantic field of XY and applies a transformation that changes *one parameter* — direction, intensity, mode, or texture — while leaving the general domain partially intact. This is not inversion. It is modification.

This is consistent with the 9% similarity rate and the 12% inversion rate. The remaining 79% are cases where the modification is large enough that the result lands in a different part of semantic space — far enough that no single parameter change explains it, but not so far as to be random.

---

## 6. Findings

### 6.1 The Hypothesis Fails as Stated

Anbar's reversal hypothesis, as a claim that reversing a binary nucleus *inverts* its meaning, is falsified by the data:

- Only **12% (19/158)** of non-empty pairs show feature inversion.
- **9% (14/158)** show the opposite: reversal *preserves* semantic similarity.
- **79% (125/158)** are unrelated by the polarity metric.

The claim cannot be generalized. Arabic morphology does not encode a simple XY/YX inversion structure.

### 6.2 The Hypothesis Captures a Real Subset

The 19 true inversion cases are not noise. They include some of the most semantically clear pairs in Jabal's system: بث/ثب, حل/لح, ضف/فض, ءم/مء, ثن/نث. These pairs show that the reversal mechanism *can* produce semantic inversion, and when it does, the inversions are clean and linguistically meaningful.

The hypothesis succeeds where both nuclei encode a *directional* or *vector* meaning — a process that has an inside and an outside, a gathering and a scattering, a holding and a releasing. When the primary semantic content is directional, reversal inverts the direction.

### 6.3 The Dominant Pattern Is Unpredictable Modification

For most pairs, reversal does something more subtle and less predictable than inversion. It may:
- Shift the direction of an action while preserving the action type
- Preserve the process domain while changing the quality or texture
- Move into a related but distinct semantic field
- Move into an apparently unrelated semantic field

This suggests that the relationship between XY and YX, when it exists, is more like *semantic kinship* than *semantic opposition*. The consonants share a family resemblance — they operate in related phonosemantic territory — but the specific meaning of each combination is shaped by the individual consonants' contributions, not by a simple reversal rule.

### 6.4 Feature Polarity as an Insufficient Model

The `FEATURE_POLARITIES` system used in this analysis defines 30 semantic opposition pairs. This is a significant coverage, but the Arabic feature vocabulary contains many dimensions — direction (باطن/ظاهر), intensity (قوة/رخاوة), texture (غلظ/رقة), structure (تجمع/تفرق), dynamics (نفاذ/احتباس) — that interact in non-linear ways. A pair like بغ ↔ غب (internal surging vs. sinking inward) is semantically suggestive of inversion but does not trigger the classifier because the specific features involved lack defined polarity mappings.

This means the 12% inversion rate is likely an *undercount*. Some genuine inversions are probably in the "unrelated" bin because their inversions operate along semantic axes not covered by the polarity list. The true inversion rate may be higher — but it is unlikely to reach the majority.

---

## 7. Implications

### 7.1 For LV1 Research

The reversal hypothesis should be retired as a strong morphological claim and repositioned as a weak tendency with a specific scope condition: it applies to directional process-meanings, not to meanings in general. The promoted evidence for this study should note that the 19 inversion cases are real and worth preserving, but the 125 unrelated cases are equally real and must not be erased.

Future work could attempt to predict *which* nuclei will show inversion (those with directional or vector-like meanings) vs. which will show domain shift. This might be trainable if the semantic feature sets are rich enough.

### 7.2 For the Broader Morphological Theory

The finding aligns with a view of Arabic consonant ordering that is more probabilistic than rule-governed. Each consonant pair XY carves out a region of semantic space based on the individual letter meanings (as established in Phase 2 of the Genome, via Muajam Ishtiqaqi). The pairing XY and YX will tend to be in related semantic regions — which explains why 21% of pairs show some detectable relationship — but the specific positions within that region are not mirror images of each other.

This is consistent with research in morphological semantics more broadly: phonosemantic correspondences are statistical, not logical. Arabic is notable for the *degree* of its systematicity, not for having a simple one-to-one inversion structure.

### 7.3 For LV2 and Cognate Discovery

For the cognate discovery engine, this finding implies that reversal cannot be used as a simple feature to detect related roots across languages. It *could* be used as a weak positive signal — if an Arabic root XY has a cognate in another language, a root YX in that language is more likely to be cognate with the Arabic reversal than a random root would be — but the signal would be noisy.

The 19 confirmed inversion pairs are more immediately useful: they represent cases where two Arabic roots are semantically opposed, and cross-lingual cognates of both roots could potentially be identified and their semantic relationship in the target language tested.

### 7.4 For Understanding Jabal's System

One underappreciated implication is what this analysis reveals about Jabal's nuclei themselves. The 14 similarity cases — where XY and YX mean nearly the same thing — suggest that Jabal's system is not simply listing all possible permutations as distinct semantic units. The instances where two orderings share a domain may reflect cases where the consonant order is genuinely free, or where Jabal recognized a strong family resemblance but recorded them separately for completeness.

The 8 empty pairs (e.g., لو ↔ ول, both empty) further suggest that not all consonant pairings yield productive nuclei in Jabal's Arabic. The 456-nucleus system has genuine gaps, and the reversal structure is one lens through which those gaps become visible.

---

## 8. Data Notes

- Total pairs in dataset: 166
- Pairs excluded (empty features on one or both sides): 8
  - ءل ↔ لء, تف ↔ فت (forward empty), تس ↔ ست (forward empty), ظع ↔ عظ (forward empty), ظن ↔ نظ (forward empty), ضق ↔ قض (forward empty), لن ↔ نل (forward empty), لو ↔ ول (both empty)
- Non-empty pairs analyzed: 158
- Classification thresholds: Jaccard ≥ 0.3 for "similar"; any overlap between inverted-features and reverse-features for "inversion"
- Feature polarity source: `FEATURE_POLARITIES` in `core/feature_decomposition.py`, extended by `SEMANTIC_OPPOSITES` in `factory/scoring.py`

---

*Generated from `outputs/lv1_scoring/reverse_pair_data.json` (166 pairs, covering letters ء through و). Analysis uses semantic features extracted by `decompose_semantic_text()` from Jabal al-Muhtashim's meaning descriptions for each binary nucleus.*
