#!/usr/bin/env python3
"""Static site generator. Reads ONLY ../report/tools_data.py, ../report/build.py (data section + DD),
../runs/*, ../data/gh_snapshot.json and ../matrix.csv. Writes HTML into this folder."""
import os, sys, json, csv, html, re
HERE = os.path.dirname(os.path.abspath(__file__)); BENCH = os.path.dirname(HERE); REP = BENCH + "/report"
sys.path.insert(0, REP); os.chdir(REP)
src = open(REP + "/build.py").read()
data_part = src.split("# ---------- SVG helpers")[0]
dd_part = src[src.index("DD = {"):src.index("shots = {")]
ns = {"__file__": REP + "/build.py"}
exec(data_part, ns); exec(dd_part, ns)
T, SCORED, CRITERIA, SCORES, WHY, score, ranked = ns["T"], ns["SCORED"], ns["CRITERIA"], ns["SCORES"], ns["WHY"], ns["score"], ns["ranked"]
DD, gui, lane, PROFILES, t3probe = ns["DD"], ns["gui"], ns["lane"], ns["PROFILES"], ns["t3"]
SOURCES, SECONDARY = ns["SOURCES"], ns["SECONDARY_MENTIONS"]
orca_ready = ns["orca_ready"]; lb = ns["lb"]; n_rate, n_large, n_schema = ns["n_rate"], ns["n_large"], ns["n_schema"]
base = ns["base"]
matrix = {r["Tool"]: r for r in csv.DictReader(open(BENCH + "/matrix.csv"))}
esc = html.escape
GUIKEY = {"orca":"orca","synara":"synara","superset":"superset","emdash":"emdash","paseo":"paseo","openchamber":"openchamber","cloudroom":"cloudroom-gui","mux":"mux"}
STATUS = {i: ("Driven end-to-end" if i in ("orca","cs") else "Installed or launched" if i in ("t3","synara","superset","emdash","paseo","vk","openchamber","mux","cloudroom") else "Not testable here") for i in SCORED}
SHORT = {"mux": "Mux / Xum"}
U = "unknown"

def srcs_for(t):
    keys = [t["name"].split(" ")[0].lower()]
    if t.get("repo") and "/" in t["repo"]: keys.append(t["repo"].split(" ")[0].lower())
    if t["id"] == "cloudroom": keys.append("ondrej")
    if t["id"] == "cs": keys.append("claude squad")
    out = []
    for lab, url in SOURCES:
        s = (lab + " " + url).lower()
        if any(k in s for k in keys): out.append((lab, url))
    return out

# ---------- data blob for JS ----------
tools = []
for rank, i in enumerate(ranked, 1):
    t = T[i]; s, cov = score(i); m = matrix.get(t["name"], {})
    g = gui.get(GUIKEY.get(i, ""), None)
    tools.append(dict(id=i, rank=rank, name=t["name"], short=SHORT.get(i, t["name"]), maker=t["maker"], url=t["url"], repo=t["repo"] or "", license=t["license"],
        price=t["price"], status=STATUS[i], score=s, coverage=cov, crit={k: SCORES[i][k] for k, *_ in CRITERIA},
        stars=m.get("GitHub stars", ""), issues=m.get("Open issues+PRs", ""), release=m.get("Latest release", ""), release_date=(m.get("Latest release date (UTC)", "") or "")[:10],
        why=WHY[i], who=DD[i][0], pros=DD[i][1], cons=DD[i][2],
        first_window=(g or {}).get("first_window_s"), rss=(g or {}).get("rss_mb_tree"),
        facts={k: t[k] for k in ("platforms","agents","parallel","isolation","review","remote","mcp","cost","models","setup")},
        hands_on=t["hands_on"], bugs=t["bugs"], notes=t["notes"]))
TJ = {x["id"]: x for x in tools}
crit = [dict(k=k, label=l, w=w, five=f) for k, l, w, f in CRITERIA]
bench = dict(tools=tools, criteria=crit, profiles={k: v for k, v in PROFILES.items()})
open(HERE + "/assets/data.js", "w").write("window.BENCH=" + json.dumps(bench, separators=(",", ":")) + ";\n")
json.dump(bench, open(HERE + "/assets/data.json", "w"), indent=1)

