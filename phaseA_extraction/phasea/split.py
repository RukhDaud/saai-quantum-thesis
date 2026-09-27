"""Data splits.

1. random_split: stratified 60/20/20 on has_odd_condition (seeded).
2. held_out_source: train on all sources except one, test on that source
   (e.g. train on EU 2022/1426, test on UN R157). This is the test of
   generalisation to an unseen regulation and is the stronger claim.
"""
import pandas as pd
from sklearn.model_selection import train_test_split

SEED = 20260927


def source_family(s):
    s = str(s)
    if "2022/1426" in s:
        return "EU2022_1426"
    if "157" in s:
        return "UNR157"
    return s.split(",")[0]


def random_split(df, seed=SEED):
    y = df["has_odd_condition"].fillna("")
    train, rest = train_test_split(df, test_size=0.4, random_state=seed, stratify=y)
    dev, test = train_test_split(rest, test_size=0.5, random_state=seed,
                                 stratify=rest["has_odd_condition"].fillna(""))
    return train, dev, test


def held_out_source(df, test_family):
    fam = df["source"].map(source_family)
    return df[fam != test_family], df[fam == test_family]
