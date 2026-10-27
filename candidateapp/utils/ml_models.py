"""
Real scikit-learn models for Salary Prediction and Placement Probability.

Trained on a synthetic-but-realistic dataset generated deterministically (fixed seed)
so the project is fully runnable out of the box with no external dataset required.
Run `python manage.py train_ml_models` to (re)train and cache the models to
candidateapp/ml_artifacts/*.joblib. If artifacts are missing, they are trained
automatically on first use.
"""
import os

import joblib
import numpy as np
from django.conf import settings
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

ARTIFACT_DIR = os.path.join(settings.BASE_DIR, "candidateapp", "ml_artifacts")
SALARY_MODEL_PATH = os.path.join(ARTIFACT_DIR, "salary_model.joblib")
PLACEMENT_MODEL_PATH = os.path.join(ARTIFACT_DIR, "placement_model.joblib")

ROLE_BASE_SALARY = {
    "data_analyst": 5.5, "data_scientist": 8.0, "machine_learning_engineer": 9.0,
    "web_developer": 4.5, "python_developer": 5.0, "business_analyst": 5.0,
    "bi_developer": 5.5, "software_engineer": 5.0, "devops_engineer": 6.5,
    "data_engineer": 7.0,
}


def _generate_salary_dataset(n=2000, seed=42):
    rng = np.random.default_rng(seed)
    roles = list(ROLE_BASE_SALARY.keys())
    role_idx = rng.integers(0, len(roles), n)
    experience = rng.uniform(0, 8, n)
    skills_count = rng.integers(1, 15, n)
    cgpa = rng.uniform(5.5, 9.9, n)

    base = np.array([ROLE_BASE_SALARY[roles[i]] for i in role_idx])
    salary = (
        base
        + experience * 1.4
        + skills_count * 0.18
        + (cgpa - 7) * 0.3
        + rng.normal(0, 0.4, n)
    )
    salary = np.clip(salary, 2.5, 45)

    X = np.column_stack([role_idx, experience, skills_count, cgpa])
    return X, salary, roles


def _generate_placement_dataset(n=3000, seed=7):
    rng = np.random.default_rng(seed)
    cgpa = rng.uniform(5.0, 10.0, n)
    skills_count = rng.integers(0, 16, n)
    projects_count = rng.integers(0, 8, n)
    aptitude_score = rng.uniform(20, 100, n)

    score = (
        (cgpa - 5) / 5 * 0.3
        + (skills_count / 15) * 0.3
        + (projects_count / 7) * 0.2
        + (aptitude_score / 100) * 0.2
    )
    prob = 1 / (1 + np.exp(-8 * (score - 0.5)))
    placed = (rng.uniform(0, 1, n) < prob).astype(int)

    X = np.column_stack([cgpa, skills_count, projects_count, aptitude_score])
    return X, placed


def train_and_save_models():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    X_sal, y_sal, roles = _generate_salary_dataset()
    salary_model = RandomForestRegressor(n_estimators=150, max_depth=8, random_state=42)
    salary_model.fit(X_sal, y_sal)
    joblib.dump({"model": salary_model, "roles": roles}, SALARY_MODEL_PATH)

    X_pl, y_pl = _generate_placement_dataset()
    placement_model = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
    placement_model.fit(X_pl, y_pl)
    joblib.dump({"model": placement_model}, PLACEMENT_MODEL_PATH)

    return salary_model, placement_model


def _load_or_train_salary():
    if os.path.exists(SALARY_MODEL_PATH):
        return joblib.load(SALARY_MODEL_PATH)
    train_and_save_models()
    return joblib.load(SALARY_MODEL_PATH)


def _load_or_train_placement():
    if os.path.exists(PLACEMENT_MODEL_PATH):
        return joblib.load(PLACEMENT_MODEL_PATH)
    train_and_save_models()
    return joblib.load(PLACEMENT_MODEL_PATH)


def predict_salary(role: str, experience_years: float, skills_count: int, cgpa: float):
    bundle = _load_or_train_salary()
    model, roles = bundle["model"], bundle["roles"]
    role_key = role.lower().replace(" ", "_") if role else "software_engineer"
    role_idx = roles.index(role_key) if role_key in roles else roles.index("software_engineer")

    X = np.array([[role_idx, experience_years or 0, skills_count, cgpa or 7.0]])
    pred = float(model.predict(X)[0])

    # min-max range from the forest's individual tree spread
    tree_preds = np.array([t.predict(X)[0] for t in model.estimators_])
    salary_min = float(max(2.0, np.percentile(tree_preds, 10)))
    salary_max = float(np.percentile(tree_preds, 90))
    return round(pred, 2), round(salary_min, 2), round(salary_max, 2)


def predict_placement(cgpa: float, skills_count: int, projects_count: int, aptitude_score: float = 60.0):
    bundle = _load_or_train_placement()
    model = bundle["model"]
    X = np.array([[cgpa or 7.0, skills_count, projects_count, aptitude_score]])
    proba = float(model.predict_proba(X)[0][1]) * 100

    tips = []
    if (cgpa or 0) < 7:
        tips.append("Improving your CGPA above 7.0 can noticeably boost placement chances")
    if skills_count < 6:
        tips.append("Add more in-demand technical skills to your profile")
    if projects_count < 2:
        tips.append("Build at least 2-3 solid projects to showcase practical experience")
    if not tips:
        tips.append("Great profile! Keep practicing aptitude tests to stay sharp")

    return round(proba, 1), tips