# ---------- layout ----------
NAV = [("index.html","Home"),("leaderboard.html","Leaderboard"),("compare.html","Compare"),("methodology.html","Methodology"),("about.html","About / FAQ")]
def page(fname, title, desc, body, depth=0, active=""):
    r = "../" * depth
    nav = "".join(f'<a href="{r}{h}"' + (' aria-current="page"' if h == active else "") + f'>{esc(l)}</a>' for h, l in NAV)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="dark"><meta name="theme-color" content="#0b0b0c">
<link rel="preload" href="{r}assets/fonts/HostGrotesk.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="{r}assets/vendor/dither-kit.css"><link rel="stylesheet" href="{r}assets/style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' fill='%230b0b0c'/%3E%3Cpath d='M3 3h2v2H3zM7 7h2v2H7zM11 11h2v2h-2zM11 3h2v2h-2zM3 11h2v2H3z' fill='%23e9e9e6'/%3E%3C/svg%3E">
</head><body>
<a class="skip" href="#main">Skip to content</a>
<div class="rails" aria-hidden="true"></div>
<header class="top"><div class="wrap topin">
<a class="logo" href="{r}index.html"><span class="mark" aria-hidden="true"></span>Harness Bench</a>
<button class="mb o navtoggle" aria-expanded="false" aria-controls="nav">Menu</button>
<nav id="nav" aria-label="Primary">{nav}</nav></div></header>
<main id="main">{body}</main>
<footer class="foot"><div class="hatch" aria-hidden="true"></div><div class="wrap footin">
<div><span class="lab">Harness Bench / 2026-10-19</span><p>Agent orchestrators for coding agents. Scores are editorial judgement from docs, repos and feature testing on one Linux box. No real-model task runs were scored.</p></div>
<div class="footnav">{nav}</div></div></footer>
<script src="{r}assets/vendor/dither-kit-lite.js" defer></script><script src="{r}assets/data.js" defer></script><script src="{r}assets/app.js" defer></script>
</body></html>"""

def sec(label, title, inner, cls="", id_=""):
    return (f'<section class="sec {cls}"' + (f' id="{id_}"' if id_ else "") + f'><div class="wrap"><div class="sechead"><span class="lab">{esc(label)}</span>'
            + (f'<h2>{title}</h2>' if title else "") + f'</div>{inner}</div><i class="x xl" aria-hidden="true"></i><i class="x xr" aria-hidden="true"></i></section>')
def band(): return '<div class="hatch" aria-hidden="true"></div>'
def cv(v): return "·" if v is None else str(v)
def bars_attr(rows, hl=1):
    return esc(json.dumps([{"label": r[0], "value": r[1], "hl": i < hl} for i, r in enumerate(rows)]))
def write(path, s):
    assert "\u2014" not in s, path + " contains an em dash"
    p = HERE + "/" + path; os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(s)

# ---------- HOME ----------
top3 = tools[:3]
podium = "".join(f"""<a class="pod" href="tools/{t['id']}.html"><span class="lab">#{t['rank']} / {esc(t['status'])}</span>
<span class="podn">{esc(t['name'])}</span><span class="pods"><b>{t['score']:.0f}</b><small>/100</small></span>
<span class="meter" data-meter="{t['score']}" data-max="100" data-hl="{1 if t['rank']==1 else 0}" role="img" aria-label="{esc(t['name'])} scores {t['score']} of 100"></span>
<span class="podw">{esc(t['why'])}</span></a>""" for t in top3)
cs_runs = lane["Claude Squad"]; or_runs = lane["Orca (orca serve CLI)"]
orv = sum(r["verified"] for r in or_runs); csv_ = sum(r["verified"] for r in cs_runs)
kpis = [("Tools in landscape", str(len(T))), ("Scored on rubric", str(len(SCORED))), ("Driven end-to-end", "2"), ("Stub tasks verified, Orca", f"{orv}/{len(or_runs)*6}"), ("Real-model passes", f"{sum(1 for x in lb if x['ok'])}/{len(lb)}")]
kp = "".join(f'<div class="kpi"><span class="lab">{esc(a)}</span><b>{esc(b)}</b></div>' for a, b in kpis)
take = [
 ("Orca leads at 93", "The only GUI orchestrator we drove end-to-end on Linux, headless via orca serve. 6 worktree-isolated stub agents launched in 1.52 to 1.90 s; 18/18 verified over 3 runs; about 1.1 GB peak RSS."),
 ("T3 Code is close at 90", "Richest documented feature set (cross-provider delegate_task, an MCP for agents, PR flow, mobile). Its server booted headless in 1.01 s, but we ran no agent session through it."),
 ("Synara third at 79", "Similar breadth to T3 Code with an agent gateway and a built-in browser. Self-described early-stage, and 2.1 GB at idle in our launch probe."),
 ("Cloudroom scores 72", "David Ondrej's tool. A distinct cloud-teleport model under Apache-2.0. The GUI launched in 3.3 s; the core needs root on a fresh VM, so it was not installed. Review flow unverified."),
 ("Claude Squad is the light one", "Also 18/18 on the stub lane at about 100 MB peak RSS, and sessions came back paused and resumable after we killed tmux."),
 ("No real-model scores", "No Claude, Codex, Cursor or Grok CLI was logged in. 0 of 9 opencode attempts on a Groq free tier passed, so task success is not part of any score."),
]
tk = "".join(f'<li><span class="lab">{n:02d}</span><h3>{esc(a)}</h3><p>{esc(b)}</p></li>' for n, (a, b) in enumerate(take, 1))
home = f"""<section class="hero"><div class="dots" aria-hidden="true"></div><div class="wrap heroin">
<div class="herotext"><span class="lab">Benchmark / agent orchestrators and harnesses / 2026-10-19</span>
<h1>Which agent orchestrator should run your coding agents?</h1>
<p class="lede">We scored {len(SCORED)} orchestrators for Claude Code, Codex and friends on a 9-part rubric, from vendor docs, repos and hands-on feature testing on a Linux box. Two were driven end-to-end with a stub agent. No model-quality numbers: nothing here was run against a logged-in agent CLI.</p>
<div class="cta"><a class="mb" href="leaderboard.html">See the leaderboard</a><a class="mb o" href="methodology.html">Read the method</a></div></div>
<figure class="heroart"><canvas id="heroArt" aria-hidden="true"></canvas><figcaption class="lab">6 parallel worktrees: 5 clean merges, 1 designed conflict (t5b). Ordered Bayer dither.</figcaption></figure>
</div><i class="x xl" aria-hidden="true"></i><i class="x xr" aria-hidden="true"></i></section>
{band()}
{sec("Leaderboard / top 3", "The podium", f'<div class="podium">{podium}</div><div class="kpis">{kp}</div>')}
{band()}
{sec("All scores", "Weighted score out of 100", f'<div class="chart dk-theme-dark" data-bars="{bars_attr([(t["short"], t["score"]) for t in tools], 1)}" style="--h:{len(tools)*30+30}px" role="img" aria-label="Bar chart of weighted scores; full numbers in the leaderboard table"></div><p class="cap">Dithered bars rendered with DitherKit. Highlighted: the leader. <a href="leaderboard.html">Sortable table with every criterion</a>.</p>')}
{band()}
{sec("Key takeaways", "What the data says", f'<ol class="takes">{tk}</ol>')}
{band()}
{sec("Category matrix", "Where each tool earns its points", '<div class="heat" data-heat role="table" aria-label="Scores by criterion, 0 to 5"></div><p class="cap">Each cell is a 0 to 5 judgement; denser dither means a higher score. Hatched cells had no evidence and count as a neutral 2.5.</p>')}
"""
write("index.html", page("index.html", "Harness Bench: agent orchestrators for coding agents, scored", "A docs- and feature-testing benchmark of agent orchestrators: Orca 93, T3 Code 90, Synara 79.", home, 0, "index.html"))

# ---------- LEADERBOARD ----------
ck = [c["k"] for c in crit]
head = "".join(f'<th scope="col" aria-sort="none"><button data-k="{k}" data-type="{ty}">{esc(lab)}</button></th>' for k, lab, ty in
    [("rank","#","n"),("name","Tool","s")] + [(c["k"], c["k"], "n") for c in crit] + [("score","Score","n"),("coverage","Coverage","n"),("stars","Stars","n"),("status","Hands-on","s")])
rows = ""
for t in tools:
    rows += (f'<tr data-rank="{t["rank"]}" data-name="{esc(t["name"])}" data-score="{t["score"]}" data-coverage="{t["coverage"]}" data-stars="{t["stars"] or -1}" data-status="{esc(t["status"])}" '
        + " ".join(f'data-{k.lower()}="{-1 if t["crit"][k] is None else t["crit"][k]}"' for k in ck) + ">"
        + f'<td class="num">{t["rank"]}</td><th scope="row"><a href="tools/{t["id"]}.html">{esc(t["name"])}</a></th>'
        + "".join(f'<td class="num c{cv(t["crit"][k])}">{cv(t["crit"][k])}</td>' for k in ck)
        + f'<td class="num sc">{t["score"]:.1f}</td><td class="num">{t["coverage"]}%</td><td class="num">{esc(t["stars"] or "-")}</td><td><span class="tag {"ok" if t["status"].startswith("Driven") else "no" if t["status"].startswith("Not") else ""}">{esc(t["status"])}</span></td></tr>')
legend = "".join(f'<li><b>{c["k"]}</b> {esc(c["label"])} <span class="lab">w{c["w"]}</span></li>' for c in crit)
unscored = [x for x in T.values() if x["id"] not in SCORED]
ul = "".join(f'<tr><th scope="row">{esc(x["name"])}</th><td>{esc(x["group"])}</td><td>{esc(x["license"])}</td><td>{esc(x["hands_on"])}</td></tr>' for x in unscored)
prof = ""
for pn, pw in PROFILES.items():
    order = sorted(SCORED, key=lambda i: -score(i, pw)[0])[:5]
    prof += f'<tr><th scope="row">{esc(pn)}</th><td>' + ", ".join(f'{esc(T[i]["name"])} ({score(i, pw)[0]})' for i in order) + "</td></tr>"
lbody = f"""<section class="phead"><div class="wrap"><span class="lab">Leaderboard</span><h1>{len(SCORED)} orchestrators, one rubric</h1>
<p class="lede">Weighted score out of 100. Click a column to sort. A dot means no evidence for that criterion (scored as a neutral 2.5); coverage shows how much of the weight a score rests on.</p></div></section>
{band()}
{sec("Scores", "", f'<div class="chart dk-theme-dark" data-bars="{bars_attr([(t["short"], t["score"]) for t in tools], 1)}" style="--h:{len(tools)*30+30}px" role="img" aria-label="Bar chart of weighted scores"></div>')}
{band()}
{sec("Full table", "Every criterion", f'<div class="tablewrap" tabindex="0" role="region" aria-label="Sortable leaderboard table"><table class="lb" id="lb"><caption class="sr">Leaderboard, sortable by column</caption><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div><ul class="legend">{legend}</ul>')}
{band()}
{sec("Sensitivity", "Does the ranking survive other weightings?", f'<div class="tablewrap"><table><thead><tr><th scope="col">Weight profile</th><th scope="col">Top 5 (score)</th></tr></thead><tbody>{prof}</tbody></table></div><p class="cap">Solo terminal hacker: friction 20, openness 15, review 8, reach 3. Team shipping PRs: review 30, maturity 20. Remote / phone-first: reach 30, friction 5. Unlisted criteria keep the default weight.</p>')}
{band()}
{sec("Landscape, not scored", f"{len(unscored)} more tools we checked", f'<div class="tablewrap"><table><thead><tr><th scope="col">Tool</th><th scope="col">Category</th><th scope="col">License</th><th scope="col">Why no score</th></tr></thead><tbody>{ul}</tbody></table></div>')}
"""
write("leaderboard.html", page("leaderboard.html", "Leaderboard / Harness Bench", "Sortable scores for 13 agent orchestrators.", lbody, 0, "leaderboard.html"))

# ---------- TOOL PAGES ----------
FL = [("platforms","Platforms"),("agents","Supported agents"),("parallel","Parallelism"),("isolation","Isolation"),("review","Review, merge, PR"),("remote","Remote, cloud, mobile"),("mcp","MCP"),("cost","Cost visibility"),("models","Model choice"),("setup","Setup")]
for t in tools:
    i = t["id"]; raw = T[i]
    crow = "".join(f'<li><span class="ck">{c["k"]}</span><span class="cl">{esc(c["label"])}<small>weight {c["w"]}</small></span><span class="meter" data-meter="{t["crit"][c["k"]] if t["crit"][c["k"]] is not None else 0}" data-max="5" data-none="{1 if t["crit"][c["k"]] is None else 0}" role="img" aria-label="{esc(c["label"])}: {cv(t["crit"][c["k"]])} of 5"></span><b class="cv">{cv(t["crit"][c["k"]])}</b></li>' for c in crit)
    facts = "".join(f'<div><dt>{esc(l)}</dt><dd{" class=unk" if t["facts"][k]==U else ""}>{esc(t["facts"][k])}</dd></div>' for k, l in FL)
    ev = [("Hands-on (this box)", t["hands_on"])]
    if t["first_window"] is not None: ev.append(("Launch probe", f'First window {t["first_window"]} s, process-tree RSS {t["rss"]} MB on Xvfb.'))
    if i == "t3": ev.append(("Server probe", "Headless server port open in 1.01 s, 394 MB idle."))
    if i == "orca":
        ev.append(("Lane A, 3 runs", f'All 6 sessions launched in {min(r["launch"] for r in or_runs):.2f} to {max(r["launch"] for r in or_runs):.2f} s; {orv}/18 verified; peak RSS {min(r["rss"] for r in or_runs):.0f} to {max(r["rss"] for r in or_runs):.0f} MB; orca serve ready in 2.79 to 3.06 s.'))
    if i == "cs":
        ev.append(("Lane A, 3 runs", f'All 6 sessions created in {min(r["launch"] for r in cs_runs):.2f} to {max(r["launch"] for r in cs_runs):.2f} s (includes about 1.1 s per session of driver keystroke delays); {csv_}/18 verified; peak RSS {min(r["rss"] for r in cs_runs):.0f} to {max(r["rss"] for r in cs_runs):.0f} MB.'))
    if i in ("orca", "cs"): ev.append(("Crash and merge", "SIGKILL on one session: the other 5 stayed verified and partial work was preserved. Git merges: 5/6 clean, with t5b conflicting in shelf/config.py as designed."))
    if t["bugs"] != U: ev.append(("Known issues", t["bugs"]))
    if t["notes"]: ev.append(("Notes", t["notes"]))
    evh = "".join(f'<div><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>' for a, b in ev)
    sl = "".join(f'<li><a href="{esc(u)}" rel="noopener">{esc(l)}</a></li>' for l, u in srcs_for(raw))
    shot = f'<figure class="shot"><img src="../assets/img/{GUIKEY[i]}.jpg" alt="Screenshot of {esc(t["name"])} first window on Linux (Xvfb launch probe)" width="640" height="400"><figcaption class="lab">First window, Xvfb launch probe</figcaption></figure>' if i in GUIKEY else ""
    idx = ranked.index(i); prev_ = T[ranked[idx-1]] if idx else None; next_ = T[ranked[idx+1]] if idx+1 < len(ranked) else None
    pn = '<nav class="pn" aria-label="Other tools">' + (f'<a class="mb o" href="{prev_["id"]}.html">Prev: {esc(prev_["name"])}</a>' if prev_ else "<span></span>") + (f'<a class="mb o" href="{next_["id"]}.html">Next: {esc(next_["name"])}</a>' if next_ else "") + "</nav>"
    meta = [("Maker", t["maker"]), ("License", t["license"]), ("Pricing", t["price"]), ("Stars", t["stars"] or "-"), ("Open issues+PRs", t["issues"] or "-"), ("Latest release", (t["release"] + " " + t["release_date"]).strip() or "-")]
    mh = "".join(f'<div><dt class="lab">{esc(a)}</dt><dd>{esc(b)}</dd></div>' for a, b in meta)
    body = f"""<section class="phead"><div class="wrap toolhead"><div><span class="lab"><a href="../leaderboard.html">Leaderboard</a> / #{t['rank']} of {len(tools)} / <span class="tag {'ok' if t['status'].startswith('Driven') else 'no' if t['status'].startswith('Not') else ''}">{esc(t['status'])}</span></span>
