#!/usr/bin/env python3
"""Otso 1 km web layer: publish the tiles of one day on the orphan branch `live1km` of github.com/AmmarKheder/Otso
(read by ammarkheder.com/Otso/1km/ through raw.githubusercontent.com). Separate from Otso's `live` branch (0.4 deg,
publish.py), which this script never touches. The branch holds ONE day (the latest) and is rewritten with a single
commit each time (`push --force`), so it does not grow. The commit author is the repository owner, nobody else.
The git work tree is built in a scratch directory (node-local /tmp in the Slurm job: no Lustre inodes).
    python publish1km.py 2026-10-28 --tiles /tmp/x/tiles --work /tmp/x/repo [--dry-run]"""
import argparse
import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

REMOTE = "git@github-otso:AmmarKheder/Otso.git"
BRANCH = "live1km"
AUTHOR = ("AmmarKheder", "ammarkheder@outlook.fr")
DISCLAIMER = ("Research forecast, not an official alert: it does not replace the air-quality forecasts and alerts of your "
              "national or local authorities. / Prévision de recherche, ne remplace pas les alertes officielles.")


def git(work, *args):
    r = subprocess.run(["git", "-c", f"user.name={AUTHOR[0]}", "-c", f"user.email={AUTHOR[1]}", *args], cwd=work,
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:400]}")
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--tiles", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tiles, work = Path(a.tiles), Path(a.work)
    meta = json.loads((tiles / "tiles.json").read_text())
    assert meta["date"] == a.date, (meta["date"], a.date)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    shutil.copytree(tiles, work / a.date)
    latest = {"latest": a.date, "updated": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "tag": meta["tag"],
              "leads": meta["leads"], "valid": {L: v["valid"] for L, v in meta["layers"]["mean"].items()},
              "tiles_json": f"{a.date}/tiles.json", "disclaimer": DISCLAIMER}
    (work / "latest.json").write_text(json.dumps(latest, indent=1))
    (work / "README.md").write_text(
        "# Otso 1 km: map tiles\n\n"
        f"Web map tiles of Otso 1 km (Otso 1.2 at 0.4°, downscaled to 1 km by a generative model trained on the LGHAP v2 "
        f"satellite-station product), issue day {a.date}, lead days J+1..J+5. This branch holds the latest day only and is "
        "rewritten every day (one commit). Page: https://ammarkheder.com/Otso/1km/ . Code: the `main` branch.\n\n"
        "Layout: `<day>/<product>/<lead>/<z>/<x>/<y>.png` (Web Mercator XYZ, 256 px), `<day>/tiles.json` (encoding: the "
        "palette index is the value; sources; existing tiles), `<day>/edge.geojson` (60° N edge of the 1 km domain).\n\n"
        "North of 60° N there is no 1 km forecast: the map shows a boreal climatology there. Land outside the model's "
        "1 km mask south of 60° N shows Otso 0.4°.\n\n" + DISCLAIMER + "\n")
    nfiles = sum(1 for _ in work.rglob("*") if _.is_file())
    size = sum(f.stat().st_size for f in work.rglob("*") if f.is_file())
    print(f"tree: {nfiles} files, {size / 1e6:.1f} MB", flush=True)
    if a.dry_run:
        return
    git(work, "init", "-q")
    git(work, "checkout", "-q", "--orphan", BRANCH)
    git(work, "config", "core.sshCommand", "ssh -o BatchMode=yes")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", f"Otso 1 km tiles {a.date}", "--author", f"{AUTHOR[0]} <{AUTHOR[1]}>")
    git(work, "remote", "add", "origin", REMOTE)
    git(work, "push", "-q", "--force", "origin", f"{BRANCH}:{BRANCH}")
    print(f"published {a.date} on {BRANCH}: {nfiles} files, {size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
