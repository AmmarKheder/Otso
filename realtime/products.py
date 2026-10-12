#!/usr/bin/env python3
"""Otso step 5a: the light products of one forecast, from out/<date>/pred.npy (members, 10, 361, 900) -> out/<date>/pub/
  mean_<lead>h.png, p90_<lead>h.png   data PNGs (900 x 361, 8 bit): PM2.5 on a log scale, 0.1 .. 1000 ug m-3 in 254 steps,
                                      0 = ocean; the page decodes them and draws the map itself (hover values, zoom)
  prob_<lead>h.png                    probability (%) that PM2.5 exceeds 25 ug m-3 (WHO 24 h guideline x 1.7 ~ CAMS "moderate");
                                      255 = ocean
  map_<lead>h.png                     rendered map (ensemble mean, coastlines, colour bar): preview and fallback without JS
  cities.json                         60 large cities: mean, 10/90 % of the members, P(> 25) at every lead (3 x 3 cells)
  otso_<date>.nc                      NetCDF (mean, p10, p50, p90, prob; 0.1 ug m-3 precision), for whoever wants the fields
  index.json                          what the page needs (date, leads, files, inputs, disclaimer)
    python products.py 2026-10-10"""
import datetime as dt
import json
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from PIL import Image

import common as C

PM_COLORS = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090", "#fdae61", "#f46d43", "#d73027", "#a50026"]
PM_BOUNDS = [0, 5, 10, 15, 25, 37.5, 50, 75, 100, 150, 250]
THR = 25.0
VERSION = C.VERSION                                               # Otso 1.1 (paper weights) or 1.2 (fine-tuned on 2026), from realtime/model.json
LOG0, LOG1 = -1.0, 3.0                                           # data PNG: 10^-1 .. 10^3 ug m-3
CITIES = [("Beijing", 39.9, 116.4), ("Shanghai", 31.2, 121.5), ("Delhi", 28.6, 77.2), ("Mumbai", 19.1, 72.9), ("Kolkata", 22.6, 88.4),
          ("Dhaka", 23.8, 90.4), ("Karachi", 24.9, 67.0), ("Lahore", 31.5, 74.3), ("Tehran", 35.7, 51.4), ("Istanbul", 41.0, 29.0),
          ("Cairo", 30.0, 31.2), ("Riyadh", 24.7, 46.7), ("Baghdad", 33.3, 44.4), ("Lagos", 6.5, 3.4), ("Kano", 12.0, 8.5),
          ("Accra", 5.6, -0.2), ("Nairobi", -1.3, 36.8), ("Addis Ababa", 9.0, 38.7), ("Johannesburg", -26.2, 28.0), ("Kinshasa", -4.3, 15.3),
          ("Paris", 48.9, 2.3), ("London", 51.5, -0.1), ("Berlin", 52.5, 13.4), ("Madrid", 40.4, -3.7), ("Rome", 41.9, 12.5),
          ("Milan", 45.5, 9.2), ("Warsaw", 52.2, 21.0), ("Moscow", 55.8, 37.6), ("Athens", 38.0, 23.7), ("Helsinki", 60.2, 24.9),
          ("Bangkok", 13.8, 100.5), ("Jakarta", -6.2, 106.8), ("Hanoi", 21.0, 105.8), ("Manila", 14.6, 121.0), ("Singapore", 1.3, 103.8),
          ("Seoul", 37.6, 127.0), ("Tokyo", 35.7, 139.7), ("Osaka", 34.7, 135.5), ("Taipei", 25.0, 121.6), ("Ulaanbaatar", 47.9, 106.9),
          ("Sydney", -33.9, 151.2), ("Melbourne", -37.8, 145.0), ("New York", 40.7, -74.0), ("Los Angeles", 34.1, -118.2),
          ("Chicago", 41.9, -87.6), ("Houston", 29.8, -95.4), ("Toronto", 43.7, -79.4), ("Vancouver", 49.3, -123.1),
          ("Mexico City", 19.4, -99.1), ("Bogota", 4.7, -74.1), ("Lima", -12.0, -77.0), ("Santiago", -33.5, -70.7),
          ("Sao Paulo", -23.5, -46.6), ("Buenos Aires", -34.6, -58.4), ("Tashkent", 41.3, 69.2), ("Almaty", 43.2, 76.9),
          ("Kathmandu", 27.7, 85.3), ("Hong Kong", 22.3, 114.2), ("Chengdu", 30.6, 104.1), ("Wuhan", 30.6, 114.3)]
