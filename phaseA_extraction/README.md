# Phase A — requirement → ODD boundary predicate extraction

Input: one regulatory statement (e.g. an EU 2022/1426 or UN R157 point).
Output: has_odd_condition, odd_dimension, variable, operator, threshold, unit, response
(label set in `phasea/schema.py`, identical to the annotation template).

## Components
| File | What it does | Needs gold labels? | Runs here? |
|---|---|---|---|
| `phasea/rule_baseline.py` | Keyword/regex extractor (Baseline 1) | No | Yes |
| `phasea/tfidf_baseline.py` | TF-IDF + logistic regression (Baseline 2) | Yes | Yes |
| `phasea/train_scibert.py` | SciBERT fine-tuning, 5 seeds, mean ± SD (Model 3) | Yes | Colab/GPU only |
| `phasea/evaluate.py` | Accuracy, macro-F1, exact match, whole-predicate match | Yes | Yes |
| `phasea/split.py` | Stratified 60/20/20 and held-out-source split | — | Yes |
| `tests/test_phasea.py` | Plumbing tests on toy data (5 pass) | No | Yes |

## Order of work
1. Two annotators label `EU1426_annotation_template.xlsx` independently.
2. `python ../phase2/tools/agreement.py A1.xlsx A2.xlsx` → Cohen's kappa; adjudicate → `gold.xlsx`.
3. `python -m phasea.rule_baseline gold.csv --out results/rule.csv` then `python -m phasea.evaluate gold.xlsx results/rule.csv`.
4. `python -m phasea.tfidf_baseline gold.xlsx --split random` and `--split source --test-source UNR157`.
5. On Colab: `python -m phasea.train_scibert gold.xlsx --split random` (and `--split source`).

## Rules that protect the results
- The rule lexicon was written before any gold label existed. It must stay frozen; changing it after
  looking at gold labels would leak test information. Known misses (e.g. "time of day", "road category")
  are kept as the baseline's honest errors.
- The rule extractor never invents a threshold: no number in the text → `unspecified`.
- SciBERT results are reported as mean ± SD over 5 seeds, never the best seed.
- The held-out-source split (train EU 2022/1426, test UN R157) is the main generalisation claim.
