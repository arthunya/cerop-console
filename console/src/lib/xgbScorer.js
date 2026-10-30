// Scores the exported CEROP financial XGBoost model in plain JavaScript.
//
// Input: one firm's raw (unscaled) feature values, keyed by feature name.
// Steps: StandardScaler transform -> walk every tree -> sum leaf values -> sigmoid.
// XGBoost works in float32, so feature values, split values and the running sum are
// rounded with Math.fround to follow the same arithmetic. A missing value (NaN) takes the
// node's default direction, as XGBoost does.
//
// Parity with Python predict_proba() is tested on all 1,364 test firms by
// console/scripts/parity.mjs.

const f32 = Math.fround;

function parseBaseScore(raw) {
  // xgboost 3.x stores base_score as a string such as "[1.4E-1]" or "5E-1"
  const s = String(raw).replace(/[[\]]/g, "");
  return parseFloat(s);
}

export function buildScorer(whatif) {
  const learner = whatif.booster.learner;
  const trees = learner.gradient_booster.model.trees;
  const baseScore = parseBaseScore(learner.learner_model_param.base_score);
  const objective = learner.objective.name;
  if (objective !== "binary:logistic") throw new Error(`unexpected objective ${objective}`);
  const baseMargin = Math.log(baseScore / (1 - baseScore));

  const names = whatif.feature_names;
  const order = whatif.model_feature_order.map((n) => {
    const i = names.indexOf(n);
    if (i < 0) throw new Error(`feature ${n} missing from scaler`);
    return i;
  });

  const compiled = trees.map((t) => ({
    left: t.left_children,
    right: t.right_children,
    feat: t.split_indices,
    cond: t.split_conditions.map(f32),
    defLeft: t.default_left.map((v) => v === 1 || v === true),
  }));

  function scaled(raw) {
    // raw: array in scaler (feature_names) order
    const z = new Array(order.length);
    for (let k = 0; k < order.length; k++) {
      const i = order[k];
      const v = raw[i];
      z[k] = v === null || v === undefined || Number.isNaN(v)
        ? NaN
        : f32((v - whatif.scaler_mean[i]) / whatif.scaler_scale[i]);
    }
    return z;
  }

  function margin(z) {
    let sum = f32(baseMargin);
    for (const t of compiled) {
      let n = 0;
      while (t.left[n] !== -1) {
        const x = z[t.feat[n]];
        if (Number.isNaN(x)) n = t.defLeft[n] ? t.left[n] : t.right[n];
        else n = x < t.cond[n] ? t.left[n] : t.right[n];
      }
      sum = f32(sum + t.cond[n]);
    }
    return sum;
  }

  function predictRaw(rawArray) {
    const m = margin(scaled(rawArray));
    return f32(1 / (1 + Math.exp(-m)));
  }

  function predictNamed(values) {
    return predictRaw(names.map((n) => values[n]));
  }

  return { predictRaw, predictNamed, featureNames: names };
}