DISCLAIMER = (f"Otso {C.VERSION} is a research forecast (Foehn-CAMS, 0.4 degrees, trained on the CAMS analyses of 2017-2022"
              + (", fine-tuned on the live inputs of January-August 2026" if C.VERSION != "1.1" else "") + ", run on live inputs since October 2026). "
              "It is not an official product and does not replace the air-quality forecasts and alerts of your country.")


def cell(lat, lon):
    return int(round((84.0 - lat) / 0.4)), int(round((lon + 180.0) / 0.4)) % 900


PM_OFF, PM_STEPS, PROB_OFF = 8, 247, 10                            # encoding v2: a gap of >= 8 between ocean (0) and the data


def data_png(a, lsm, path, kind):
    """8-bit data PNG. iOS Safari returns canvas pixels with a dithering noise of +-1..2, so ocean (0) and the first data
    value are kept >= 8 apart and the page treats v < 4 as ocean (pm) and v > 250 as ocean (prob)."""
    if kind == "pm":
        v = PM_OFF + np.round(PM_STEPS * (np.log10(np.clip(a, 0.1, 1000.0)) - LOG0) / (LOG1 - LOG0))
        v = np.where(lsm, v, 0)
    else:
        v = np.where(lsm, PROB_OFF + np.round(100.0 * np.clip(a, 0, 1)), 255)
    Image.fromarray(v.astype(np.uint8), "L").save(path, optimize=True)


def rendered_map(a, lsm, path, title):
    import cartopy
    cartopy.config["data_dir"] = "/scratch/project_462001140/ammar/eccv/cran-pm/experiments/figures/cartopy_data"
    import cartopy.crs as ccrs
    cmap = ListedColormap(PM_COLORS[:-1]); cmap.set_over(PM_COLORS[-1]); norm = BoundaryNorm(PM_BOUNDS, cmap.N)
    fig = plt.figure(figsize=(12, 5.6), dpi=110)
    ax = fig.add_axes([0.01, 0.135, 0.98, 0.815], projection=ccrs.PlateCarree()); ax.set_global(); ax.set_extent([-180, 180, -60, 84])
    ax.imshow(np.where(lsm, a, np.nan), cmap=cmap, norm=norm, extent=(-180, 180, -60, 84), transform=ccrs.PlateCarree(), interpolation="nearest")
    ax.coastlines(resolution="110m", linewidth=0.5, color="#333"); ax.spines["geo"].set_visible(False)
    ax.set_title(title, fontsize=11, loc="left", pad=6)
    cax = fig.add_axes([0.30, 0.095, 0.40, 0.022])
    cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal", extend="max")
    cb.set_label("PM$_{2.5}$ (µg m$^{-3}$), ensemble mean", fontsize=9); cb.ax.tick_params(labelsize=8)
    fig.text(0.99, 0.012, f"Otso {VERSION} · research forecast, not an official alert · ammarkheder.com/Otso", ha="right", fontsize=7.5, color="#5b6977")
    fig.savefig(path, dpi=110, facecolor="white"); plt.close(fig)


