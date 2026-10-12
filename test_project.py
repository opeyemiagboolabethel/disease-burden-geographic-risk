"""Check evidence alignment, chronology, count integrity and application interactions."""
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.forecasting import forecast,band
from src.rate_model import estimate_rates

ROOT=Path(__file__).resolve().parent

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel=pd.read_csv(ROOT/'outputs/annual_panel.csv')
        cls.pred=pd.read_csv(ROOT/'outputs/all_predictions.csv')
        cls.latest=pd.read_csv(ROOT/'outputs/geographic_profiles.csv')

    def test_complete_panel_and_category_subset(self):
        p=self.panel
        self.assertEqual(len(p),2*51*22)
        self.assertFalse(p.duplicated(['type','state','year']).any())
        wide=p.pivot(index=['state','year'],columns='type',values='cases')
        self.assertTrue((wide['Neuroinvasive disease cases']<=wide['All disease cases']).all())

    def test_independent_source_reconciliation(self):
        a=pd.read_csv(ROOT/'outputs/source_total_audit.csv')
        self.assertEqual(len(a),44)
        self.assertTrue(a.matches.all())

    def test_same_year_population_denominators(self):
        p=self.panel
        self.assertTrue(p.loc[p.year.lt(2020),'reported_rate_100k'].isna().all())
        recent=p.loc[p.year.ge(2020)]
        self.assertTrue(recent.population.gt(0).all())
        np.testing.assert_allclose(recent.reported_rate_100k,recent.cases/recent.population*100000)

    def test_disjoint_target_periods_and_horizons(self):
        p=self.pred
        self.assertTrue((p.year==p.origin+p.horizon).all())
        self.assertLess(p[p.phase.eq('selection')].year.max(),p[p.phase.eq('calibration')].year.min())
        self.assertLess(p[p.phase.eq('calibration')].year.max(),p[p.phase.eq('test')].year.min())

    def test_prediction_uses_origin_history_not_future(self):
        for state in ['AZ','CO','NY','AK']:
            vals=self.panel[self.panel.state.eq(state)&self.panel.type.eq('All disease cases')].set_index('year').cases
            row=self.pred[(self.pred.state.eq(state))&(self.pred.type.eq('All disease cases'))&self.pred.phase.eq('test')&self.pred.model.eq('mean_5')]
            expected=vals.loc[2018:2022].mean()
            np.testing.assert_allclose(row.prediction,expected)
            self.assertEqual(len(row),3)

    def test_test_labels_are_actual_source_records(self):
        merged=self.pred.merge(self.panel[['type','state','year','cases']],on=['type','state','year'],validate='many_to_one')
        np.testing.assert_array_equal(merged.actual,merged.cases)

    def test_rate_posterior_bounds_and_count_support(self):
        p=self.latest
        self.assertTrue((p.rate_lower<=p.smoothed_rate).all())
        self.assertTrue((p.smoothed_rate<=p.rate_upper).all())
        self.assertTrue(p.prob_above_pooled.between(0,1).all())
        fitted=estimate_rates([0,10,50,120],[100000,200000,1000000,2000000])
        self.assertGreater(fitted['mean'][0],0)
        self.assertTrue(fitted['converged'])
        self.assertTrue(np.isfinite(fitted['upper']).all())

    def test_nonnegative_forecasts_and_calibration_widths(self):
        f=pd.read_csv(ROOT/'outputs/future_forecasts.csv')
        self.assertEqual(len(f),2*51*3)
        self.assertTrue(f[['prediction','lower','upper']].ge(0).all().all())
        self.assertTrue((f.lower<=f.prediction).all()&(f.prediction<=f.upper).all())

    def test_application_filters_and_views(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/'streamlit_app.py')).run(timeout=30)
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'1,517')
        app.selectbox[0].select('All disease cases').run(timeout=30)
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'2,167')
        app.multiselect[0].select('West').run(timeout=30)
        self.assertEqual(len(app.exception),0)
        app.selectbox[1].select('Alaska').run(timeout=30)
        app.radio[1].set_value('2023–2025 independent test').run(timeout=30)
        self.assertEqual(len(app.exception),0)

if __name__=='__main__':unittest.main()
