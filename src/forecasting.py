"""Small, auditable forecasting models for annual surveillance counts."""
import numpy as np

MODELS = ('last_year', 'mean_3', 'mean_5', 'damped_log_trend')


def forecast(values, model, horizon=3):
    y = np.asarray(values, dtype=float)
    if len(y) < 5 or not np.isfinite(y).all() or (y < 0).any():
        raise ValueError('At least five finite nonnegative observations are required.')
    if model == 'last_year':
        out = np.repeat(y[-1], horizon)
    elif model.startswith('mean_'):
        out = np.repeat(y[-int(model.split('_')[1]):].mean(), horizon)
    elif model == 'damped_log_trend':
        z = np.log1p(y[-5:])
        slope, intercept = np.polyfit(np.arange(5), z, 1)
        # Fixed damping, not tuned on calibration or test observations.
        steps = np.cumsum(.8 ** np.arange(1, horizon + 1))
        out = np.expm1(intercept + 4 * slope + slope * steps)
    else:
        raise ValueError(model)
    return np.maximum(out, 0)


def band(prediction, width):
    z = np.log1p(np.asarray(prediction, dtype=float))
    return np.maximum(np.expm1(z - width), 0), np.expm1(z + width)