def main():
    d = C.parse_date(sys.argv[1]); O = C.out_dir(d); P = O / "pub"; P.mkdir(exist_ok=True)
    pred = np.load(O / "pred.npy").astype(np.float32)                                   # (M, 10, 361, 900)
    leads = [12 * k for k in range(1, 11)]
    mean = pred.mean(0); q10, q50, q90 = np.percentile(pred, [10, 50, 90], axis=0); prob = (pred > THR).mean(0)
    lsm = np.load(C.G / "cams_static.npz")["static"][0] > 0.5                           # land-sea mask of the model grid
    files = {"mean": [], "p90": [], "prob": [], "map": []}
    for k, L in enumerate(leads):
        vt = dt.datetime(d.year, d.month, d.day) + dt.timedelta(hours=L)
        data_png(mean[k], lsm, P / f"mean_{L:03d}h.png", "pm"); files["mean"].append(f"mean_{L:03d}h.png")
        data_png(q90[k], lsm, P / f"p90_{L:03d}h.png", "pm"); files["p90"].append(f"p90_{L:03d}h.png")
        data_png(prob[k], lsm, P / f"prob_{L:03d}h.png", "prob"); files["prob"].append(f"prob_{L:03d}h.png")
        rendered_map(mean[k], lsm, P / f"map_{L:03d}h.png", f"Otso {VERSION} PM$_{{2.5}}$ forecast, +{L} h: valid {vt:%a %d %b %Y %H:%M} UTC (issued from the 00 UTC run of {d})")
        files["map"].append(f"map_{L:03d}h.png")
    out = {}
    for name, la, lo in CITIES:
        i, j = cell(la, lo); i0, i1, j0, j1 = max(i - 1, 0), min(i + 2, 361), j - 1, j + 2
        v = pred[:, :, i0:i1, j0:j1].mean((2, 3))                                       # members x leads, 3 x 3 cells
        out[name] = {"lat": la, "lon": lo, "mean": [round(float(x), 1) for x in v.mean(0)],
                     "p10": [round(float(x), 1) for x in np.percentile(v, 10, axis=0)],
                     "p90": [round(float(x), 1) for x in np.percentile(v, 90, axis=0)],
                     "p_above_25": [round(float(x), 2) for x in (v > THR).mean(0)]}
    (P / "cities.json").write_text(json.dumps({"date": str(d), "leads_h": leads, "unit": "ug m-3", "cities": out}, separators=(",", ":")))
    try:
        import xarray as xr
        t0 = np.datetime64(dt.datetime(d.year, d.month, d.day), "h"); vt = np.array([t0 + np.timedelta64(L, "h") for L in leads])
        ds = xr.Dataset({"pm25_mean": (("time", "lat", "lon"), mean), "pm25_p10": (("time", "lat", "lon"), q10),
                         "pm25_p50": (("time", "lat", "lon"), q50), "pm25_p90": (("time", "lat", "lon"), q90),
                         "prob_above_25": (("time", "lat", "lon"), prob)},
                        coords={"time": vt, "lat": 84.0 - 0.4 * np.arange(361), "lon": -180.0 + 0.4 * np.arange(900)},
                        attrs={"title": f"Otso {VERSION} PM2.5 forecast issued from the 00 UTC run of {d}", "model": f"Otso {VERSION} = Foehn-CAMS, 0.4 deg",
                               "members": int(pred.shape[0]), "units": "ug m-3, instantaneous at the valid time", "disclaimer": DISCLAIMER,
                               "source": "https://github.com/AmmarKheder/Otso", "inputs": json.dumps(C.meta(d), default=str)})
        for v in ds.data_vars:
            ds[v].attrs["units"] = "ug m-3" if v.startswith("pm") else "1"
        enc = {v: {"zlib": True, "complevel": 5, "dtype": "float32", "least_significant_digit": 1} for v in ds.data_vars}
        ds.to_netcdf(P / f"otso_{d}.nc", encoding=enc); files["netcdf"] = f"otso_{d}.nc"
    except Exception as e:                                                               # the page does not need it
        print("NetCDF not written:", repr(e)[:200])
    gm = [round(float(np.nanmean(np.where(lsm, mean[k], np.nan))), 2) for k in range(10)]
    idx = {"date": str(d), "issued": f"{d}T00:00Z", "leads_h": leads, "members": int(pred.shape[0]), "threshold": THR,
           "png": {"version": 2, "pm_log10_range": [LOG0, LOG1], "pm_offset": PM_OFF, "pm_steps": PM_STEPS, "prob_offset": PROB_OFF, "ocean": {"pm": 0, "prob": 255}},
           "files": files, "cities": "cities.json", "disclaimer": DISCLAIMER, "model": f"Otso {VERSION} (Foehn-CAMS, 0.4°)", "version": VERSION,
           "inputs": C.meta(d), "land_mean": gm}
    (P / "index.json").write_text(json.dumps(idx, indent=1, default=str))
    sz = sum(f.stat().st_size for f in P.iterdir()) / 1e6
    C.log(d, f"products: {len(files['map'])} leads, {len(out)} cities, netcdf {'yes' if 'netcdf' in files else 'no'}, {sz:.1f} MB")


if __name__ == "__main__":
    main()
