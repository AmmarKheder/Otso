# Otso 1 km: map tiles

Web map tiles of Otso 1 km (Otso 1.2 at 0.4°, downscaled to 1 km by a generative model trained on the LGHAP v2 satellite-station product), issue day 2026-10-31, lead days J+1..J+5. This branch holds the latest day only and is rewritten every day (one commit). Page: https://ammarkheder.com/Otso/1km/ . Code: the `main` branch.

Layout: `<day>/<product>/<lead>/<z>/<x>/<y>.png` (Web Mercator XYZ, 256 px), `<day>/tiles.json` (encoding: the palette index is the value; sources; existing tiles), `<day>/edge.geojson` (60° N edge of the 1 km domain).

North of 60° N there is no 1 km forecast: the map shows a boreal climatology there. Land outside the model's 1 km mask south of 60° N shows Otso 0.4°.

Research forecast, not an official alert: it does not replace the air-quality forecasts and alerts of your national or local authorities. / Prévision de recherche, ne remplace pas les alertes officielles.
