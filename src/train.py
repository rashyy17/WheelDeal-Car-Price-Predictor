# src/train.py
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Paths
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw.csv"
MODEL_PATH = ROOT / "models" / "wheel_deal_pipeline.pkl"

# 1) Load
df = pd.read_csv(DATA_PATH)
print("Loaded dataset with rows:", len(df))
print(df.columns.tolist())

# 2) Basic cleaning / ensure numeric types
# If mileage/engine/max_power have stray strings, try to coerce
for col in ["mileage", "engine", "max_power", "km_driven", "vehicle_age", "seats"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop rows without price
df = df[~df['selling_price'].isna()]

# 3) Define features and target
NUM_COLS = [c for c in ["vehicle_age", "km_driven", "mileage", "engine", "max_power", "seats"] if c in df.columns]
CAT_COLS = [c for c in ["brand", "model", "fuel_type", "transmission_type", "seller_type"] if c in df.columns]

X = df[NUM_COLS + CAT_COLS].copy()
y = df["selling_price"].astype(float).copy()

# 4) Optional: remove extreme outliers in price (helps robustness)
q_low = y.quantile(0.005)
q_high = y.quantile(0.995)
keep_mask = (y >= q_low) & (y <= q_high)
X = X[keep_mask]
y = y[keep_mask]
print(f"After trimming extreme price outliers: {len(y)} rows remain")

# 5) Target transform: log1p to avoid negative predictions and reduce skew
y_trans = np.log1p(y)

# 6) Preprocessing pipeline
num_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

cat_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
    ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
])


preprocessor = ColumnTransformer([
    ("num", num_pipeline, NUM_COLS),
    ("cat", cat_pipeline, CAT_COLS)
], remainder="drop", sparse_threshold=0)

# 7) Model and full pipeline (predicts log price)
rf = RandomForestRegressor(n_jobs=-1, random_state=42)

pipe = Pipeline([
    ("preproc", preprocessor),
    ("model", rf)
])

# 8) Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y_trans, test_size=0.2, random_state=42)

# 9) Hyperparameter tuning (randomized search — small budget but helpful)
param_dist = {
    "model__n_estimators": [100, 200, 400],
    "model__max_depth": [None, 8, 12, 20],
    "model__min_samples_split": [2, 4, 8],
    "model__min_samples_leaf": [1, 2, 4],
    "model__max_features": ["sqrt", 0.5, 0.8]
}

search = RandomizedSearchCV(pipe, param_distributions=param_dist, n_iter=12, cv=3,
                            scoring="neg_mean_absolute_error", verbose=1, random_state=42)

print("Starting hyperparameter search (this may take a while)...")
search.fit(X_train, y_train)

best = search.best_estimator_
print("Best params:", search.best_params_)

# 10) Evaluate on test set; remember to inverse-transform predictions with expm1
y_pred_log = best.predict(X_test)
y_pred = np.expm1(y_pred_log)   # back to original price scale
y_test_orig = np.expm1(y_test)

import numpy as np

mae = mean_absolute_error(y_test_orig, y_pred)
mse = mean_squared_error(y_test_orig, y_pred)   # mean squared error
rmse = np.sqrt(mse)                              # root mean squared error
r2 = r2_score(y_test_orig, y_pred)

print(f"MAE: {mae:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"R2: {r2:.4f}")


# 11) Save the pipeline (it contains preprocessing + model predicting log price)
joblib.dump(best, MODEL_PATH)
print("Saved pipeline to:", MODEL_PATH)
