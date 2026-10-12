"""Explore West Nile burden, geographic contrasts and evaluated forecasts."""
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Disease Burden & Geographic Intelligence | Opeyemi Agboola',page_icon='🗺️',layout='wide')
st.markdown('''<style>
.block-container{max-width:1450px;padding-top:2rem;padding-bottom:3rem}
.hero{background:linear-gradient(115deg,#092739,#10666b);border-radius:22px;padding:2.5rem;color:#fff;margin-bottom:1.4rem}
.hero h1{color:white;font-size:clamp(2rem,3.2vw,3.6rem);line-height:1.1;margin:.8rem 0}
.hero p{color:#d8eeea;max-width:900px;font-size:1.05rem}.eyebrow{font-size:.78rem;letter-spacing:.13em;text-transform:uppercase}
[data-testid="stMetric"]{background:#fff;border:1px solid #dce6e2;padding:1rem;border-radius:15px}
button[data-baseweb="tab"]{font-size:1rem}footer{display:none}
</style>''',unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="eyebrow">Opeyemi Agboola · Public Health Data Science</div><h1>Where burden concentrates.<br>How uncertain the outlook is.</h1><p>West Nile surveillance intelligence: geographic comparisons, independently tested forecasts and transparent planning bands, using CDC records and Census population estimates.</p></div>''',unsafe_allow_html=True)

@st.cache_data
def load():
    names=['annual_panel','geographic_profiles','future_forecasts','selected_predictions','model_scores','test_evaluation','source_total_audit','regional_summary']
    return {k:pd.read_csv(ROOT/'outputs'/f'{k}.csv') for k in names},json.loads((ROOT/'outputs/summary.json').read_text())

data,summary=load()
panel=data['annual_panel'];profiles=data['geographic_profiles']
with st.sidebar:
    st.subheader('Explore the evidence')
    case_type=st.selectbox('Disease category',['Neuroinvasive disease cases','All disease cases'])
    st.caption('Neuroinvasive cases are included within all disease cases. These categories must not be added together.')
    regions=st.multiselect('Census regions',sorted(panel.region.unique()),help='Leave blank to include all four regions.')
    names=sorted(panel.name.unique())
    state_name=st.selectbox('State briefing',names,index=names.index('Colorado'))
    st.caption('Finalised CDC records through 2025 · Census Vintage 2025 · Downloaded 12 October 2026')

scope=profiles.loc[profiles.type.eq(case_type)].copy()
if regions:scope=scope.loc[scope.region.isin(regions)]
country=panel.loc[panel.type.eq(case_type)]
if regions:country=country.loc[country.region.isin(regions)]
columns=st.columns(4)
columns[0].metric('Reported cases · 2025',f'{scope.cases.sum():,.0f}')
columns[1].metric('Reported rate / 100,000',f'{scope.cases.sum()/scope.population.sum()*100000:.2f}' if len(scope) else '—')
columns[2].metric('States + DC in scope',len(scope))
columns[3].metric('Above recent rate baseline',int(scope.rate_difference.gt(0).sum()))
st.caption('Geography is state of residence, not necessarily place of infection. These are reported disease cases, not all infections or individual risk estimates.')

def style(fig):
    fig.update_layout(template='plotly_white',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font={'family':'Arial','color':'#163340'},margin={'l':15,'r':15,'t':35,'b':30})
    return fig

def csv(frame):return frame.to_csv(index=False).encode()

atlas,brief,forecast_tab,evidence,methods=st.tabs(['Geographic atlas','State briefing','Forecast laboratory','Model evidence','Data & methods'])
with atlas:
    st.subheader('Burden volume and population-adjusted rates tell different stories')
    measure=st.radio('Map measure',['Reported rate per 100,000','Reported cases','Geographic profile'],horizontal=True)
    if scope.empty:
        st.info('No geographic units in this scope.')
    else:
        color={'Reported rate per 100,000':'reported_rate_100k','Reported cases':'cases','Geographic profile':'profile'}[measure]
        args={'color_continuous_scale':['#e1efec','#248d8e','#153c50']} if color!='profile' else {'color_discrete_map':{'Higher rate / above recent baseline':'#b46d35','Higher rate / at or below baseline':'#336a83','Below upper-quartile rate':'#abcfc7'}}
        fig=px.choropleth(scope,locations='state',locationmode='USA-states',scope='usa',color=color,hover_name='name',hover_data={'cases':':,','reported_rate_100k':':.2f','baseline_mean_rate':':.2f','population':':,','state':False},labels={'reported_rate_100k':'Rate / 100,000','cases':'Cases','profile':'Profile'},**args)
        fig.update_geos(projection_type='albers usa',showlakes=False,bgcolor='rgba(0,0,0,0)');fig.update_layout(height=530)
        st.plotly_chart(style(fig),width='stretch')
        st.caption('2025 rates use same-year July Census population estimates. Profiles use the full 51-unit upper-quartile rate threshold and compare 2025 with the mean annual rate for 2020–2024. Filters do not redefine those thresholds. Small counts can produce unstable rates.')
        rank=scope.sort_values('reported_rate_100k',ascending=False)
        st.dataframe(rank[['name','region','cases','reported_rate_100k','baseline_mean_rate','profile']],hide_index=True,width='stretch')
        st.download_button('Download geographic evidence',csv(rank),'geographic_evidence.csv','text/csv',key='atlas_csv')

with brief:
    # The state briefing has its own selector; regional filtering only affects atlas/metrics.
    record=profiles.loc[profiles.type.eq(case_type)&profiles.name.eq(state_name)].iloc[0]
    history=panel.loc[panel.type.eq(case_type)&panel.name.eq(state_name)].sort_values('year')
    st.subheader(f'{state_name}: from surveillance to a planning conversation')
    st.caption('This briefing follows the selected state independently of the regional filter.')
    a,b=st.columns([2,1])
    with a:
        fig=px.line(history,x='year',y='cases',markers=True,labels={'cases':'Reported cases','year':'Year'},color_discrete_sequence=['#147c80'])
        st.plotly_chart(style(fig),width='stretch')
    with b:
        st.metric('Reported cases · 2025',f'{record.cases:,}')
        st.metric('Rate per 100,000 · 2025',f'{record.reported_rate_100k:.2f}')
        st.write(f'**Geographic profile:** {record.profile}')
        st.write(f'2020–2024 mean annual rate: **{record.baseline_mean_rate:.2f}** per 100,000.')
        st.write('2025 exceeded the pre-defined three-year forecast band.' if record.above_forecast_band else '2025 stayed within the pre-defined three-year forecast band.')
    rates=history.loc[history.year.ge(2020)]
    st.plotly_chart(style(px.bar(rates,x='year',y='reported_rate_100k',labels={'reported_rate_100k':'Reported rate / 100,000'},color_discrete_sequence=['#bd813f'])),width='stretch')
    text=f'''# {state_name}: West Nile surveillance briefing\n\nCategory: {case_type}\n2025 reported cases: {record.cases}\n2025 reported rate: {record.reported_rate_100k:.2f} per 100,000\n2020–2024 mean annual rate: {record.baseline_mean_rate:.2f}\nProfile: {record.profile}\n\nInterpretation: compare burden volume and rate; inspect reporting and local context before acting. Residence is not necessarily exposure location. Small counts are unstable. No individual risk or causal explanation is inferred.\n\nSources: CDC ArboNET historic data, finalised 16 September 2026; Census population estimates Vintage 2025; accessed 12 October 2026. Independent analysis by Opeyemi Agboola, without agency endorsement.\n'''
    st.download_button('Download state briefing',text,f'{record.state}_surveillance_briefing.md','text/markdown')

    st.subheader('Area-level rate uncertainty')
    a,b,c=st.columns(3)
    a.metric('Smoothed reported rate / 100,000',f'{record.smoothed_rate:.2f}')
    b.metric('90% conditional credible range',f'{record.rate_lower:.2f}–{record.rate_upper:.2f}')
    c.metric('Probability above pooled U.S. rate',f'{record.prob_above_pooled:.1%}')
    st.caption('Empirical-Bayes Gamma-Poisson model: counts follow a Poisson distribution conditional on a state rate; state rates share a fitted Gamma prior. The probability concerns the reported state-level rate, not individual infection risk. These conditional intervals omit uncertainty in fitted hyperparameters, reporting and population estimates; they are distinct from forecast bands. No adjacency or spatial transmission is modelled.')

with forecast_tab:
    st.subheader('A forecast should show its limits as clearly as its central estimate')
    record=profiles.loc[profiles.type.eq(case_type)&profiles.name.eq(state_name)].iloc[0]
    historical=panel.loc[panel.type.eq(case_type)&panel.name.eq(state_name)].sort_values('year')
    outlook=st.radio('Forecast view',['2026–2028 planning outlook','2023–2025 independent test'],horizontal=True)
    if outlook.startswith('2026'):
        f=data['future_forecasts']; f=f.loc[f.type.eq(case_type)&f.name.eq(state_name)].sort_values('year')
        cutoff=2025
    else:
        f=data['selected_predictions'];f=f.loc[f.type.eq(case_type)&f.state.eq(record.state)&f.phase.eq('test')].sort_values('year')
        cutoff=2022
    hist=historical.loc[historical.year.le(cutoff)]
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=hist.year,y=hist.cases,name='Reported history',mode='lines+markers',line={'color':'#147c80'}))
    fig.add_trace(go.Scatter(x=f.year,y=f.upper,name='Planning band',mode='lines',line={'width':0},showlegend=False))
    fig.add_trace(go.Scatter(x=f.year,y=f.lower,name='Empirical planning band',fill='tonexty',fillcolor='rgba(20,124,128,.16)',line={'width':0}))
    fig.add_trace(go.Scatter(x=[cutoff]+f.year.tolist(),y=[hist.cases.iloc[-1]]+f.prediction.tolist(),name='Selected forecast',mode='lines+markers',line={'color':'#bc813b','dash':'dash'}))
    if cutoff==2022:
        fig.add_trace(go.Scatter(x=f.year,y=f.actual,name='Held-out reported cases',mode='lines+markers',line={'color':'#874b67'}))
    fig.update_layout(yaxis_title='Reported disease cases',xaxis_title='Year',height=440)
    st.plotly_chart(style(fig),width='stretch')
    st.caption('The five-year mean was selected before calibration and testing. Bands use the 90th percentile of pooled absolute log-count errors separately for each horizon. These are empirical planning ranges, not guaranteed 90% prediction intervals. No future population assumptions or future incidence rates are manufactured.')
    st.dataframe(f[['year','prediction','lower','upper']],hide_index=True,width='stretch')
    st.download_button('Download selected forecast',csv(f),f'{record.state}_forecast.csv','text/csv')

