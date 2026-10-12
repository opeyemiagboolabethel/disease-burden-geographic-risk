"""Create publication-style figures from the committed evidence tables."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'#f6f7f3','axes.facecolor':'#f6f7f3','text.color':'#163340','axes.labelcolor':'#163340'})
t='Neuroinvasive disease cases'
s=pd.read_csv(OUT/'model_scores.csv');s=s[s.type.eq(t)].pivot(index='model',columns='phase',values='mae').loc[['last_year','mean_3','mean_5','damped_log_trend']]
fig,ax=plt.subplots(figsize=(11,5.5));s[['selection','test']].plot.bar(ax=ax,color=['#147c80','#bd813f'],width=.7)
ax.set_xticklabels(['Last year','3-year mean','5-year mean\n(selected)','Damped log trend'],rotation=0)
ax.set_xlabel('');ax.set_ylabel('Mean absolute error · cases / state / year');ax.set_title('Selection winner and later test performance are different questions',loc='left',pad=20)
ax.legend(['Earlier selection','Final test'],frameon=False);fig.text(.08,.015,'CDC ArboNET · 51 geographic units · Fixed three-year test origin 2022 · Independent analysis',fontsize=9)
fig.tight_layout(rect=[0,.045,1,1]);fig.savefig(OUT/'model-comparison.svg');fig.savefig(OUT/'model-comparison.png',dpi=140);plt.close(fig)

p=pd.read_csv(OUT/'geographic_profiles.csv');p=p[p.type.eq(t)].nlargest(12,'reported_rate_100k').sort_values('reported_rate_100k')
fig,ax=plt.subplots(figsize=(11,7));ax.errorbar(p.smoothed_rate,p.name,xerr=[p.smoothed_rate-p.rate_lower,p.rate_upper-p.smoothed_rate],fmt='o',color='#147c80',capsize=4,label='Smoothed rate + conditional 90% range')
ax.scatter(p.reported_rate_100k,p.name,color='#bd813f',marker='x',s=60,label='Raw reported rate',zorder=4)
ax.set_xlabel('Reported neuroinvasive disease rate / 100,000 residents');ax.set_title('Geographic burden, with area-level uncertainty visible',loc='left',pad=20)
ax.legend(frameon=False,loc='lower right');fig.text(.08,.015,'2025 · CDC + Census · Gamma-Poisson empirical Bayes · Hyperparameter/reporting uncertainty omitted',fontsize=9)
fig.tight_layout(rect=[0,.045,1,1]);fig.savefig(OUT/'geographic-rate-uncertainty.svg');fig.savefig(OUT/'geographic-rate-uncertainty.png',dpi=140);plt.close(fig)
