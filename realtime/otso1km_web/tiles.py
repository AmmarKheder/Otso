#!/usr/bin/env python3
"""Otso 1 km web tiles: XYZ Web Mercator PNG tiles of one Otso 1 km day, for the map at ammarkheder.com/Otso/1km/.
Web layer only: the 1 km products (out/<d>/<tag>/*.npz) are read, never changed.

Sources, per pixel (in the palette index, so the page says which one it shows and draws a light texture on the last three):
  0 1 km    out/<d>/<tag>/lead<L>_part<r>.npz (infer.py: 10 x 10 deg tiles of the 0.01 deg LGHAP lattice, north-up, NaN
            outside the LGHAP mask; data from 58 S to 60.0 N), sampled nearest-neighbour at z7 (~1.2 km/px at the equator).
  2 north   land north of 60.0 N (no 1 km truth there, so no 1 km model): Otso's own forecast of the lead day, corrected
            towards GHAP (lead's choice, 2026-10-28): per 0.25 deg land cell and calendar month, the quantile mapping of
            data/processed/global/north_qm_ghap.npz (CAMS day 0 -> GHAP, 2017-2022; tested 60-70 N 2022: RMSE 3.62, R 0.52,
            vs 4.64 for the GHAP climatology and 6.09 for raw CAMS), y = expm1(interp(log1p x, q_cams[m], q_ghap[m])) with x
            the Otso ensemble mean of the member daily means; times lghap_over_ghap_55_60N[m] at 60 N tapering (cosine)
            to 1 at 64 N so that the joint with the 1 km field has no step; then bilinear in log1p to the pixels (land).
            Probability: the same mapping applied to each Otso member, fraction above 15 ug m-3.
  3 interp  holes of the model's LGHAP mask inside the 1 km domain (parts of Bavaria, Czechia, Austria, ...): normalised
            convolution of the surrounding 1 km values (Gaussian-weighted mean of the valid neighbours, in log1p; radius
            grown 2 px, then 8, 16, 32, 64 px on an 8 x 8 block grid, up to ~50 km). Not within 3 px of the sea.
  1 0.4     holes with no 1 km pixel within ~50 km: Otso's own 0.4 deg forecast of the lead day as the 1 km model sees it
            (member daily means, trapezoid 00/12/24 UTC; bilinear in log1p; probability: member fraction, linear).
  Land = Natural Earth 10 m land minus 10 m lakes. Antarctica is not drawn.
Output <out>/<product>/<L>/<z>/<x>/<y>.png for z = 0..zmax(product, lead) (lower zooms: 2 x 2 means, in log1p for PM2.5),
       <out>/tiles.json (encoding, palettes, bitsets of the tiles per product and zoom, sizes, sources) and
       <out>/edge.geojson (the 60 N edge of the 1 km domain over land: dashed on the map).
Encoding: 8-bit paletted PNG, full colours. The index IS the value (the page inflates the PNG and reads it):
  mean   0 none; BASE[s] + c*N[s] + sub; c = class of the paper's bounds [0,5,10,15,25,37.5,50,75,100,150,250, over]
         (0..10), sub = sub-bin (linear in class 0, geometric otherwise, the last class 250..1000); value = bin centre.
  prob15 0 none; PBASE[s] + k, k = round(8 P) members of 8 above 15 ug m-3.
    python tiles.py 2026-10-28 --tag pmA_final_K0T3 --out DIR [--leads 1,2,3,4,5] [--products mean,prob15]
                    [--zmax mean:7,7,6,6,6/prob15:6] [--box x0,x1,y0,y1 (z7 tiles, tests)] [--workers 10]"""
import argparse
import base64
import datetime as dt
import io
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
O1K = HERE.parent
PROJ = O1K.parent
OUT1K = O1K / "out"
RT = Path("/scratch/project_462001804/ammar/eccv/cran-pm/experiments/global1km/realtime")
OTSO_OUT, OTSO_DATA = RT / "out", RT / "data"
STATIC = HERE / "static"
NORTH_QM = PROJ / "data/processed/global/north_qm_ghap.npz"

ZN = 7                                   # native zoom of the 1 km field
NPX = 256 << ZN                          # 32768 px around the world at z7
LGHAP_LAT_S, LGHAP_LON_W, RES = -58.0, -180.0, 0.01      # lattice pixel i spans [-58 + 0.01 i, -58 + 0.01 (i + 1)]
NI, NJ = 12000, 36000
EDGE_N = 60.0                            # last LGHAP data row ends at 60.0 N
TAPER_N = 64.0                           # the LGHAP / GHAP level ratio tapers from 60 N to 1 at 64 N
GRID_LAT0, GRID_RES, GRID_NJ = 84.0, 0.25, 1440                # 0.25 deg store grid: lat 84 - 0.25 row, lon -180 + 0.25 col
GRID_NI = int((GRID_LAT0 - 58.0) / GRID_RES) + 1                # rows 84 .. 58 N
OTSO_LAT0, OTSO_RES, OTSO_NI, OTSO_NJ = 84.0, 0.4, 361, 900   # Otso cell centres: lat 84 - 0.4 i, lon -180 + 0.4 j
LAT_MAX = 85.0511287798
COAST_PX = 3                             # holes are not filled within 3 z7 px of the sea
HOLE_KM = 50.0                           # interpolation radius limit; beyond it Otso 0.4 deg
MG = 192                                 # margin (px) around a block for the hole interpolation

