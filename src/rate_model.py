"""Empirical-Bayes Gamma-Poisson model of reported area-level disease rates."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln
from scipy.stats import gamma


def estimate_rates(counts, populations):
    counts=np.asarray(counts,dtype=float)
    exposure=np.asarray(populations,dtype=float)/100000
    if (counts<0).any() or (exposure<=0).any():
        raise ValueError('Counts must be nonnegative and exposures positive.')
    pooled=counts.sum()/exposure.sum()
    def objective(par):
        a,b=np.exp(par)
        logp=gammaln(counts+a)-gammaln(a)-gammaln(counts+1)+a*(np.log(b)-np.log(b+exposure))+counts*(np.log(exposure)-np.log(b+exposure))
        return -float(logp.sum())
    fits=[minimize(objective,np.log([a,a/max(pooled,1e-8)]),method='L-BFGS-B',bounds=[(-8,12),(-8,12)]) for a in [.2,1,5]]
    fit=min(fits,key=lambda x:x.fun)
    if not fit.success:raise RuntimeError(fit.message)
    alpha,beta=np.exp(fit.x)
    shape=alpha+counts;rate=beta+exposure
    return {'mean':shape/rate,'lower':gamma.ppf(.05,shape,scale=1/rate),'upper':gamma.ppf(.95,shape,scale=1/rate),'prob_above_pooled':gamma.sf(pooled,shape,scale=1/rate),'alpha':float(alpha),'beta':float(beta),'pooled_rate':float(pooled),'converged':bool(fit.success)}
