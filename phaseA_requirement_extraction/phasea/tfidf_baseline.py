"""Baseline 2: TF-IDF + logistic regression for the categorical fields.

Trains one classifier per categorical field on gold-labelled rows. Threshold
and unit still come from the regex in rule_baseline (a bag-of-words model
cannot copy a number out of the text). Needs gold labels to run.

Usage:
    python -m phasea.tfidf_baseline gold.csv --split random --out results/tfidf_predictions.csv
    python -m phasea.tfidf_baseline gold.csv --split source --test-source UNR157
"""
import argparse

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from .evaluate import evaluate, load
from .rule_baseline import predict_one
from .schema import CATEGORICAL, norm
from .split import SEED, held_out_source, random_split


def fit_predict(train, test):
    out = pd.DataFrame({"req_id": test["req_id"].values})
    for f in CATEGORICAL:
        y = train[f].map(norm)
        if y.nunique() < 2:  # a single class in training: predict it
            out[f] = y.iloc[0]
            continue
        clf = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True),
                            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED))
        clf.fit(train["text"], y)
        out[f] = clf.predict(test["text"])
    rule = pd.DataFrame([predict_one(t) for t in test["text"]])
    for f in ["variable", "threshold", "unit", "response"]:
        out[f] = rule[f].values
    yes = out["has_odd_condition"] == "yes"
    for f in ["threshold", "unit", "response"]:
        out.loc[~yes, f] = ""
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gold")
    ap.add_argument("--split", choices=["random", "source"], default="random")
    ap.add_argument("--test-source", default="UNR157")
    ap.add_argument("--out", default="results/tfidf_predictions.csv")
    a = ap.parse_args()
    gold = load(a.gold)
    gold = gold[gold["has_odd_condition"].map(norm) != ""]
    if a.split == "random":
        train, dev, test = random_split(gold)
        train = pd.concat([train, dev])  # no hyper-parameter search in this baseline
    else:
        train, test = held_out_source(gold, a.test_source)
    pred = fit_predict(train, test)
    pred.to_csv(a.out, index=False)
    summ, _, _ = evaluate(test, pred)
    print(f"train={len(train)} test={len(test)}")
    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