BOUNDS = [0, 5, 10, 15, 25, 37.5, 50, 75, 100, 150, 250]
COLORS = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#fee090", "#fdae61", "#f46d43", "#d73027", "#a50026"]
OVER = "#5c0019"
TOP = 1000.0                             # members are capped at 1000 ug m-3
SRC_1KM, SRC_OTSO, SRC_NORTH, SRC_INTERP = 0, 1, 2, 3
NSRC = 4
N = [8, 3, 6, 6]                         # sub-bins per class for each source
BASE = [1]
for _s in range(1, NSRC):
    BASE.append(BASE[-1] + 11 * N[_s - 1])                       # [1, 89, 122, 188]; last index 253
PBASE = [1, 10, 19, 28]                  # prob15: 1 km, 0.4 deg, north (corrected 0.4 deg), interpolated
PROB_COLORS = ["#f4f1f8", "#dcd5ea", "#c2b6dc", "#a798cc", "#8c7bbb", "#7360a8", "#5c4794", "#46307e", "#2f1a66"]


def hexrgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def class_edges(n):
    """(11, n + 1) sub-bin edges per class"""
    hi = BOUNDS[1:] + [TOP]
    return np.array([np.linspace(a, b, n + 1) if c == 0 else np.geomspace(a, b, n + 1) for c, (a, b) in enumerate(zip(BOUNDS, hi))])


def mean_palette():
    cols = [hexrgb(c) for c in COLORS] + [hexrgb(OVER)]
    pal = [[0, 0, 0]]
    for s in range(NSRC):
        for c in range(11):
            pal += [cols[c]] * N[s]
    return np.array(pal, np.uint8)


def prob_palette():
    cols = [hexrgb(c) for c in PROB_COLORS]
    return np.array([[0, 0, 0]] + cols * 3, np.uint8)


def quant_mean(v, src):
    idx = np.zeros(v.shape, np.uint8)
    ok = np.isfinite(v)
    if not ok.any():
        return idx
    x = np.clip(v[ok].astype(np.float32), 0.0, TOP * 0.999)
    c = np.searchsorted(np.array(BOUNDS[1:], np.float32), x, side="right")           # 0..10
    lo = np.array(BOUNDS, np.float32)[c]
    hi = np.array(BOUNDS[1:] + [TOP], np.float32)[c]
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.where(c == 0, x / 5.0, np.log(np.maximum(x, 1e-6) / np.maximum(lo, 1e-6)) / np.log(hi / np.maximum(lo, 1e-6)))
    s_ = src[ok].astype(np.int64)
    n = np.array(N)[s_]
    base = np.array(BASE)[s_]
    s = np.clip(np.floor(frac * n), 0, n - 1).astype(np.int64)
    idx[ok] = (base + c * n + s).astype(np.uint8)
    return idx


def quant_prob(p, src):
    idx = np.zeros(p.shape, np.uint8)
    ok = np.isfinite(p)
    k = np.clip(np.rint(p[ok].astype(np.float32) * 8), 0, 8).astype(np.int64)
    pb = np.array(PBASE)[src[ok].astype(np.int64)]
    idx[ok] = (pb + k).astype(np.uint8)
    return idx


def decode_mean_index(idx):
    """index -> (value, source), as the page does (self-test)"""
    out = np.full(idx.shape, np.nan, np.float32)
    src = np.full(idx.shape, -1, np.int8)
    for i in np.unique(idx[idx > 0]):
        i = int(i)
        s = max(k for k in range(NSRC) if BASE[k] <= i)
        c, sub = divmod(i - BASE[s], N[s])
        e = class_edges(N[s])
        a, b = e[c, sub], e[c, sub + 1]
        out[idx == i] = (a + b) / 2 if c == 0 else math.sqrt(a * b)
        src[idx == i] = s
    return out, src


# ------------------------------------------------------------------------------------------------ geometry
def lat_of_row(y, n=NPX):
    return np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (np.asarray(y, np.float64) + 0.5) / n))))


def lon_of_col(x, n=NPX):
    return (np.asarray(x, np.float64) + 0.5) / n * 360.0 - 180.0


