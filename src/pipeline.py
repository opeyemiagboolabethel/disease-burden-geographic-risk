"""Rebuild surveillance panel, chronological evaluation and planning outputs."""
import json
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from src.forecasting import MODELS, forecast, band
from src.rate_model import estimate_rates

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
FIPS = dict(zip('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split(), [1,2,4,5,6,8,9,10,11,12,13,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,44,45,46,47,48,49,50,51,53,54,55,56]))


def build():
    OUT.mkdir(exist_ok=True)
    raw = pd.read_csv(ROOT / 'data/state_cases.csv')
    monthly = pd.read_csv(ROOT / 'data/monthly_cases.csv')
    population = pd.read_csv(ROOT / 'data/state_population.csv', encoding='latin1')
    population = population.loc[population.SUMLEV.eq(40) & population.STATE.isin(FIPS.values())].copy()
    population['state'] = population.STATE.map({v:k for k,v in FIPS.items()})
    population['region'] = population.REGION.astype(str).map({'1':'Northeast','2':'Midwest','3':'South','4':'West'})
    meta = population[['state','NAME','region']].rename(columns={'NAME':'name'})
    annual = raw.loc[raw.Year.str.fullmatch(r'\d{4}')].copy()
    annual['year'] = annual.Year.astype(int)
    assert not annual.duplicated(['Type','State','year']).any()
    assert annual['Reported Cases'].ge(0).all()
    # Independently compare the state totals (including PR) with monthly totals.
    checks = []
    for t in raw.Type.unique():
        for y in range(2004, 2026):
            x = annual.loc[annual.Type.eq(t) & annual.year.eq(y), 'Reported Cases'].sum()
            m = monthly.loc[monthly.Type.eq(t) & monthly.Year.eq(str(y)), 'Reported Cases'].sum()
            checks.append({'type':t,'year':y,'state_total_including_PR':int(x),'monthly_total':int(m),'matches':bool(x==m)})
    audit = pd.DataFrame(checks)
    assert audit.matches.all(), 'Source totals differ: investigate before zero expansion.'
    types = list(raw.Type.unique())
    grid = pd.MultiIndex.from_product([types,sorted(FIPS),range(2004,2026)], names=['type','state','year']).to_frame(index=False)
    annual = annual.rename(columns={'Type':'type','State':'state','Reported Cases':'cases'})
    panel = grid.merge(annual[['type','state','year','cases']], on=['type','state','year'], how='left', validate='one_to_one')
    panel['source_row_present'] = panel.cases.notna()
    panel['cases'] = panel.cases.fillna(0).astype(int)
    panel = panel.merge(meta, on='state', validate='many_to_one')
    # Same-year July population denominators; rates intentionally absent before 2020.
    pops = population.melt(id_vars='state',value_vars=[f'POPESTIMATE{y}' for y in range(2020,2026)],var_name='year',value_name='population')
    pops['year'] = pops.year.str[-4:].astype(int)
    panel = panel.merge(pops,on=['state','year'],how='left',validate='many_to_one')
    panel['reported_rate_100k'] = panel.cases / panel.population * 100000
    series = {(t,s):g.sort_values('year').set_index('year').cases for (t,s),g in panel.groupby(['type','state'])}
    rows=[]
    phases={'selection':[2011,2012], 'calibration':[2015,2016,2017], 'test':[2022]}
    for (t,s), vals in series.items():
        for phase, origins in phases.items():
            for origin in origins:
                history=vals.loc[:origin].values
                for model in MODELS:
                    for h,pred in enumerate(forecast(history,model),1):
                        actual=float(vals.loc[origin+h])
                        rows.append({'type':t,'state':s,'phase':phase,'origin':origin,'horizon':h,'year':origin+h,'model':model,'prediction':float(pred),'actual':actual,'absolute_error':abs(pred-actual),'absolute_log_error':abs(np.log1p(pred)-np.log1p(actual))})
    predictions=pd.DataFrame(rows)
    scores=predictions.groupby(['type','phase','model'],as_index=False).agg(mae=('absolute_error','mean'),log_mae=('absolute_log_error','mean'),n=('actual','size'))
    selection=scores.loc[scores.phase.eq('selection')].sort_values(['type','mae','model']).groupby('type',as_index=False).first()
    champions=dict(zip(selection.type,selection.model))
    chosen=predictions.loc[predictions.model.eq(predictions.type.map(champions))].copy()
    widths=chosen.loc[chosen.phase.eq('calibration')].groupby(['type','horizon'],as_index=False).agg(width=('absolute_log_error',lambda x:np.quantile(x,.9,method='higher')),n=('actual','size'))
    chosen=chosen.merge(widths,on=['type','horizon'],validate='many_to_one')
    chosen['lower'],chosen['upper']=band(chosen.prediction,chosen.width)
    chosen['covered']=chosen.actual.ge(chosen.lower)&chosen.actual.le(chosen.upper)
    evaluation=chosen.loc[chosen.phase.eq('test')].groupby(['type','horizon'],as_index=False).agg(mae=('absolute_error','mean'),log_mae=('absolute_log_error','mean'),band_coverage=('covered','mean'),n=('actual','size'))
    future=[]
    for (t,s), vals in series.items():
        for h,pred in enumerate(forecast(vals.values,champions[t]),1):
            width=float(widths.loc[widths.type.eq(t)&widths.horizon.eq(h),'width'].iloc[0])
            lo,hi=band(pred,width)
            future.append({'type':t,'state':s,'year':2025+h,'horizon':h,'model':champions[t],'prediction':float(pred),'lower':float(lo),'upper':float(hi)})
    future=pd.DataFrame(future).merge(meta,on='state',validate='many_to_one')
    latest=panel.loc[panel.year.eq(2025)].copy()
    baseline=panel.loc[panel.year.between(2020,2024)].groupby(['type','state'],as_index=False).agg(baseline_mean_cases=('cases','mean'),baseline_mean_rate=('reported_rate_100k','mean'))
    latest=latest.merge(baseline,on=['type','state'],validate='one_to_one')
    latest['rate_difference']=latest.reported_rate_100k-latest.baseline_mean_rate
    q=latest.groupby('type').reported_rate_100k.quantile(.75)
    latest['high_rate']=latest.reported_rate_100k.ge(latest.type.map(q))
    latest['profile']=np.select([latest.high_rate & latest.rate_difference.gt(0),latest.high_rate],['Higher rate / above recent baseline','Higher rate / at or below baseline'],default='Below upper-quartile rate')
    latest['relative_change_cases']=np.where(latest.baseline_mean_cases.gt(0),(latest.cases/latest.baseline_mean_cases-1)*100,np.nan)
    latest['upper_quartile_cutoff']=latest.type.map(q)
    recent_test=chosen.loc[chosen.phase.eq('test')&chosen.year.eq(2025),['type','state','prediction','upper','actual']].copy()
    latest=latest.merge(recent_test,on=['type','state'],validate='one_to_one')
    latest['above_forecast_band']=latest.actual.gt(latest.upper)
    rate_fits=[]
    for t in types:
        idx=latest.index[latest.type.eq(t)]
        fitted=estimate_rates(latest.loc[idx,'cases'],latest.loc[idx,'population'])
        for key,column in [('mean','smoothed_rate'),('lower','rate_lower'),('upper','rate_upper'),('prob_above_pooled','prob_above_pooled')]:
            latest.loc[idx,column]=fitted[key]
        rate_fits.append({'type':t,**{k:fitted[k] for k in ['alpha','beta','pooled_rate','converged']}})
    pd.DataFrame(rate_fits).to_csv(OUT/'rate_model_parameters.csv',index=False)
    tables={'annual_panel':panel,'source_total_audit':audit,'all_predictions':predictions,'model_scores':scores,'selected_models':selection,'calibration_widths':widths,'selected_predictions':chosen,'test_evaluation':evaluation,'future_forecasts':future,'geographic_profiles':latest}
    with sqlite3.connect(OUT/'surveillance.sqlite') as conn:
        for name,frame in tables.items():
            frame.to_csv(OUT/(name+'.csv'),index=False)
            frame.to_sql(name,conn,if_exists='replace',index=False)
        sql=(ROOT/'analysis.sql').read_text()
        regional=pd.read_sql_query(sql,conn)
        regional.to_csv(OUT/'regional_summary.csv',index=False)
    summary={'states_and_DC':51,'years':[2004,2025],'rows':len(panel),'zero_expanded_rows':int((~panel.source_row_present).sum()),'champions':champions,'selection_target_years':[2012,2015],'calibration_target_years':[2016,2020],'test_origin':2022,'test_years':[2023,2025],'forecast_years':[2026,2028],'source_total_checks':len(audit),'latest_totals':latest.groupby('type').cases.sum().astype(int).to_dict(),'rates_available':[2020,2025]}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    print(evaluation.to_string(index=False))


if __name__=='__main__':
    build()
