import numpy as np


def ridge_fit(X: np.ndarray, Y: np.ndarray, lam: float = 1e-6) -> np.ndarray:
    """Ridge-regress X -> Y with intercept. Returns weight matrix W."""
    Xb = np.hstack([X, np.ones((X.shape[0], 1))])
    A = Xb.T @ Xb + lam * np.eye(Xb.shape[1])
    return np.linalg.solve(A, Xb.T @ Y)


def ridge_predict(X: np.ndarray, W: np.ndarray) -> np.ndarray:
    Xb = np.hstack([X, np.ones((X.shape[0], 1))])
    return Xb @ W


def nrmse(y: np.ndarray, yhat: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y - yhat) ** 2)) / (np.std(y) + 1e-12))


def squared_corr(y: np.ndarray, yhat: np.ndarray) -> float:
    """Squared Pearson correlation — the per-delay term in Jaeger's memory capacity."""
    if np.std(y) < 1e-12 or np.std(yhat) < 1e-12:
        return 0.0
    return float(np.corrcoef(y, yhat)[0, 1] ** 2)
