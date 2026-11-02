
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import tldextract

from scipy.stats import randint, uniform
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV, StratifiedGroupKFold

from xgboost import XGBClassifier

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "ml/datasets/processed"
MODEL_DIR = ROOT_DIR / "ml/saved_models/tuned_candidates"
REPORT_DIR = ROOT_DIR / "ml/evaluation/results/url_tuning"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

extract_domain = tldextract.TLDExtract(
    suffix_list_urls=(),
    include_psl_private_domains=True
)


def get_domain(url):
    extracted = extract_domain(str(url))
    domain = extracted.top_domain_under_public_suffix

    if domain:
        return domain.lower()

    return str(url).lower()


def main():
    train_df = pd.read_csv(DATA_DIR / "url_train.csv")

    with open(DATA_DIR / "url_feature_columns.json") as file:
        feature_columns = json.load(file)

    X_train = train_df[feature_columns]
    y_train = train_df["label"]
    groups = train_df["url"].apply(get_domain)

    if X_train.isnull().any().any():
        raise ValueError("Missing training features detected")

    if not np.isfinite(X_train.to_numpy()).all():
        raise ValueError("Non-finite training features detected")

    if groups.nunique() < 5:
        raise ValueError("Not enough domain groups for 5-fold validation")

    cv = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    models = {
        "random_forest": (
            RandomForestClassifier(
                random_state=42,
                n_jobs=1
            ),
            {
                "n_estimators": randint(300, 901),
                "max_depth": [None, 10, 20, 30, 40],
                "min_samples_split": randint(2, 11),
                "min_samples_leaf": randint(1, 6),
                "max_features": ["sqrt", "log2", 0.5, 0.8],
                "class_weight": ["balanced", "balanced_subsample"]
            }
        ),
        "xgboost": (
            XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=42,
                n_jobs=1,
                verbosity=0
            ),
            {
                "n_estimators": randint(250, 801),
                "max_depth": randint(3, 9),
                "learning_rate": uniform(0.02, 0.13),
                "subsample": uniform(0.7, 0.3),
                "colsample_bytree": uniform(0.7, 0.3),
                "min_child_weight": randint(1, 8),
                "reg_lambda": uniform(0.5, 4.5),
                "gamma": uniform(0, 2)
            }
        )
    }

    scoring = {
        "f1": "f1",
        "precision": "precision",
        "recall": "recall",
        "roc_auc": "roc_auc"
    }

    summary = {}

    print("\n========== URL MODEL OPTIMIZATION ==========")
    print("Training records:", len(train_df))
    print("Features:", len(feature_columns))
    print("Unique domain groups:", groups.nunique())
    print("Cross-validation: 5-fold StratifiedGroupKFold")
    print("Random search iterations per model: 15")

    for name, (model, parameters) in models.items():
        print(f"\n========== OPTIMIZING {name.upper()} ==========")

        search = RandomizedSearchCV(
            estimator=model,
            param_distributions=parameters,
            n_iter=15,
            scoring=scoring,
            refit="f1",
            cv=cv,
            random_state=42,
            n_jobs=-1,
            verbose=2,
            return_train_score=True,
            error_score="raise"
        )

        search.fit(X_train, y_train, groups=groups)

        best_index = search.best_index_
        results = search.cv_results_

        metrics = {
            metric: float(results[f"mean_test_{metric}"][best_index])
            for metric in scoring
        }

        summary[name] = {
            "best_cv_metrics": metrics,
            "best_parameters": search.best_params_,
            "best_f1": float(search.best_score_)
        }

        model_path = MODEL_DIR / f"{name}_tuned_candidate.joblib"
        joblib.dump(search.best_estimator_, model_path)

        cv_results = pd.DataFrame(results)
        cv_results.to_csv(
            REPORT_DIR / f"{name}_cv_results.csv",
            index=False
        )

        print("\nBest parameters:")
        print(search.best_params_)

        print("\nBest cross-validation metrics:")
        for metric, value in metrics.items():
            print(f"{metric}: {value:.4f}")

        print("\nSaved candidate:", model_path)

    with open(REPORT_DIR / "url_tuning_summary.json", "w") as file:
        json.dump(summary, file, indent=4)

    print("\n========== OPTIMIZATION SUMMARY ==========")
    print(pd.DataFrame({
        name: data["best_cv_metrics"]
        for name, data in summary.items()
    }).T.to_string())

    print("\nTuned candidates saved separately.")
    print("Original models and held-out test set were not modified.")


if __name__ == "__main__":
    main()