def row_of_lat(lat, n=NPX):
    s = math.sin(math.radians(lat))
    return (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n


TY0 = int(row_of_lat(OTSO_LAT0 + 0.2) // 256)            # z7 tile rows with data: 84 N .. LGHAP's 58 S
TY1 = int(row_of_lat(LGHAP_LAT_S) // 256) + 1
Y60 = row_of_lat(EDGE_N)


# ------------------------------------------------------------------------------------------------ inputs
def load_mosaic(day, tag, L, product):
    """(12000, 36000) float16, row 0 = northern edge (62 N), NaN outside the LGHAP mask"""
    M = np.full((NI, NJ), np.nan, np.float16)
    d = OUT1K / day / tag
    n = 0
    for r in range(64):
        f = d / f"lead{L}_part{r}.npz"
        if not f.exists():
            break
        with np.load(f) as z:
            for k in z.files:
                if k.startswith(product + "/"):
                    rr, cc = int(k[-5:-3]), int(k[-2:])
                    R0 = (NI - 1000) - 1000 * rr
                    M[R0:R0 + 1000, cc * 1000:(cc + 1) * 1000] = z[k]
                    n += 1
    if n == 0:
        raise SystemExit(f"no {product} tiles for lead {L} in {d}")
    return M


def otso_daily(day, L):
    """Otso's lead day L as prep.build_pm feeds the 1 km model: member daily means (trapezoid 00/12/24 UTC, h = 0 is the
    CAMS analysis); returns their mean and the member fraction above 15 ug m-3 (361, 900), and the member count"""
    pred = np.load(OTSO_OUT / day / "pred.npy", mmap_mode="r")             # (M, 10, 361, 900), 12..120 h
    cams = np.load(OTSO_DATA / day / "cams.npy")[:, 1].astype(np.float32)   # PM2.5 at t0 - 12 h, t0
    M = pred.shape[0]
    inst = lambda h: np.broadcast_to(cams[1], (M,) + cams[1].shape) if h == 0 else np.asarray(pred[:, h // 12 - 1], np.float32)
    a, b, c = 24 * (L - 1), 24 * L - 12, 24 * L
    dm = np.maximum(0.25 * inst(a) + 0.5 * inst(b) + 0.25 * inst(c), 0.0)
    return dm.mean(0), (dm > 15.0).mean(0), M


def otso_sample(field, lat, lon, log=True):
    """bilinear (in log1p if log) of an Otso (361, 900) field at pixel centres lat (ny,), lon (nx,) -> (ny, nx)"""
    F = np.log1p(np.maximum(field, 0)).astype(np.float64) if log else field.astype(np.float64)
    fi = (OTSO_LAT0 - lat) / OTSO_RES
    i0 = np.clip(np.floor(fi).astype(np.int64), 0, OTSO_NI - 2)
    wi = np.clip(fi - i0, 0, 1)
    fj = (lon + 180.0) / OTSO_RES
    j0f = np.floor(fj)
    wj = fj - j0f
    j0 = j0f.astype(np.int64) % OTSO_NJ
    j1 = (j0 + 1) % OTSO_NJ
    top = F[i0][:, j0] * (1 - wj) + F[i0][:, j1] * wj
    bot = F[i0 + 1][:, j0] * (1 - wj) + F[i0 + 1][:, j1] * wj
    v = top * (1 - wi)[:, None] + bot * wi[:, None]
    v[(lat > OTSO_LAT0) | (lat < OTSO_LAT0 - OTSO_RES * (OTSO_NI - 1))] = np.nan
    return np.expm1(v) if log else v


def otso_members_daily(day, L):
    """member daily means of Otso's lead day L (trapezoid 00/12/24 UTC, h = 0 is the CAMS analysis): (M, 361, 900)"""
    pred = np.load(OTSO_OUT / day / "pred.npy", mmap_mode="r")
    cams = np.load(OTSO_DATA / day / "cams.npy")[:, 1].astype(np.float32)
    M = pred.shape[0]
    inst = lambda h: np.broadcast_to(cams[1], (M,) + cams[1].shape) if h == 0 else np.asarray(pred[:, h // 12 - 1], np.float32)
    a, b, c = 24 * (L - 1), 24 * L - 12, 24 * L
    return np.maximum(0.25 * inst(a) + 0.5 * inst(b) + 0.25 * inst(c), 0.0)


def otso_points(field, lat, lon):
    """bilinear in log1p of an Otso (361, 900) field at points (lat, lon) -> ug m-3"""
    F = np.log1p(np.maximum(field, 0)).astype(np.float64)
    fi = (OTSO_LAT0 - lat) / OTSO_RES
    i0 = np.clip(np.floor(fi).astype(np.int64), 0, OTSO_NI - 2)
    wi = np.clip(fi - i0, 0, 1)
    fj = (lon + 180.0) / OTSO_RES
    j0f = np.floor(fj)
    wj = fj - j0f
    j0 = j0f.astype(np.int64) % OTSO_NJ
    j1 = (j0 + 1) % OTSO_NJ
    v = (F[i0, j0] * (1 - wj) + F[i0, j1] * wj) * (1 - wi) + (F[i0 + 1, j0] * (1 - wj) + F[i0 + 1, j1] * wj) * wi
    return np.expm1(v)


def north_grids(day, L, valid_day, qm):
    """north of the 1 km domain: Otso corrected towards GHAP on the 0.25 deg land cells north of 58 N, as two full grids
    (GRID_NI x GRID_NJ) -- log1p of the corrected ensemble-mean daily mean, and the member fraction above 15 ug m-3 --
    with the sea cells given the value of the nearest land cell (so that the bilinear step never mixes in nothing)"""
    from scipy.ndimage import distance_transform_edt
    m = dt.date.fromisoformat(valid_day).month
    qc, qg = qm["q_cams"][m - 1].astype(np.float64), qm["q_ghap"][m - 1].astype(np.float64)      # (99, ncell)
    rows, cols = qm["cell_row"].astype(np.int64), qm["cell_col"].astype(np.int64)
    lat, lon = GRID_LAT0 - GRID_RES * rows, -180.0 + GRID_RES * cols
    t = np.clip((lat - EDGE_N) / (TAPER_N - EDGE_N), 0, 1)
    factor = 1.0 + (float(qm["lghap_over_ghap_55_60N"][m - 1]) - 1.0) * 0.5 * (1 + np.cos(np.pi * t))

    def qmap(x):                                                                      # x (ncell,) ug -> corrected ug
        lx = np.log1p(np.maximum(x, 0))
        k = np.clip((qc <= lx[None, :]).sum(0), 1, qc.shape[0] - 1)                    # np.interp per cell (clamped ends)
        cidx = np.arange(lx.size)
        x0, x1, y0, y1 = qc[k - 1, cidx], qc[k, cidx], qg[k - 1, cidx], qg[k, cidx]
        with np.errstate(invalid="ignore", divide="ignore"):
            w = np.where(x1 > x0, (lx - x0) / (x1 - x0), 0.0)
        y = np.where(lx <= qc[0], qg[0], np.where(lx >= qc[-1], qg[-1], y0 + np.clip(w, 0, 1) * (y1 - y0)))
        return np.expm1(y) * factor
    dm = otso_members_daily(day, L)
    ym = qmap(otso_points(dm.mean(0), lat, lon))
    pm = np.mean([qmap(otso_points(dm[k], lat, lon)) > 15.0 for k in range(dm.shape[0])], axis=0)
    out = []
    for v in (np.log1p(ym), pm):
        G = np.full((GRID_NI, GRID_NJ), np.nan, np.float32)
        ok = (rows < GRID_NI) & np.isfinite(v)
        G[rows[ok], cols[ok]] = v[ok]
        idx = distance_transform_edt(~np.isfinite(G), return_distances=False, return_indices=True)
        out.append(G[idx[0], idx[1]])
    return out


def grid_sample(G, lat, lon):
    """bilinear of a (GRID_NI, GRID_NJ) grid (row 0 = 84 N) at pixel centres lat (ny,), lon (nx,), periodic in lon"""
    fi = (GRID_LAT0 - lat) / GRID_RES
    i0 = np.clip(np.floor(fi).astype(np.int64), 0, GRID_NI - 2)
    wi = np.clip(fi - i0, 0, 1)
    fj = (lon + 180.0) / GRID_RES
    j0f = np.floor(fj)
    wj = fj - j0f
    j0 = j0f.astype(np.int64) % GRID_NJ
    j1 = (j0 + 1) % GRID_NJ
    top = G[i0][:, j0] * (1 - wj) + G[i0][:, j1] * wj
    bot = G[i0 + 1][:, j0] * (1 - wj) + G[i0 + 1][:, j1] * wj
    return top * (1 - wi)[:, None] + bot * wi[:, None]


def land_z7(y0, y1):
    """Natural Earth 10 m land minus 10 m lakes on the z7 pixel rows [y0, y1), uint8 (cached, bit-packed, in static/)"""
    cache = STATIC / f"land_z7_{y0}_{y1}.npy"
    if cache.exists():
        return np.unpackbits(np.load(cache), axis=1)[:, :NPX]
    import shapefile
    from pyproj import Transformer
    from rasterio.features import rasterize
    from rasterio.transform import Affine
    from shapely.geometry import box, shape
    from shapely.ops import transform as stransform
    tr = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    clip = box(-180, -LAT_MAX + 1e-6, 180, LAT_MAX - 1e-6)

    def proj(path):
        out = []
        for s in shapefile.Reader(str(path)).shapes():
            g = shape(s.__geo_interface__).buffer(0).intersection(clip)
            if not g.is_empty:
                out.append(stransform(tr.transform, g))
        return out
    R = 20037508.342789244
    res = 2 * R / NPX
    tf = Affine(res, 0, -R, 0, -res, R - y0 * res)
    shp = (y1 - y0, NPX)
    m = rasterize(((g, 1) for g in proj(STATIC / "ne_10m_land.shp")), out_shape=shp, transform=tf, fill=0, dtype="uint8")
    lk = rasterize(((g, 1) for g in proj(STATIC / "ne_10m_lakes.shp")), out_shape=shp, transform=tf, fill=0, dtype="uint8")
    m[lk == 1] = 0
    np.save(cache, np.packbits(m, axis=1))
    return m


_LAND_PACKED = None


def land_rows(y0, y1):
    """land on z7 rows [y0, y1) (rows outside [0, TY1 * 256) are sea), uint8"""
    global _LAND_PACKED
    if _LAND_PACKED is None:
        land_z7(0, TY1 * 256)
        _LAND_PACKED = np.load(STATIC / f"land_z7_0_{TY1 * 256}.npy", mmap_mode="r")
    out = np.zeros((y1 - y0, NPX), np.uint8)
    a, b = max(y0, 0), min(y1, TY1 * 256)
    if b > a:
        out[a - y0:b - y0] = np.unpackbits(np.asarray(_LAND_PACKED[a:b]), axis=1)[:, :NPX]
    return out


# ------------------------------------------------------------------------------------------------ fields
def sample_1km(M, y0, y1, x0, x1):
    lat = lat_of_row(np.arange(y0, y1))
    lon = lon_of_col(np.arange(x0, x1))
    I = np.floor((lat - LGHAP_LAT_S) / RES).astype(np.int64)
    J = np.clip(np.floor((lon - LGHAP_LON_W) / RES).astype(np.int64), 0, NJ - 1)
    inside = (I >= 0) & (I < NI)
    R = np.where(inside, NI - 1 - I, 0)
    V = np.empty((y1 - y0, x1 - x0), np.float32)
    for a in range(0, y1 - y0, 512):
        V[a:a + 512] = M[R[a:a + 512]][:, J]
    V[~inside] = np.nan
    return V, lat, lon


def fill_holes(V, S, hole, log, px_km):
    """normalised convolution of the valid 1 km pixels of V into hole (bool, same shape), growing radius: 2 px at full
    resolution, then 8, 16, 32, 64 px on 8 x 8 blocks while the radius stays under HOLE_KM; in place (S = SRC_INTERP);
    returns the holes left"""
    from scipy.ndimage import gaussian_filter, map_coordinates
    val = np.isfinite(V) & (S == SRC_1KM)
    X = np.where(val, np.log1p(np.maximum(V, 0)) if log else V, 0).astype(np.float32)
    m = val.astype(np.float32)
    num, den = gaussian_filter(X, 2, truncate=3), gaussian_filter(m, 2, truncate=3)
    put = hole & (den > 0.03)
    with np.errstate(invalid="ignore", divide="ignore"):
        est = num / den
    V[put] = (np.expm1(est[put]) if log else est[put])
    S[put] = SRC_INTERP
    left = hole & ~put
    if not left.any():
        return left
    B = 8
    h, w = X.shape
    hb, wb = h // B, w // B
    Xs = X[:hb * B, :wb * B].reshape(hb, B, wb, B).sum((1, 3))
    ms = m[:hb * B, :wb * B].reshape(hb, B, wb, B).sum((1, 3))
    rr, cc = np.nonzero(left)
    for sc in (1, 2, 4, 8):
        if sc * B * px_km > HOLE_KM * 1.05 or not rr.size:
            break
        n_, d_ = gaussian_filter(Xs, sc, truncate=3), gaussian_filter(ms, sc, truncate=3)
        with np.errstate(invalid="ignore", divide="ignore"):
            e = np.where(d_ > 0.03 * B * B, n_ / d_, np.nan)
        cy, cx = (rr + 0.5) / B - 0.5, (cc + 0.5) / B - 0.5
        v = map_coordinates(np.nan_to_num(e, nan=0.0), [cy, cx], order=1, mode="nearest")
        okc = map_coordinates(np.isfinite(e).astype(np.float32), [cy, cx], order=1, mode="nearest") > 0.999
        if okc.any():
            V[rr[okc], cc[okc]] = np.expm1(v[okc]) if log else v[okc]
            S[rr[okc], cc[okc]] = SRC_INTERP
            rr, cc = rr[~okc], cc[~okc]
    left = np.zeros_like(hole)
    left[rr, cc] = True
    return left


def z7_field(M, otso, north_g, product, y0, y1, x0, x1):
    """values (float32, NaN = none) and source (uint8) on z7 rows [y0, y1), columns [x0, x1); north_g = the north grid
    of this product (log1p PM2.5 or probability)"""
    from scipy.ndimage import binary_dilation
    e0, e1 = max(y0 - MG, 0), y1 + MG                                         # rows with margins for the interpolation
    V, lat, lon = sample_1km(M, e0, e1, x0, x1)
    S = np.zeros(V.shape, np.uint8)
    land = land_rows(e0 - COAST_PX, e1 + COAST_PX)[:, x0:x1].astype(bool)
    lnd = land[COAST_PX:COAST_PX + (e1 - e0)]
    # north of 60 N: Otso corrected towards GHAP (bilinear from the 0.25 deg cells), land only
    north = np.nonzero((lat >= EDGE_N) & (lat <= GRID_LAT0))[0]
    for a in range(0, north.size, 1024):
        rr = north[a:a + 1024]
        g = grid_sample(north_g, lat[rr], lon)
        val = (np.expm1(g) if product == "mean" else g).astype(np.float32)
        put = lnd[rr] & ~np.isfinite(V[rr]) & np.isfinite(val)
        sub, ss = V[rr], S[rr]
        sub[put] = val[put]
        ss[put] = SRC_NORTH
        V[rr], S[rr] = sub, ss
    # holes of the 1 km domain (south of 60 N), away from the sea: interpolated, else Otso 0.4 deg
    south = (lat < EDGE_N) & (lat >= LGHAP_LAT_S)
    if south.any():
        sea = binary_dilation(~land, iterations=COAST_PX)[COAST_PX:COAST_PX + (e1 - e0)]
        hole = lnd & ~sea & ~np.isfinite(V) & south[:, None]
        hole[: y0 - e0] = False                                                   # only the band's own rows are filled
        hole[y1 - e0:] = False
        if hole.any():
            fld = otso[0] if product == "mean" else otso[1]
            CW = 2048
            for c0 in range(0, x1 - x0, CW):
                c1 = min(c0 + CW, x1 - x0)
                if not hole[:, c0:c1].any():
                    continue
                a0, a1 = max(c0 - MG, 0), min(c1 + MG, x1 - x0)
                Vs, Ss, Hs = V[:, a0:a1].copy(), S[:, a0:a1].copy(), np.zeros((e1 - e0, a1 - a0), bool)
                Hs[:, c0 - a0:c1 - a0] = hole[:, c0:c1]
                lat_c = float(lat[(y0 + y1) // 2 - e0])
                px_km = 40075.0 * math.cos(math.radians(lat_c)) / NPX
                left = fill_holes(Vs, Ss, Hs, product == "mean", px_km)
                if left.any():
                    rr, cc = np.nonzero(left)
                    o = otso_sample(fld, lat[np.unique(rr)], lon[a0:a1], log=(product == "mean"))
                    ur = {r: k for k, r in enumerate(np.unique(rr))}
                    ov = o[[ur[r] for r in rr], cc]
                    okv = np.isfinite(ov)
                    Vs[rr[okv], cc[okv]] = ov[okv]
                    Ss[rr[okv], cc[okv]] = SRC_OTSO
                V[:, c0:c1], S[:, c0:c1] = Vs[:, c0 - a0:c1 - a0], Ss[:, c0 - a0:c1 - a0]
    return V[y0 - e0:y1 - e0], S[y0 - e0:y1 - e0]


def downsample(V, S, product):
    """2 x 2: mean of the valid pixels (log1p for PM2.5); source = the most frequent source among them (1 km on ties)"""
    h, w = V.shape
    v = V.reshape(h // 2, 2, w // 2, 2)
    s = S.reshape(h // 2, 2, w // 2, 2)
    ok = np.isfinite(v)
    n = ok.sum((1, 3))
    x = np.log1p(np.where(ok, v, 0)) if product == "mean" else np.where(ok, v, 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = x.sum((1, 3)) / n
    m = np.expm1(m) if product == "mean" else m
    m[n == 0] = np.nan
    cnt = np.stack([((s == k) & ok).sum((1, 3)) for k in range(NSRC)])
    return m.astype(np.float32), np.argmax(cnt, 0).astype(np.uint8)


def encode(idx, pal):
    mx = int(idx.max())
    im = Image.fromarray(idx, mode="P")
    im.putpalette(pal[:mx + 1].reshape(-1).tolist(), rawmode="RGB")
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True, transparency=0)
    return b.getvalue()


def write_level(V, S, z, ty0, tx0, product, outdir, pal, write):
    I = quant_mean(V, S) if product == "mean" else quant_prob(V, S)
    stats = {}
    srcpx = np.bincount(S[I > 0].ravel(), minlength=NSRC) if z == ZN else None
    if not write:
        return stats, srcpx
    for a in range(I.shape[0] // 256):
        for b in range(I.shape[1] // 256):
            t = I[a * 256:(a + 1) * 256, b * 256:(b + 1) * 256]
            if not t.any():
                continue
            x, y = tx0 + b, ty0 + a
            png = encode(np.ascontiguousarray(t), pal)
            p = outdir / str(z) / str(x)
            p.mkdir(parents=True, exist_ok=True)
            (p / f"{y}.png").write_bytes(png)
            stats[(x, y)] = len(png)
    return stats, srcpx


def do_lead(job):
    """one (lead, product): z7 field in bands of 16 tile rows (zooms 7..3 written per band), then zooms 2..0 from the
    z3 rows of all bands. Memory: the 1 km mosaic (0.9 GB) + one band with margins (~3 GB)."""
    day, tag, L, product, out, zmax, box, valid_day, north_file = job
    t0 = time.time()
    BAND = 16                                                                   # z7 tile rows per band (= one z3 tile row)
    ty0, ty1, tx0, tx1 = TY0, TY1, 0, 1 << ZN
    zmin = 0
    if box:
        tx0, tx1, by0, by1 = box
        ty0, ty1 = max(ty0, by0), min(ty1, by1)
        zmin = 3
    al = 1 << (ZN - zmin) if box else BAND
    ty0, tx0 = ty0 // BAND * BAND, tx0 // al * al
    ty1, tx1 = -(-ty1 // BAND) * BAND, -(-tx1 // al) * al
    M = load_mosaic(day, tag, L, product)
    om, op, _ = otso_daily(day, L)
    north_g = np.load(north_file)[0 if product == "mean" else 1]
    pal = mean_palette() if product == "mean" else prob_palette()
    d = Path(out) / product / str(L)
    stats = {z: {} for z in range(zmin, ZN + 1) if z <= zmax}
    srcpx = np.zeros(NSRC, np.int64)
    low_V, low_S = [], []
    for by in range(ty0, ty1, BAND):
        V, S = z7_field(M, (om, op), north_g, product, by * 256, (by + BAND) * 256, tx0 * 256, tx1 * 256)
        for z in range(ZN, 2, -1):
            sh = ZN - z
            st, sp = write_level(V, S, z, by >> sh, tx0 >> sh, product, d, pal, write=(zmin <= z <= zmax))
            if sp is not None:
                srcpx += sp
            if zmin <= z <= zmax:
                stats[z].update(st)
            if z > 3:
                V, S = downsample(V, S, product)
        low_V.append(V)
        low_S.append(S)
    del M
    if zmin == 0:
        V, S = np.concatenate(low_V), np.concatenate(low_S)                     # z3 rows from tile row ty0 >> 4
        for z in range(2, -1, -1):
            if V.shape[0] % 2:
                V = np.concatenate([V, np.full((1,) + V.shape[1:], np.nan, np.float32)])
                S = np.concatenate([S, np.zeros((1,) + S.shape[1:], np.uint8)])
            V, S = downsample(V, S, product)
            pad_rows = (-V.shape[0]) % 256
            Vp = np.concatenate([V, np.full((pad_rows, V.shape[1]), np.nan, np.float32)]) if pad_rows else V
            Sp = np.concatenate([S, np.zeros((pad_rows, S.shape[1]), np.uint8)]) if pad_rows else S
            st, _ = write_level(Vp, Sp, z, ty0 >> (ZN - z), tx0 >> (ZN - z), product, d, pal, write=True)
            stats[z] = st
    n = sum(len(s) for s in stats.values())
    b = sum(sum(s.values()) for s in stats.values())
    print(f"  lead {L} {product}: zmax {zmax}, {n} tiles, {b / 1e6:.1f} MB, z7 px by source (1km, 0.4, north, interp) {srcpx.tolist()}, "
          f"{time.time() - t0:.0f} s", flush=True)
    return L, product, zmax, {z: {f"{x}/{y}": v for (x, y), v in s.items()} for z, s in stats.items()}, srcpx.tolist()


def edge_geojson():
    """the 60 N parallel over land (the northern edge of the 1 km domain), as lon intervals"""
    y = int(Y60)
    row = land_rows(y, y + 1)[0].astype(np.int8)
    d = np.diff(np.concatenate([[0], row, [0]]))
    a, b = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
    lines = [[[round(float(i / NPX * 360 - 180), 3), EDGE_N], [round(float(j / NPX * 360 - 180), 3), EDGE_N]]
             for i, j in zip(a, b) if j - i >= 4]
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "northern edge of the 1 km domain (60 N)"},
                                                       "geometry": {"type": "MultiLineString", "coordinates": lines}}]}


def parse_zmax(spec, products, leads):
    """'mean:7,7,6,6,6/prob15:6' -> {(product, lead): zmax}"""
    zm = {(p, L): ZN for p in products for L in leads}
    for part in spec.split("/") if spec else []:
        p, v = part.split(":")
        vals = [int(x) for x in v.split(",")]
        for k, L in enumerate(leads):
            zm[(p, L)] = vals[min(k, len(vals) - 1)]
    return zm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--tag", default="pmA_final_K0T3")
    ap.add_argument("--out", required=True)
    ap.add_argument("--leads", default="1,2,3,4,5")
    ap.add_argument("--products", default="mean,prob15")
    ap.add_argument("--zmax", default="mean:7,7,6,6,6/prob15:6", help="per product, per lead (last value repeated)")
    ap.add_argument("--box", default=None, help="x0,x1,y0,y1 z7 tile range (tests: zooms 7..3)")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    leads = [int(x) for x in a.leads.split(",")]
    products = a.products.split(",")
    zm = parse_zmax(a.zmax, products, leads)
    box = tuple(map(int, a.box.split(","))) if a.box else None
    run = json.loads((OUT1K / a.date / a.tag / "run.json").read_text())
    valid = {L: run["per_lead_day"][str(L)]["valid"] for L in leads}
    t0 = time.time()
    land_z7(0, TY1 * 256)                                                     # builds the cache once, before the pool
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="o1k_north_"))                          # outside the published tree
    qm = dict(np.load(NORTH_QM))
    nf = {}
    for L in leads:
        nf[L] = tmp / f"north_L{L}.npy"
        np.save(nf[L], np.stack(north_grids(a.date, L, valid[L], qm)))
    del qm
    print(f"north grids (Otso corrected towards GHAP) ready in {time.time() - t0:.0f} s", flush=True)
    jobs = [(a.date, a.tag, L, p, str(out), zm[(p, L)], box, valid[L], str(nf[L])) for L in leads for p in products]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(do_lead, jobs))
    for f in nf.values():
        f.unlink(missing_ok=True)
    tmp.rmdir()
    sizes, bits, layers = {}, {}, {}
    for L, p, zmax, st, srcpx in res:
        sizes.setdefault(p, {})[str(L)] = {"tiles": sum(len(s) for s in st.values()), "bytes": sum(sum(s.values()) for s in st.values()),
                                           "by_zoom": {str(z): [len(s), sum(s.values())] for z, s in st.items()},
                                           "z7_px_by_source": dict(zip(["1km", "otso04", "north", "interp"], srcpx))}
        layers.setdefault(p, {})[str(L)] = {"zmax": zmax, "valid": valid[L]}
        for z, s in st.items():
            n = 1 << z
            b = bits.setdefault(p, {}).setdefault(z, np.zeros(n * n, np.uint8))
            for k in s:
                x, y = map(int, k.split("/"))
                b[y * n + x] = 1
    (out / "edge.geojson").write_text(json.dumps(edge_geojson(), separators=(",", ":")))
    meta = {"date": a.date, "tag": a.tag, "native_zoom": ZN, "leads": leads, "products": products, "layers": layers, "members": 8,
            "encoding": {"version": 4, "bounds": BOUNDS, "colors": COLORS, "over": OVER, "top": TOP, "n": N, "base": BASE,
                         "sources": ["1km", "otso04", "north", "interp"], "prob_colors": PROB_COLORS, "prob_base": PBASE,
                         "mean": "0 none; base[s] + c*n[s] + sub, s = 0 (1 km), 1 (Otso 0.4 deg, holes with no 1 km pixel within 50 km), "
                                 "2 (north of 60 N: Otso 0.4 deg corrected towards GHAP), 3 (holes of the 1 km mask: interpolated from the "
                                 "1 km neighbours); c = class (bounds, 10 = over); sub-bins linear in class 0, geometric otherwise "
                                 "(class 10 up to top); value = bin centre",
                         "prob15": "0 none; prob_base[s] + k, P = k/8, sources as for the mean"},
            "north": {"edge_n": EDGE_N, "taper_to_n": TAPER_N, "file": NORTH_QM.name,
                      "method": "per 0.25 deg land cell and month: y = expm1(interp(log1p(Otso daily mean), q_cams, q_ghap)) x LGHAP/GHAP ratio (cosine taper 60 -> 64 N), bilinear in log1p"},
            "tiles": {p: {str(zz): base64.b64encode(np.packbits(b).tobytes()).decode() for zz, b in sorted(d.items())} for p, d in bits.items()},
            "sizes": sizes, "total_bytes": sum(v["bytes"] for p in sizes.values() for v in p.values()),
            "total_tiles": sum(v["tiles"] for p in sizes.values() for v in p.values()),
            "sources": {"1km": f"Otso 1 km (CD-FFM downscaling of Otso 1.2), run {a.tag}",
                        "interp": "holes of the model's LGHAP mask south of 60 N: normalised convolution of the 1 km values around them (up to ~50 km)",
                        "otso04": "holes with no 1 km value within ~50 km: Otso 1.2 at 0.4 deg (member daily means, bilinear in log1p)",
                        "north": "north of 60 N: Otso 1.2 forecast corrected towards GHAP by per-cell monthly quantile mapping (CAMS -> GHAP, 2017-2022), level joined to the 1 km layer at 60 N (LGHAP/GHAP ratio, cosine taper to 64 N)",
                        "land": "Natural Earth 10 m land minus 10 m lakes (public domain)"},
            "elapsed_s": round(time.time() - t0, 1)}
    (out / "tiles.json").write_text(json.dumps(meta, separators=(",", ":"), default=int))
    print(f"done {meta['total_tiles']} tiles, {meta['total_bytes'] / 1e6:.1f} MB in {meta['elapsed_s']} s", flush=True)


if __name__ == "__main__":
    main()
