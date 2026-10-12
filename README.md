# Otso: a live research forecast of fine particulate matter

Otso runs every morning on the LUMI supercomputer and forecasts daily PM<sub>2.5</sub> from all its sources over all
land, 12 hours to 5 days ahead, as an ensemble of eight members on a 0.4° grid. It is the coarse version of the model of
the Foehn paper ([ammarkheder.com/Foehn](https://ammarkheder.com/Foehn/), [code](https://github.com/AmmarKheder/Foehn)),
fine-tuned on live inputs, and run on the 00 UTC CAMS analysis, the 00 UTC ECMWF IFS open-data forecast and the GFAS
fires of the previous day, with the FLEXGREEN transport recomputed for each day.

- **The forecast:** <https://ammarkheder.com/Otso/> (a web app that can be installed on a phone; 37 languages).
- **The data:** the [`live`](https://github.com/AmmarKheder/Otso/tree/live) branch holds the last seven days (maps, city
  table, NetCDF, provenance), rewritten every day; `latest.json` lists the available days.
- **The code:** `realtime/` (fetch, build, transport and forecast job, products, publication, daily verification,
  hindcast and fine-tuning). It uses the model code of the [Foehn repository](https://github.com/AmmarKheder/Foehn).
- **The page:** `docs/`, served by GitHub Pages.

Otso is a research forecast. It is not an official product and does not replace the air-quality forecasts and alerts of
national or local authorities. It is not part of the Foehn paper, whose kilometre-scale forecasts are retrospective.

Contains modified Copernicus Atmosphere Monitoring Service information 2026 (CAMS analysis, GFAS); ECMWF open data,
CC BY 4.0; city names from GeoNames (CC BY); map data from OpenStreetMap contributors. Neither the European Commission
nor ECMWF is responsible for any use of this forecast.

Developed by Ammar Kheder, Atmospheric Modelling Centre Lahti (University of Helsinki, LUT University). MIT licence.
If you use Otso, please cite the Foehn paper and name each forecast by its issue date.
