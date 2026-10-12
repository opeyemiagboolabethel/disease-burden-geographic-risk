# Disease Burden Forecasting & Geographic Risk Modelling

An independent public-health data-science project by Opeyemi Agboola. It uses West Nile disease surveillance to connect geographic burden, area-level rate uncertainty, chronological forecasting evaluation and usable planning evidence.

## Evidence and scope

- **CDC ArboNET:** historic West Nile human disease records, finalised 16 September 2026. [Official source](https://www.cdc.gov/west-nile-virus/data-maps/historic-data.html).
- **U.S. Census Bureau:** Vintage 2025 annual state population estimates for 2020–2025. [Official source](https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html).
- Both sources were downloaded on **12 October 2026**. Full original CSV files and SHA-256 fingerprints are included. Attribution to CDC, participating state health departments and the Census Bureau applies to the source evidence. This application is independent and is not endorsed by either agency. Agency logos are not used.

The analytical panel covers **50 states and DC, 2004–2025**, with 2,244 category/state/year rows. All disease cases and neuroinvasive cases are analysed separately; neuroinvasive cases are included within all disease cases and must not be added to them. Puerto Rico is present in the source but excluded from the 51-unit analysis.

The CDC mapping file provides positive-count entries. The panel expands absent state/category/year entries to zero **reported** cases. Before expansion, all **44** category/year totals for 2004–2025, including Puerto Rico, reconcile with independently downloaded national monthly totals. This does not establish zero infection or complete surveillance. Earlier emergence years are excluded; a 1999 state/month discrepancy is outside the analytical period.

## What this project demonstrates

1. A geographic atlas that distinguishes reported case volume from population-adjusted rates.
2. Matching-year population denominators, available only for 2020–2025.
3. A Gamma-Poisson empirical-Bayes model of 2025 area-level reported rates, with conditional credible ranges.
4. Model selection, separately calibrated planning bands and a later chronological test.
5. State briefings, downloadable evidence, SQL regional summaries and a reproducible application.

The profile categories compare the 2025 reported rate with the full 51-unit upper quartile and with the average annual rate in 2020–2024. They are transparent descriptive screens, not causal explanations, individual risk scores or formal hotspot tests. No adjacency, spatial dependence or transmission model is implied.

## Forecasting design

Four fixed candidates: last-year persistence, recent three-year mean, recent five-year mean and a five-year log-linear trend with a fixed damping factor of 0.8. Counts are nonnegative, and trend fitting uses log(1+count).

| Phase | Origins | Target years | Purpose |
| --- | --- | --- | --- |
| Selection | 2011, 2012 | 2012–2015 | Choose one global model separately for each disease category |
| Calibration | 2015, 2016, 2017 | 2016–2020 | Estimate horizon-specific absolute log-error widths |
| Final test | 2022 | 2023–2025 | Inspect forecasts and band coverage after choices are fixed |
| Planning outlook | 2025 | 2026–2028 | Refit the selected method to observed history |

The target periods do not overlap across phases. Training includes only observations at or before each origin. Model selection uses mean absolute count error, with deterministic tie-breaking. The five-year mean wins selection for both categories. Last-year persistence has lower count MAE in the final test; it is reported but not retrospectively made the selected champion.

Calibration pools 153 state-origin errors for each category/horizon. The 90th percentile, using the higher observed order statistic, becomes a symmetric band on the log-count scale. Bands are transformed back and lower bounds clipped at zero. These are empirical planning bands, not distribution-free or guaranteed 90% prediction intervals. Repeated states and overlapping target windows introduce dependence.

## Area-level rate model

For each category, reported 2025 counts follow a Poisson model conditional on a state rate and population exposure (population divided by 100,000). State rates share a Gamma prior fitted by marginal maximum likelihood. The conditional Gamma posterior yields means, 5th/95th percentiles and probability above the observed pooled national reported rate. Three fixed optimisation initialisations provide a basic numerical check; converged fits are required.

Hyperparameters are estimated from these same 51 units. Their uncertainty is not included in the displayed credible ranges. Reporting, population uncertainty and geographic dependence are also omitted. A high probability concerns a reported **area-level** disease rate, not an individual's infection probability.

## Run

Use Python **3.12**. All processed outputs are committed, so the application requires no secrets, API account or live source download.

```sh
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Streamlit Community Cloud: select the separate repository, branch `main`, entrypoint `streamlit_app.py`, Python **3.12**. No secrets are needed.

## Reproduce

```sh
pip install -r requirements.txt
python download_data.py
python -m src.pipeline
python -m unittest test_project.py
python make_figures.py
```

Source files are retained without changing their content. If a live endpoint has changed, the downloader rejects the new bytes rather than silently replacing the analysis vintage.

## Outputs

`annual_panel.csv` contains original-row flags, cases, matching-year populations and rates. `source_total_audit.csv` records the independent totals check. `all_predictions.csv` contains every evaluated model/origin/horizon. `selected_models.csv`, `calibration_widths.csv` and `test_evaluation.csv` preserve decisions and results. `future_forecasts.csv` contains the 2026–2028 research outlook. `geographic_profiles.csv` includes raw and smoothed rates, posterior ranges and descriptive profiles. `rate_model_parameters.csv` records prior parameters. `surveillance.sqlite` contains the analytical tables, and `analysis.sql` builds the regional summary.

## Limits

Reported disease is not infection incidence. Mild non-neuroinvasive cases are especially underreported. Residence is not necessarily exposure location, and travel-associated cases can occur. Climate, mosquito surveillance, interventions and reporting changes are not covariates in these models. Annual aggregation cannot give operational weekly outbreak warnings.

Historical data are from the latest downloaded vintage, not archived vintages at each forecast origin. The evaluation is therefore retrospective and chronological, not a real-time surveillance reconstruction. Future rates are not calculated because future population denominators are not modelled. Research outputs should support contextual review, not replace public-health surveillance or clinical judgement.

## Source reuse

CDC-authored material is generally public domain, subject to exceptions for third-party content; see [CDC use of agency materials](https://www.cdc.gov/other/agencymaterials.html). Source attribution is retained. No endorsement is implied. Source policies govern the data; this repository does not relicense agency materials.

