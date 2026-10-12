"""Otso 1.2 release: the page text (name, what changed, the scores of 6-20 September). Usage: python page_to_12.py <index.html>"""
import json, sys
p = sys.argv[1]
with open(p) as f:
    s = f.read()
n0 = len(s)
def rep(old, new, count=1):
    global s
    assert old in s, "MISSING: " + old[:100]
    s = s.replace(old, new, count)
S = json.load(open("/scratch/project_462001140/ammar/eccv/cran-pm/experiments/global1km/realtime/out/scores_otso12.json"))
R = {r["lead_h"]: r for r in S["rows"]}
f1 = lambda x: "–" if x is None else f"{x:.1f}"
tr = "".join(f'<tr><td>+{L} h</td><td><b>{f1(R[L]["v12"]["rmse_land"])}</b></td><td>{f1(R[L]["v11"]["rmse_land"])}</td><td>{f1(R[L]["cams"]["rmse_land"])}</td><td>{f1(R[L]["persistence"]["rmse_land"])}</td></tr>' for L in (12, 24, 48, 72, 96, 120))
new_scores = f'''    <h3 style="margin-top:6px">Otso 1.2: fine-tuned on 2026</h3>
    <p class="sub">Otso 1.2 keeps the network of the paper and learns, for six passes, from the live inputs of January to August 2026 (243 days). Scored on 6–20 September, after its training period (no day in common with its training targets), against the CAMS analysis. RMSE of the ensemble mean over land, µg m⁻³.</p>
    <div class="tablewrap"><table class="ct scores" id="v12-table"><thead><tr><th>Lead</th><th>Otso 1.2</th><th>Otso 1.1</th><th>CAMS forecast</th><th>persistence</th></tr></thead><tbody>{tr}</tbody></table></div>
    <ul class="scores-notes">
      <li><strong>15 to 24 % lower error than Otso 1.1</strong> at every lead, and a probabilistic score (CRPS) 23 to 36 % lower: the members are both closer to the truth and better spread.</li>
      <li><strong>Ahead of the CAMS operational forecast from three days on</strong>: 8 % lower error over land five days ahead (13.4 vs 14.7). The CAMS forecast keeps the lead one day ahead (8.8 vs 10.3), as expected from the system that also produces the analyses used as truth.</li>
      <li>One reason: the CAMS system of 2026 differs from the 2017–2022 analyses the paper's model learnt from; seeing eight months of it was enough. All numbers: <a href="scores_otso12.json">scores_otso12.json</a>.</li>
    </ul>
    <h3 style="margin-top:22px">Otso 1.1: the paper's weights on live inputs</h3>
'''
rep('''    <h2>How good is it? The first scores on live inputs</h2>''', '''    <h2>How good is it?</h2>
''' + new_scores)
rep("<title>Otso 1.1 — live PM2.5 forecast of the Foehn project (beta)</title>", "<title>Otso 1.2 — live PM2.5 forecast of the Foehn project (beta)</title>")
rep('<meta name="description" content="Otso 1.1 runs the 0.4° Foehn model', '<meta name="description" content="Otso 1.2 runs the 0.4° Foehn model')
rep('<meta property="og:title" content="Otso 1.1 — live PM2.5 forecast (beta)" />', '<meta property="og:title" content="Otso 1.2 — live PM2.5 forecast (beta)" />')
rep('<span style="color:var(--muted);font-weight:400">/ Otso 1.1</span>', '<span style="color:var(--muted);font-weight:400">/ Otso 1.2</span>')
rep('<h1 style="margin:0">Otso <span style="font-weight:500;color:var(--blue)">1.1</span></h1>', '<h1 style="margin:0">Otso <span style="font-weight:500;color:var(--blue)">1.2</span></h1>')
rep("<p class=\"lede\">Every morning Otso 1.1 takes", "<p class=\"lede\">Every morning Otso 1.2 takes")
rep("Otso is the coarse (0.4°) model of the\n        <a href=\"../\">Foehn paper</a>, the one evaluated in Aurora's protocol, run on live inputs.", "Otso is the coarse (0.4°) model of the\n        <a href=\"../\">Foehn paper</a>, the one evaluated in Aurora's protocol, fine-tuned on the live inputs of 2026.")
rep("<strong>Research forecast.</strong> <span class=\"long\">Otso 1.1 is an experiment", "<strong>Research forecast.</strong> <span class=\"long\">Otso 1.2 is an experiment")
rep("<h2>What Otso 1.1 is, and is not</h2>", "<h2>What Otso 1.2 is, and is not</h2>")
rep("<li><strong>The coarse Foehn model of the paper, unchanged.</strong> Otso 1.1 is Foehn-CAMS, the 0.4° version trained on the CAMS analyses of 2017–2022 in the protocol of Microsoft's Aurora, with the weights used for the paper's results. Nothing is retrained or tuned for the live run.</li>",
    "<li><strong>The coarse Foehn model of the paper, brought up to date.</strong> Otso 1.2 is Foehn-CAMS, the 0.4° version trained on the CAMS analyses of 2017–2022 in the protocol of Microsoft's Aurora, fine-tuned on the live inputs of January–August 2026, because the CAMS system of 2026 differs from the one it learnt from. Otso 1.1, the paper's weights unchanged, ran on 10 and 11 October 2026.</li>")
rep("Otso is named after the bear of Finnish folklore; the version number counts the releases of the live chain (1.1: city search and the hindcast of the 2026 inputs), not the model, which is the paper's: a thing of the forest, best observed from a distance.",
    "Otso is named after the bear of Finnish folklore. Versions: 1.1, the paper's weights on live inputs; 1.2, fine-tuned on January–August 2026. A thing of the forest, best observed from a distance.")
s = s.replace('document.title = "Otso 1.1 — PM2.5 forecast";', 'document.title = "Otso 1.2 — PM2.5 forecast";').replace("<th>Otso 1.1 · land</th><th>CAMS forecast</th><th>persistence</th><th>cities · Otso</th>", "<th>Otso · land</th><th>CAMS forecast</th><th>persistence</th><th>cities · Otso</th>")
s = s.replace("Otso 1.1 · Foehn project", "Otso 1.2 · Foehn project").replace('"Otso 1.1 · forecast of "', '"Otso 1.2 · forecast of "').replace("<span>Otso 1.1</span>", "<span>Otso 1.2</span>")
with open(p, "w") as f:
    f.write(s)
print("page -> Otso 1.2:", n0, "->", len(s), "| remaining 'Otso 1.1':", s.count("Otso 1.1"))
