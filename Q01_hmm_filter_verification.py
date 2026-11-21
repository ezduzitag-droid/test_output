"""Q01 verification: filtered vs smoothed HMM regime probabilities (synthetic data only)."""
import numpy as np
from hmmlearn.hmm import GaussianHMM
from scipy.stats import multivariate_normal

rng = np.random.default_rng(7)

# --- synthetic 2-regime, 2-feature series (NOT market data) ---
T, K = 3000, 2
A_true = np.array([[0.98, 0.02], [0.05, 0.95]])
mu = np.array([[0.0005, 0.004], [-0.0010, 0.015]])      # [return, vol-proxy]
sd = np.array([[0.004, 0.0015], [0.012, 0.005]])
s = np.zeros(T, int)
for t in range(1, T):
    s[t] = rng.choice(K, p=A_true[s[t - 1]])
X = rng.normal(mu[s], sd[s])

TRAIN = 2000
model = GaussianHMM(n_components=K, covariance_type="full", n_iter=200, random_state=0)
model.fit(X[:TRAIN])                                     # parameters see only data < TRAIN

def forward_filter(model, X):
    """Causal filtered P(s_t | x_1..x_t) using fixed fitted params. O(T*K^2)."""
    K = model.n_components
    B = np.column_stack([
        multivariate_normal(model.means_[k], model.covars_[k], allow_singular=True).pdf(X)
        for k in range(K)])
    out = np.zeros((len(X), K))
    alpha = model.startprob_ * B[0]
    out[0] = alpha / alpha.sum()
    for t in range(1, len(X)):
        alpha = (out[t - 1] @ model.transmat_) * B[t]
        out[t] = alpha / alpha.sum()
    return out

filt = forward_filter(model, X)
smooth_full = model.predict_proba(X)                     # forward-backward over ALL data

# 1) last row of predict_proba on a window ending at t == filtered prob at t
ts = np.arange(TRAIN, T, 97)
err = max(np.abs(model.predict_proba(X[:t + 1])[-1] - filt[t]).max() for t in ts)
print(f"[1] max |predict_proba(X[:t+1])[-1] - manual filter| over {len(ts)} t: {err:.2e}")

# 2) look-ahead: smoothed (full-sample) vs filtered at the same t
test = slice(TRAIN, T)
dis = (filt[test].argmax(1) != smooth_full[test].argmax(1)).mean()
mad = np.abs(filt[test] - smooth_full[test]).mean()
print(f"[2] test region: argmax disagreement filtered vs smoothed = {dis:.3%}; mean |dP| = {mad:.4f}")

# 3) Viterbi label instability: do past labels change when new data arrives?
w1 = model.predict(X[:2500])
w2 = model.predict(X[:3000])
chg = (w1 != w2[:2500])
print(f"[3] Viterbi: {chg.mean():.3%} of labels for t<2500 changed after appending 500 obs "
      f"(max index changed: {np.where(chg)[0].max() if chg.any() else None})")

# 4) leakage consequence: accuracy vs true regime, filtered vs smoothed, test region
acc_f = (filt[test].argmax(1) == s[test]).mean()
acc_s = (smooth_full[test].argmax(1) == s[test]).mean()
print(f"[4] agreement with true regime: filtered={acc_f:.3f}  smoothed(look-ahead)={acc_s:.3f}")