with evidence:
    st.subheader('Selection happens before we look at the final test')
    st.write('**Selection:** origins 2011 and 2012 → targets through 2015. **Calibration:** origins 2015–2017 → targets through 2020. **Final test:** origin 2022 → 2023–2025. Each fit sees only history available at its origin.')
    scores=data['model_scores'].loc[data['model_scores'].type.eq(case_type)]
    comparison=scores.loc[scores.phase.isin(['selection','test'])]
    fig=px.bar(comparison,x='model',y='mae',color='phase',barmode='group',labels={'mae':'Mean absolute error · cases per state/year','model':'Model'},color_discrete_map={'selection':'#147c80','test':'#bc813b'})
    st.plotly_chart(style(fig),width='stretch')
    st.info('The five-year mean is the selected model. Last-year persistence has a lower count-scale error in the final test, but is not retrospectively substituted. This is evidence of changing forecast performance, not proof that a more complex model is better.')
    st.dataframe(data['test_evaluation'].loc[data['test_evaluation'].type.eq(case_type)],hide_index=True,width='stretch')
    st.caption('MAE weights larger absolute errors more heavily; log-MAE provides a complementary scale-sensitive view. Coverage is observed across 51 units at each horizon. Years, geographic units and overlapping calibration windows are dependent; no statistical coverage guarantee is claimed.')