<h1>{esc(t['name'])}</h1><p class="lede">{esc(t['who'])}</p>
<p class="links"><a class="mb o" href="{esc(t['url'])}" rel="noopener">Website</a>{f'<a class="mb o" href="https://github.com/{esc(t["repo"].split(" ")[0])}" rel="noopener">Repo</a>' if "/" in t["repo"] else ""}<a class="mb" href="../compare.html?a={i}&amp;b={ranked[0] if i != ranked[0] else ranked[1]}">Compare</a></p></div>
<div class="bigscore"><span class="lab">Weighted score</span><b>{t['score']:.1f}</b><span class="lab">coverage {t['coverage']}%</span><span class="meter" data-meter="{t['score']}" data-max="100" data-hl="1" role="img" aria-label="{t['score']} of 100"></span></div></div>
<div class="wrap"><dl class="meta">{mh}</dl></div></section>
{band()}
{sec("Scores by category", "Rubric breakdown", f'<div class="split"><ul class="crit">{crow}</ul><figure class="radarfig"><canvas class="radar" data-radar="{i}" role="img" aria-label="Radar chart of {esc(t["name"])} scores by criterion"></canvas><figcaption class="cap">{esc(t["why"])}</figcaption></figure></div>')}
{band()}
{sec("Verdict", "Strengths and weaknesses", '<div class="pc"><div><h3 class="lab">Strengths</h3><ul>' + "".join(f"<li>{esc(x)}</li>" for x in t["pros"]) + '</ul></div><div><h3 class="lab">Weaknesses</h3><ul>' + "".join(f"<li>{esc(x)}</li>" for x in t["cons"]) + '</ul></div></div>')}
{band()}
{sec("Evidence", "What we saw and where it came from", f'<div class="split"><dl class="ev">{evh}</dl>{shot}</div>' + (f'<h3 class="lab srch">Sources</h3><ul class="srcs">{sl}</ul>' if sl else ""))}
{band()}
{sec("Feature facts", "From docs, repos and our probes", f'<dl class="facts">{facts}</dl><p class="cap">"unknown" means we found no source and did not guess.</p>{pn}')}
"""
    write(f"tools/{i}.html", page(f"tools/{i}.html", f"{t['name']} / Harness Bench", f"{t['name']} scored {t['score']} of 100.", body, 1, ""))

# ---------- COMPARE ----------
opts = "".join(f'<option value="{t["id"]}">{esc(t["name"])} ({t["score"]:.0f})</option>' for t in tools)
cbody = f"""<section class="phead"><div class="wrap"><span class="lab">Compare</span><h1>Two tools, side by side</h1>
<p class="lede">Pick any two scored tools. The link updates so you can share the pairing.</p>
<form class="pick" onsubmit="return false"><label><span class="lab">Tool A</span><select id="ca">{opts}</select></label><span class="vs lab" aria-hidden="true">vs</span><label><span class="lab">Tool B</span><select id="cb">{opts}</select></label><button class="mb o" id="swap" type="button">Swap</button></form></div></section>
{band()}
{sec("Shape", "Rubric overlay", '<div class="split"><figure class="radarfig"><canvas class="radar" id="cradar" role="img" aria-label="Radar overlay of both tools"></canvas><figcaption class="cap"><span class="key a"></span><span id="ka"></span> <span class="key b"></span><span id="kb"></span></figcaption></figure><div id="cscore" class="cscore"></div></div>')}
{band()}
{sec("Detail", "Criterion by criterion", '<div class="tablewrap"><table class="cmp" id="ctable"></table></div>')}
{band()}
{sec("Facts", "Features, verdicts and evidence", '<div class="tablewrap"><table class="cmp facts2" id="cfacts"></table></div>')}
"""
write("compare.html", page("compare.html", "Compare / Harness Bench", "Compare two agent orchestrators side by side.", cbody, 0, "compare.html"))

# ---------- METHODOLOGY ----------
rub = "".join(f'<tr><th scope="row">{c["k"]}</th><td>{esc(c["label"])}</td><td class="num">{c["w"]}</td><td>{esc(c["five"])}</td></tr>' for c in crit)
lane_rows = f'<tr><th scope="row">Baseline git worktree</th><td class="num">1</td><td class="num">0.043</td><td class="num">8.4</td><td class="num">6/6</td><td class="num">-</td></tr>'
for nm, rs in [("Claude Squad", cs_runs), ("Orca (orca serve CLI)", or_runs)]:
    lane_rows += f'<tr><th scope="row">{nm}</th><td class="num">3</td><td class="num">{min(r["launch"] for r in rs):.2f} to {max(r["launch"] for r in rs):.2f}</td><td class="num">{sum(r["total"] for r in rs)/3:.1f}</td><td class="num">{sum(r["verified"] for r in rs)}/18</td><td class="num">{min(r["rss"] for r in rs):.0f} to {max(r["rss"] for r in rs):.0f}</td></tr>'
probes = sorted(((T[k]["name"], v) for k, v in [(i, gui[g]) for i, g in GUIKEY.items() if g in gui]), key=lambda x: x[1]["first_window_s"])
pr = "".join(f'<tr><th scope="row">{esc(n)}</th><td class="num">{v["first_window_s"]}</td><td class="num">{v["rss_mb_tree"]}</td></tr>' for n, v in probes)
lbr = "".join(f'<tr><td>{esc(x["model"])}</td><td>{x["task"]}</td><td>{x["exit"]}</td><td class="num">{x["wall"] if x["wall"] is not None else "-"}</td><td>{"pass" if x["ok"] else "fail"}</td></tr>' for x in lb)
mbody = f"""<section class="phead"><div class="wrap"><span class="lab">Methodology</span><h1>How the scores were made, and what they are not</h1>
<p class="lede">This is a docs and feature-testing benchmark. Scores are editorial judgement on a 0 to 5 scale per criterion, backed by vendor docs, repos, a GitHub snapshot (2026-10-19 17:25 UTC) and hands-on probes on one Linux box. There are no real-model task results in any score: no Claude, Codex, Cursor or Grok agent CLI was logged in on the box.</p></div></section>
{band()}
{sec("Rubric", "Nine criteria, 100 points of weight", f'<div class="tablewrap"><table><thead><tr><th scope="col">Key</th><th scope="col">Criterion</th><th scope="col">Weight</th><th scope="col">What a 5 means</th></tr></thead><tbody>{rub}</tbody></table></div><div class="chart dk-theme-dark" data-bars="{bars_attr([(c["label"], c["w"]) for c in crit], 0)}" data-max="15" style="--h:300px" role="img" aria-label="Criterion weights"></div><p class="cap">Score = sum(weight x criterion score) / 100 x 20. A criterion with no evidence counts as 2.5, and coverage reports the share of weight that had evidence.</p>')}
{band()}
{sec("Box", "Test environment", '<dl class="facts"><div><dt>Machine</dt><dd>Linux x86_64, 8 vCPU, 16 GB, no Docker.</dd></div><div><dt>Accounts</dt><dd>No authenticated agent CLIs. We did not buy credits or sign up for anything.</dd></div><div><dt>Fixture</dt><dd>A small Python repo with 6 tasks: bug fix, feature, refactor, test-writing checked against seeded mutants, and two deliberately conflicting edits (t5a, t5b). Hidden verifiers decide pass or fail.</dd></div><div><dt>Verifier self-test</dt><dd>All verifiers fail on the base repo, all pass on reference solutions, and t5a + t5b really conflict.</dd></div></dl>')}
{band()}
{sec("Feature testing / Lane A", "Orchestrator mechanics with a stub agent", f'<p class="body">A deterministic stub agent stands in for a model so we can measure the orchestrator itself: parallel launch, isolation, crash behaviour and merge. It says nothing about how well a real model codes inside each tool.</p><div class="tablewrap"><table><thead><tr><th scope="col">Harness</th><th scope="col">Runs</th><th scope="col">All launched (s)</th><th scope="col">Mean wall (s)</th><th scope="col">Verified</th><th scope="col">Peak RSS MB</th></tr></thead><tbody>{lane_rows}</tbody></table></div>')}
{band()}
{sec("Launch probes", "Time to first window on Xvfb", f'<div class="split"><div class="tablewrap"><table><thead><tr><th scope="col">Tool</th><th scope="col">First window (s)</th><th scope="col">RSS MB</th></tr></thead><tbody>{pr}<tr><th scope="row">T3 Code server</th><td class="num">1.01 (port)</td><td class="num">394</td></tr></tbody></table></div><div class="chart dk-theme-dark" data-bars="{bars_attr([(n, v["first_window_s"]) for n, v in probes], 0)}" data-unit=" s" style="--h:290px" role="img" aria-label="First-window seconds per tool, lower is faster"></div></div>')}
{band()}
{sec("Limitations", "What we could not test", f'<ul class="lims"><li><b>No real-model task success.</b> No Claude, Codex, Cursor or Grok CLI was logged in. The only key was a Groq free tier (7 to 8k tokens per minute) and one opencode request was 7.3 to 8.6k tokens. 0 of {len(lb)} attempts passed ({n_rate} rate-limit, {n_large} too-large and {n_schema} tool-schema errors in the logs). Those attempts are shown below for transparency and are not used in any score.</li><li><b>T3 Code and Synara sessions.</b> Both orchestrate agent CLIs that must be installed and authenticated; none were.</li><li><b>Cloudroom core.</b> Its installer needs root and systemd on a fresh Ubuntu 24.04 VM, which we did not do on a shared box.</li><li><b>Closed or macOS-only tools</b> (Conductor and others) were scored from docs and secondary sources only.</li><li><b>Judgement.</b> Criterion scores are one reviewer\'s reading of the evidence. Use the sensitivity table on the leaderboard and the coverage column to see how much a ranking depends on it.</li><li><b>Snapshot.</b> Stars, releases and pricing are as of 2026-10-19 and several tools ship daily.</li></ul><div class="tablewrap"><table><caption class="lab capt">Lane B attempts (not scored)</caption><thead><tr><th scope="col">Model</th><th scope="col">Task</th><th scope="col">Exit</th><th scope="col">Wall s</th><th scope="col">Verified</th></tr></thead><tbody>{lbr}</tbody></table></div>')}
"""
write("methodology.html", page("methodology.html", "Methodology / Harness Bench", "Rubric, weights and limitations.", mbody, 0, "methodology.html"))

# ---------- ABOUT / FAQ ----------
faq = [
 ("Who made this?", "Arjun Shah ran the benchmark on 2026-10-19. Every number on this site comes from the logs under runs/ and the curated data file in the benchmark repo."),
 ("Is this a test of which tool writes the best code?", "No. Code quality depends on the model and agent inside the orchestrator. We measured orchestration features and mechanics, and no real-model task runs feed the scores."),
 ("Why did real-model runs not happen?", f"No agent CLI was logged in on the box. A Groq free-tier key was tried through opencode, and 0 of {len(lb)} attempts passed because a single request exceeded the per-minute token limit."),
 ("Which tool is David Ondrej's?", "Cloudroom (cloudroom.dev; davidondrej/cloudroom-core and cloudroom-gui, Apache-2.0). It scores 72.0 with 80% coverage. There is a public dispute on X between its maker and T3 Code's author; we cite neither side's claims as evidence."),
 ("Why is Orca's star count flagged?", "GitHub reports about 97.9k stars, which is unusually high for a 7-month-old repo. We did not audit star provenance, and stars are only one input to the maturity criterion."),
 ("What does the dot in the table mean?", "No evidence for that criterion. It is scored as a neutral 2.5, and the coverage column shows how much of the weight a score actually rests on."),
 ("Can I re-weight the scores?", "The leaderboard shows four weight profiles. The raw criterion scores are in assets/data.json if you want your own."),
 ("Were any vendors paid or contacted?", "No. Nothing was bought and no accounts were created."),
]
fh = "".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)
sm = ", ".join(esc(x) for x in SECONDARY)
allsrc = "".join(f'<li><a href="{esc(u)}" rel="noopener">{esc(l)}</a></li>' for l, u in SOURCES)
abody = f"""<section class="phead"><div class="wrap"><span class="lab">About / FAQ</span><h1>About this benchmark</h1>
<p class="lede">An independent look at the apps that run several coding agents in parallel with worktrees, sessions and review. Built from docs and feature testing, with the limits stated plainly.</p></div></section>
{band()}
{sec("FAQ", "Questions", f'<div class="faq">{fh}</div>')}
{band()}
{sec("Also mentioned", "Named in secondary sources, not checked", f'<p class="body">{sm}.</p>')}
{band()}
{sec("Sources", "Everything we cited", f'<ul class="srcs cols">{allsrc}</ul><p class="cap">Site built as static HTML. Charts and art use DitherKit Lite (the SuperCompress brand-pack port of Tripwire dither-kit) plus a small Bayer renderer for the heatmap, radar and hero.</p>')}
"""
write("about.html", page("about.html", "About / FAQ / Harness Bench", "About the agent orchestrator benchmark.", abody, 0, "about.html"))
print("ok", [(t["name"], t["score"]) for t in tools])
