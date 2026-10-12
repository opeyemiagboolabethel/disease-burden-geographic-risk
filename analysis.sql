SELECT type, region, COUNT(*) AS geographic_units,
       SUM(cases) AS reported_cases, SUM(population) AS population,
       100000.0 * SUM(cases) / SUM(population) AS reported_rate_100k,
       SUM(CASE WHEN above_forecast_band = 1 THEN 1 ELSE 0 END) AS above_band_units
FROM geographic_profiles
GROUP BY type, region
ORDER BY type, reported_rate_100k DESC;