with methods:
    st.subheader('Traceable inputs. Explicit assumptions.')
    st.markdown('''
**Sources:** [CDC historic ArboNET data](https://www.cdc.gov/west-nile-virus/data-maps/historic-data.html), finalised 16 September 2026, and [Census Vintage 2025 population estimates](https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html). Accessed 12 October 2026.

**Scope:** 50 states and DC, 2004–2025. Puerto Rico appears in the source but is excluded from this analytical scope. Earlier emergence years are omitted. Neuroinvasive disease is a subset of all disease; the two panels are analysed independently.

**Zero expansion:** the CDC map CSV lists positive-count state/year entries. Absent entries are treated as zero *reported* cases in the expanded panel. Before expansion, 44 category/year state totals, including Puerto Rico, reconcile exactly with independently downloaded national monthly totals for 2004–2025. This supports the treatment within these files; zero is not proof of no infections or perfect surveillance.

**Forecast models:** last-year persistence, recent three-year mean, recent five-year mean and a fixed damped five-year log-linear trend. A separate global champion is selected for each category using selection-period count MAE, with deterministic tie-breaking. No final-test tuning.

**Geography:** reported population-adjusted rates are available only for 2020–2025, using matching-year population estimates. The profile is a descriptive rate/baseline screen, not a causal spatial model or an individual risk score. No sub-state geographic precision is implied.

**Rate uncertainty:** a Gamma-Poisson empirical-Bayes model fits a shared Gamma prior by marginal maximum likelihood to 2025 state counts and population exposures. Posterior means, conditional 90% credible ranges and probabilities above the observed pooled national reported rate support an area-level comparison. Hyperparameter uncertainty and dependence between states are omitted. This model does not account for adjacency, transmission, underdiagnosis or individual exposure.

**Limitations:** reporting and diagnosis affect the series; non-neuroinvasive illness is particularly underreported. Weather, mosquito surveillance, local interventions and exposure location are not modelled. Latest-vintage historical data can contain revisions, so this is retrospective chronological evaluation, not a reconstruction of real-time data availability. The 2026–2028 outlook is a research planning exercise, not an official agency forecast.

Independent research application by Opeyemi Agboola. CDC and Census have not endorsed this application. No patient-level data, API key or live data connection is needed.
''')
    st.dataframe(data['source_total_audit'],hide_index=True,width='stretch')
    st.download_button('Download source reconciliation',csv(data['source_total_audit']),'source_reconciliation.csv','text/csv')
