# Otso 1 km: map tiles

Web map tiles of Otso 1 km (Otso 1.2 at 0.4°, downscaled to 1 km by a generative model trained on the GHAP V1 satellite-station product (Wei et al. 2023; land from 60° S to 84° N)), issue day 2026-11-06, lead days J+1..J+5. This branch holds the latest day only and is rewritten every day (one commit). Page: https://ammarkheder.com/Otso/1km/ . Code: the `main` branch.

Layout: `<day>/<product>/<lead>/<z>/<x>/<y>.png` (Web Mercator XYZ, 256 px), `<day>/tiles.json` (encoding: the palette index is the value; sources; existing tiles; `domain`), `<day>/edge.geojson` (northern edge of the 1 km domain when it is not the lattice's; empty for the GHAP lattice).

Permanent ice (Greenland and the other ice caps) and the few land areas outside the model's 1 km mask show Otso 0.4° (interpolated from the 1 km values around when they are within 50 km).

Research forecast, not an official alert: it does not replace the air-quality forecasts and alerts of your national or local authorities. / Prévision de recherche, ne remplace pas les alertes officielles.
