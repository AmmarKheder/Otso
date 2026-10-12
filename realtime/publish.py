#!/usr/bin/env python3
"""Otso step 5c: publish out/<date>/pub/ on the `live` branch of github.com/AmmarKheder/Otso (read by the page
ammarkheder.com/Otso/ through raw.githubusercontent.com). The branch is an orphan rewritten every day with a single
commit that holds the last 7 days, so the repository does not grow: `git push --force`. The commit author is the owner of
the repository; nobody else is credited. The clone lives in LIVE (created on the first run).
    python publish.py 2026-10-10 [--keep 7] [--dry-run]"""
import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys

import common as C

LIVE = C.RT.parent.parent.parent.parent / "otso_live"                    # .../eccv/otso_live
REMOTE = "git@github-otso:AmmarKheder/Otso.git"
AUTHOR = "AmmarKheder <ammarkheder@outlook.fr>"


def git(*args, ok=False):
    r = subprocess.run(["git", *args], cwd=LIVE, capture_output=True, text=True)
    if r.returncode and not ok:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:400]}")
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("date"); ap.add_argument("--keep", type=int, default=7); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(); d = C.parse_date(a.date); src = C.out_dir(d) / "pub"
    assert (src / "index.json").exists(), f"no products in {src}: run products.py first"
    if not (LIVE / ".git").exists():
        LIVE.mkdir(parents=True, exist_ok=True); git("init", "-q"); git("remote", "add", "origin", REMOTE)
        git("config", "user.name", AUTHOR.split(" <")[0]); git("config", "user.email", AUTHOR.split("<")[1][:-1])
        git("config", "core.sshCommand", "ssh -o BatchMode=yes")
    for f in LIVE.iterdir():                                                           # the tree is rebuilt from scratch each day
        if f.name not in (".git",):
            shutil.rmtree(f) if f.is_dir() else f.unlink()
    days = sorted(p.name for p in C.OUT.iterdir() if (p / "pub" / "index.json").exists())[-a.keep:]
    latest = days[-1]
    if (C.RT / "verif" / "scores_live.json").exists():                                  # the daily verification (verify.py)
        shutil.copy(C.RT / "verif" / "scores_live.json", LIVE / "scores_live.json")
    for day in days:                                                                  # the NetCDF (13 MB) only for the latest day
        shutil.copytree(C.OUT / day / "pub", LIVE / day, ignore=None if day == latest else shutil.ignore_patterns("*.nc"))
        if day != latest:
            ix = json.loads((LIVE / day / "index.json").read_text()); ix["files"].pop("netcdf", None)
            (LIVE / day / "index.json").write_text(json.dumps(ix, indent=1, default=str))
    idx = json.loads((LIVE / latest / "index.json").read_text())
    (LIVE / "latest.json").write_text(json.dumps({"latest": latest, "days": days, "updated": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"),
                                                   "leads_h": idx["leads_h"], "disclaimer": idx["disclaimer"]}, indent=1))
    (LIVE / "README.md").write_text(f"# Otso live forecasts\n\nDaily PM2.5 forecasts of Otso (Foehn-CAMS, 0.4°), 12 h to 120 h ahead, the last {a.keep} days. "
                                    f"This branch is rewritten every day (one commit). Page: https://ammarkheder.com/Otso/ . Code: the `main` branch of this repository.\n\n"
                                    f"{idx['disclaimer']}\n")
    if a.dry_run:
        print("would publish", days, "size", sum(f.stat().st_size for f in LIVE.rglob("*") if f.is_file() and ".git" not in f.parts) / 1e6, "MB"); return
    git("checkout", "-q", "--orphan", "tmp_live", ok=True); git("add", "-A")
    git("-c", f"user.name={AUTHOR.split(' <')[0]}", "-c", f"user.email={AUTHOR.split('<')[1][:-1]}", "commit", "-q", "-m", f"Otso {latest}: forecasts of {days[0]} to {latest}", "--author", AUTHOR)
    git("branch", "-M", "live"); git("push", "-q", "--force", "origin", "live")
    C.log(d, f"published {len(days)} days ({days[0]} .. {latest}) on the live branch")
    print("published", days)


if __name__ == "__main__":
    main()
