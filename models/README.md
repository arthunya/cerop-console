# Models

Exported once from the course notebooks (2026-08-17) and only ever loaded read-only since.

| File | Object | Size | SHA-256 |
|---|---|---|---|
| `cerop_financial_xgb.pkl` | `XGBClassifier`, Week 5 configuration | 456 KB | `5769f46c80324094f6569d2b2d9c99d68dcb91ba70afc34d42e6789d14a2ed7c` |
| `cerop_financial_preprocessor.pkl` | `StandardScaler` (85 features) | 5 KB | `92c6239e7dfa0a6d43599437d1d36b8cb8f75b7595ef1e93ec4c548b68908727` |
| `cerop_operations_preprocessor.pkl` | Week 4 `ColumnTransformer` (35 outputs) | 12 KB | `903708ae9088c1dbdf554b152fd502f18b0d6a37ea5020d2e2413a59b9938b3f` |
| `cerop_operations_rf.pkl` | Tuned `RandomForestClassifier` (`final_model`, 500 trees, 27 features) | 1.24 GB | `b190d51974aca308bbd022f0fbe588df120cc37ca47522e1043245a5d59f6390` |

The Random Forest is too large for git and isn't hosted in this repo. It's available on request: open an issue or contact the author via [LinkedIn](https://linkedin.com/in/arthunya). Check any copy against the hash above.

Saved with `xgboost==3.4.1` and `scikit-learn==1.9.0` (see `requirements.txt`). Loading them with other versions may warn or fail.

Before chaining the operations preprocessor into the Random Forest, read [docs/limitations.md](../docs/limitations.md#saved-artifacts): the outputs need reindexing to `model.feature_names_in_`, and one column's scale differs from the model's training data.
