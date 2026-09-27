"""Model 3: SciBERT fine-tuning for the categorical fields (run on Colab/GPU).

One sequence classifier per categorical field (has_odd_condition,
odd_dimension, operator), model allenai/scibert_scivocab_uncased.
Threshold/unit/response come from the rule extractor, as in the TF-IDF
baseline, so the comparison isolates the classifier.

Seeds: 5 runs (SEEDS below); report mean and SD, not the best run.

Colab:
    !pip install -q transformers datasets accelerate scikit-learn pandas openpyxl
    !python -m phasea.train_scibert gold.csv --split random --out results/scibert_predictions.csv
"""
import argparse

import numpy as np
import pandas as pd

from .evaluate import evaluate, load
from .rule_baseline import predict_one
from .schema import CATEGORICAL, norm
from .split import held_out_source, random_split

MODEL = "allenai/scibert_scivocab_uncased"
SEEDS = [11, 22, 33, 44, 55]


def train_field(train, dev, test, field, seed, epochs=10, lr=2e-5, bs=16):
    import torch
    from datasets import Dataset
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                              Trainer, TrainingArguments, set_seed)
    set_seed(seed)
    labels = sorted(set(train[field].map(norm)) | set(dev[field].map(norm)))
    l2i = {l: i for i, l in enumerate(labels)}
    tok = AutoTokenizer.from_pretrained(MODEL)

    def ds(df):
        d = Dataset.from_dict({"text": df["text"].tolist(),
                               "label": [l2i.get(norm(v), 0) for v in df[field]]})
        return d.map(lambda b: tok(b["text"], truncation=True, max_length=256), batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=len(labels))
    args = TrainingArguments(output_dir=f"runs/{field}_{seed}", num_train_epochs=epochs,
                             learning_rate=lr, per_device_train_batch_size=bs,
                             eval_strategy="epoch", save_strategy="epoch",
                             load_best_model_at_end=True, metric_for_best_model="eval_loss",
                             save_total_limit=1, seed=seed, report_to=[],
                             fp16=torch.cuda.is_available())
    tr = Trainer(model=model, args=args, train_dataset=ds(train), eval_dataset=ds(dev),
                 processing_class=tok)
    tr.train()
    logits = tr.predict(ds(test)).predictions
    return [labels[i] for i in np.argmax(logits, axis=1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gold")
    ap.add_argument("--split", choices=["random", "source"], default="random")
    ap.add_argument("--test-source", default="UNR157")
    ap.add_argument("--out", default="results/scibert_predictions.csv")
    a = ap.parse_args()
    gold = load(a.gold)
    gold = gold[gold["has_odd_condition"].map(norm) != ""]
    if a.split == "random":
        train, dev, test = random_split(gold)
    else:
        rest, test = held_out_source(gold, a.test_source)
        train, dev, _ = random_split(rest)  # dev taken from training sources only
    all_runs = []
    for seed in SEEDS:
        out = pd.DataFrame({"req_id": test["req_id"].values})
        for f in CATEGORICAL:
            out[f] = train_field(train, dev, test, f, seed)
        rule = pd.DataFrame([predict_one(t) for t in test["text"]])
        for f in ["variable", "threshold", "unit", "response"]:
            out[f] = rule[f].values
        out.loc[out["has_odd_condition"] != "yes", ["threshold", "unit", "response"]] = ""
        out.to_csv(a.out.replace(".csv", f"_seed{seed}.csv"), index=False)
        s, _, _ = evaluate(test, out)
        s["seed"] = seed
        all_runs.append(s)
    res = pd.concat(all_runs)
    agg = res.groupby(["field", "metric"])["value"].agg(["mean", "std"]).reset_index()
    agg.to_csv(a.out.replace(".csv", "_summary.csv"), index=False)
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
