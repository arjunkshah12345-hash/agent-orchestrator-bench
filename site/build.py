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
for x in tools:
    W_ = {k: w for k, _, w, _ in CRITERIA}; known = {k: v for k, v in x["crit"].items() if v is not None}
    lo = round(sum(W_[k] * v for k, v in known.items()) / 100 * 20, 1); hi = round(lo + sum(W_[k] for k in x["crit"] if x["crit"][k] is None) / 100 * 100, 1)
    x["range"] = [lo, hi]
    x["validation"] = "Stub end-to-end" if x["id"] in ("orca", "cs") else "Launched" if x["status"].startswith("Installed") else "None"
    x["measured"] = ("Stub run x3, launch probe" if x["id"] == "orca" else "Stub run x3" if x["id"] == "cs" else "Server probe" if x["id"] == "t3"
                     else "Launch probe" if x["first_window"] is not None else "Boot only" if x["id"] == "vk" else "None")
TJ = {x["id"]: x for x in tools}
crit = [dict(k=k, label=l, w=w, five=f) for k, l, w, f in CRITERIA]
bench = dict(tools=tools, criteria=crit, profiles={k: v for k, v in PROFILES.items()})
open(HERE + "/assets/data.js", "w").write("window.BENCH=" + json.dumps(bench, separators=(",", ":")) + ";\n")
json.dump(bench, open(HERE + "/assets/data.json", "w"), indent=1)

# ---------- layout ----------
NAV = [("index.html","Home"),("leaderboard.html","Feature assessment"),("tiers.html","Tiers"),("reproduce.html","Reproduce"),("compare.html","Compare"),("methodology.html","Methodology"),("about.html","About / FAQ")]
def page(fname, title, desc, body, depth=0, active=""):
    r = "../" * depth
    nav = "".join(f'<a href="{r}{h}"' + (' aria-current="page"' if h == active else "") + f'>{esc(l)}</a>' for h, l in NAV)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta name="twitter:card" content="summary">
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
<nav id="nav" aria-label="Primary">{nav}</nav><a class="gh" href="https://github.com/arjunkshah12345-hash/agent-orchestrator-bench" aria-label="GitHub repository: arjunkshah12345-hash/agent-orchestrator-bench" rel="noopener"><svg viewBox="0 0 16 16" width="20" height="20" aria-hidden="true" focusable="false"><path fill="currentColor" d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"/></svg></a></div></header>
<main id="main">{body}</main>
<footer class="foot"><div class="hatch" aria-hidden="true"></div><div class="wrap footin">
<div><span class="lab">Harness Bench / 2026-10-19</span><p>A feature and orchestration benchmark, not a model leaderboard. The weighted feature assessment is editorial judgement from docs, repos and feature testing on one Linux box; the only measured results are stub-agent runs. No real-model task runs were scored.</p></div>
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

# ---------- TIERS ----------
TIERS = [("S", 90, "90 and up"), ("A", 75, "75 to 89.9"), ("B", 70, "70 to 74.9"), ("C", 60, "60 to 69.9"), ("D", 0, "below 60")]
def tier_of(v): return next(k for k, c, _ in TIERS if v >= c)
TL = {k: [t for t in tools if tier_of(t["score"]) == k] for k, _, _ in TIERS}
def chips(ts, r=""):
    return "".join(f'<a class="chip" href="{r}tools/{t["id"]}.html"><b>{esc(t["short"])}</b><span>{t["score"]:.1f}</span>' + (f'<em title="Score range crosses tiers">{tier_of(t["range"][0])} to {tier_of(t["range"][1])}</em>' if tier_of(t["range"][0]) != tier_of(t["range"][1]) else "") + '</a>' for t in ts)
def tierrows(r=""):
    return "".join(f'<div class="tier t{k}"><div class="tk"><canvas class="tband" data-tier="{i}" aria-hidden="true"></canvas><b>{k}</b><span class="lab">{c}</span></div><div class="tchips">{chips(TL[k], r) or "<span class=lab>none</span>"}</div></div>' for i, (k, _, c) in enumerate(TIERS))
TNOTE = '<p class="note"><b>Feature-assessment tier list, not a performance ranking.</b> Tiers come from the weighted feature assessment (docs, repos, feature testing). Only Orca and Claude Squad were run end-to-end, and only with stub agents. A chip marked "B to A" has a score range that crosses tiers because some criteria had no evidence.</p>'
# ---------- HOME ----------
cs_runs = lane["Claude Squad"]; or_runs = lane["Orca (orca serve CLI)"]
orv = sum(r["verified"] for r in or_runs); csv_ = sum(r["verified"] for r in cs_runs)
def rng(rs, k, f="{:.2f}"): return f.format(min(r[k] for r in rs)) + " to " + f.format(max(r[k] for r in rs))
OL, CL = rng(or_runs, "launch"), rng(cs_runs, "launch"); OM, CM = rng(or_runs, "rss", "{:.0f}"), rng(cs_runs, "rss", "{:.0f}")
NOTE = ('<p class="note"><b>Read the scores as a feature assessment.</b> Orca was run end-to-end with stub agents; T3 Code was not run through an equivalent session, '
        'so Orca 93 vs T3 Code 90 is a difference in assessed features and evidence, not an experimentally proven gap.</p>')
def mbars(rows, mx, unit):
    return esc(json.dumps([{"label": l, "value": v, "hl": h} for l, v, h in rows]))
launch_bars = mbars([("Orca", max(r["launch"] for r in or_runs), 1), ("Claude Squad", max(r["launch"] for r in cs_runs), 0)], 0, "s")
mem_bars = mbars([("Orca", max(r["rss"] for r in or_runs), 0), ("Claude Squad", max(r["rss"] for r in cs_runs), 1)], 0, "MB")
measured = f"""<div class="mpanel"><div class="mhead"><span class="lab">Measured / stub-agent test on Linux / 3 runs each</span><span class="tag ok">Measured</span></div>
<div class="mrow"><span class="lab">Verified stub tasks</span><div class="mvs"><div><b>{orv}/18</b><small>Orca</small></div><div><b>{csv_}/18</b><small>Claude Squad</small></div></div></div>
<div class="mrow"><span class="lab">Six-agent launch, worst of 3 (s). Lower is faster; highlighted bar wins</span><div class="chart bare dk-theme-dark" data-bars="{launch_bars}" data-unit=" s" data-dec="2" role="img" aria-label="Six-agent launch: Orca {OL} s, Claude Squad {CL} s"></div><p class="mcap">Orca {OL} s / Claude Squad {CL} s (includes about 1.1 s per session of tmux keystroke delays from our driver)</p></div>
<div class="mrow"><span class="lab">Peak memory, worst of 3 (MB RSS). Lower is lighter; highlighted bar wins</span><div class="chart bare dk-theme-dark" data-bars="{mem_bars}" data-unit=" MB" role="img" aria-label="Peak memory: Orca {OM} MB, Claude Squad {CM} MB"></div><p class="mcap">Orca {OM} MB (about 1.1 GB) / Claude Squad {CM} MB</p></div>
<p class="mfoot">The stub agent is a deterministic script, not an LLM. It measures the orchestrator, not code quality.</p></div>"""
podium = "".join(f"""<a class="pod" href="tools/{t['id']}.html"><span class="lab">#{t['rank']} / {esc(t['validation'])}</span>
<span class="podn">{esc(t['name'])}</span><span class="pods"><b>{t['score']:.0f}</b><small>/100 assessed</small></span><span class="lab">range {t['range'][0]} to {t['range'][1]}</span>
<span class="meter" data-meter="{t['score']}" data-max="100" data-hl="0" role="img" aria-label="{esc(t['name'])} assessed {t['score']} of 100"></span>
<span class="podw">{esc(t['why'])}</span></a>""" for t in tools[:3])
take = [
 ("Fast or light, not both", f"In the stub-agent test Orca launched six agents in {OL} s but peaked at {OM} MB. Claude Squad took {CL} s and peaked at {CM} MB. Both verified 18/18."),
 ("Orca: most validated", "The only GUI orchestrator we drove end-to-end on Linux, headless via orca serve. Highest weighted feature assessment (93) with full evidence coverage."),
 ("T3 Code: deepest documented features", "Cross-provider delegate_task, an MCP for agents, PR flow and mobile. Its server booted headless in 1.01 s, but no agent session ran through it, so its 90 rests on docs and a server probe."),
 ("Claude Squad: the light terminal option", "About 100 MB under load, scriptable through tmux, and sessions came back paused and resumable after we killed tmux. Weak on PR and remote features (assessed 65)."),
 ("Cloudroom: different model", f"David Ondrej's tool runs sessions on cloud VMs. GUI launched in 3.3 s; the core needs root on a fresh VM so it was not installed. Assessed {TJ['cloudroom']['score']}, range {TJ['cloudroom']['range'][0]} to {TJ['cloudroom']['range'][1]}."),
 ("No real-model results yet", "No Claude, Codex, Cursor or Grok CLI was logged in. A ready-to-run real-agent round is in the repo; nothing from it is reported as a result."),
]
tk = "".join(f'<li><span class="lab">{n:02d}</span><h3>{esc(a)}</h3><p>{esc(b)}</p></li>' for n, (a, b) in enumerate(take, 1))
home = f"""<section class="hero"><canvas class="field" id="heroField" aria-hidden="true"></canvas><div class="wrap heroin">
<div class="herotext"><span class="lab">Feature + orchestration benchmark / not a model leaderboard / 2026-10-19</span>
<h1>There's no universal winner.</h1>
<p class="lede">We tested how agent orchestrators run Claude Code, Codex and friends in parallel. On Linux, with a stub agent, Orca launched six agents in under 2 s against 11 to 12 s for Claude Squad, and used about ten times the memory. Which matters depends on your machine and workflow.</p>
<div class="cta"><a class="mb" href="reproduce.html">Reproduce this benchmark</a><a class="mb o" href="leaderboard.html">Feature assessment</a><a class="mb o" href="methodology.html">Method</a></div></div>
{measured}
</div><i class="x xl" aria-hidden="true"></i><i class="x xr" aria-hidden="true"></i></section>
{band()}
{sec("Key takeaways", "What the data says", f'<ol class="takes">{tk}</ol>')}
{band()}
{sec("Secondary research / weighted feature assessment", "Top 3 by assessed features", f'{NOTE}<div class="podium">{podium}</div><p class="cap">Assessment from docs, repos and feature testing. The range shows the score if every unevidenced criterion were 0 or 5. <a href="leaderboard.html">All 13 tools</a>.</p>')}
{band()}
{sec("Tier list / feature assessment", "Tiers at a glance", f'<div class="tiers mini">{tierrows()}</div><p class="cap">Feature-assessment tiers, not a performance ranking. <a href="tiers.html">Cutoffs and notes</a>.</p>')}
{band()}
{sec("How the stub test works", "6 parallel worktrees, one merge", '<div class="split"><figure class="heroart"><canvas id="heroArt" aria-hidden="true"></canvas><figcaption class="lab">6 parallel worktrees: 5 clean merges, 1 designed conflict (t5b). Ordered Bayer dither.</figcaption></figure><div><p class="body">Each orchestrator launches six sessions of a deterministic stub agent in isolated worktrees. The stub waits, then writes a reference solution; hidden verifiers decide pass or fail. Two tasks edit the same function on purpose, so one merge conflicts by design. This isolates what the orchestrator controls: launch, isolation, crash containment and footprint.</p><p class="body">Raw logs for every number are in the repo under runs/.</p><a class="mb o" href="reproduce.html">Rerun it yourself</a></div></div>')}
{band()}
{sec("Category matrix / assessment", "Where each tool earns its points", '<div class="heat" data-heat role="table" aria-label="Assessed scores by criterion, 0 to 5"></div><p class="cap">Each cell is a 0 to 5 judgement; denser dither means a higher score. Hatched cells had no evidence and are unranked.</p>')}
{band()}
{sec("Real-agent round", "Coming next", '<p class="body">A real-agent comparison is built and ready to run: 3 orchestrators (plain git worktree as control, Orca, Claude Squad) x 1 model x the same 3 coding tasks x 3 repetitions, recording verified success, wall time, tokens and resource use. It has not been run with a real model yet because no agent CLI was logged in on the box. <b>No results from it are shown anywhere on this site.</b></p><a class="mb o" href="reproduce.html#real-round">What it needs to run</a>')}
"""
write("index.html", page("index.html", "Harness Bench: there's no universal agent orchestrator", "Feature and orchestration benchmark of agent orchestrators, not a model leaderboard. Measured stub-agent test: Orca vs Claude Squad, speed vs memory.", home, 0, "index.html"))

# ---------- LEADERBOARD ----------
ck = [c["k"] for c in crit]
head = "".join(f'<th scope="col" aria-sort="none"><button data-k="{k}" data-type="{ty}">{esc(lab)}</button></th>' for k, lab, ty in
    [("rank","#","n"),("name","Tool","s")] + [(c["k"], c["k"], "n") for c in crit] + [("score","Assessed","n"),("lo","Range","n"),("coverage","Doc coverage","n"),("validation","Hands-on validation","s"),("measured","Measured results","s")])
rows = ""
for t in tools:
    rows += (f'<tr data-rank="{t["rank"]}" data-name="{esc(t["name"])}" data-score="{t["score"]}" data-coverage="{t["coverage"]}" data-lo="{t["range"][0]}" data-validation="{esc(t["validation"])}" data-measured="{esc(t["measured"])}" '
        + " ".join(f'data-{k.lower()}="{-1 if t["crit"][k] is None else t["crit"][k]}"' for k in ck) + ">"
        + f'<td class="num">{t["rank"]}</td><th scope="row"><a href="tools/{t["id"]}.html">{esc(t["name"])}</a></th>'
        + "".join(f'<td class="num c{cv(t["crit"][k])}">{cv(t["crit"][k]) if t["crit"][k] is not None else '<span class="unr" title="No evidence: unranked">n/r</span>'}</td>' for k in ck)
        + f'<td class="num sc">{t["score"]:.1f}</td><td class="num rg">{t["range"][0]} to {t["range"][1]}</td><td class="num">{t["coverage"]}%</td><td><span class="tag {"ok" if t["validation"].startswith("Stub") else "no" if t["validation"]=="None" else ""}">{esc(t["validation"])}</span></td><td>{esc(t["measured"])}</td></tr>')
legend = "".join(f'<li><b>{c["k"]}</b> {esc(c["label"])} <span class="lab">w{c["w"]}</span></li>' for c in crit)
unscored = [x for x in T.values() if x["id"] not in SCORED]
ul = "".join(f'<tr><th scope="row">{esc(x["name"])}</th><td>{esc(x["group"])}</td><td>{esc(x["license"])}</td><td>{esc(x["hands_on"])}</td></tr>' for x in unscored)
prof = ""
for pn, pw in PROFILES.items():
    order = sorted(SCORED, key=lambda i: -score(i, pw)[0])[:5]
    prof += f'<tr><th scope="row">{esc(pn)}</th><td>' + ", ".join(f'{esc(T[i]["name"])} ({score(i, pw)[0]})' for i in order) + "</td></tr>"
lbody = f"""<section class="phead"><div class="wrap"><span class="lab">Secondary research / weighted feature assessment</span><h1>{len(SCORED)} orchestrators, one feature rubric</h1>
<p class="lede">This is a weighted feature assessment from docs, repos and feature testing, not a measured performance leaderboard. Click a column to sort. "n/r" marks a criterion with no evidence: it is unranked, and the range shows the score if it were 0 or full marks. The assessed point score is the midpoint of that range.</p>
<p class="cta"><a class="mb o" href="reproduce.html">Reproduce this benchmark</a></p>{NOTE}
<dl class="colkey"><div><dt>Doc coverage</dt><dd>Share of rubric weight backed by documentation or other cited evidence.</dd></div><div><dt>Hands-on validation</dt><dd>None, Launched (installed and opened on Linux), or Stub end-to-end (six stub-agent sessions driven and verified).</dd></div><div><dt>Measured results</dt><dd>Which logged measurements exist for the tool in runs/.</dd></div></dl></div></section>
{band()}
{sec("Assessed scores", "", f'<div class="chart dk-theme-dark" data-bars="{bars_attr([(t["short"], t["score"]) for t in tools], 1)}" style="--h:{len(tools)*30+30}px" role="img" aria-label="Bar chart of weighted scores"></div>')}
{band()}
{sec("Full table", "Every criterion", f'<div class="tablewrap" tabindex="0" role="region" aria-label="Sortable leaderboard table"><table class="lb" id="lb"><caption class="sr">Leaderboard, sortable by column</caption><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div><ul class="legend">{legend}</ul>')}
{band()}
{sec("Sensitivity", "Does the ranking survive other weightings?", f'<div class="tablewrap"><table><thead><tr><th scope="col">Weight profile</th><th scope="col">Top 5 (score)</th></tr></thead><tbody>{prof}</tbody></table></div><p class="cap">Solo terminal hacker: friction 20, openness 15, review 8, reach 3. Team shipping PRs: review 30, maturity 20. Remote / phone-first: reach 30, friction 5. Unlisted criteria keep the default weight.</p>')}
{band()}
{sec("Landscape, not scored", f"{len(unscored)} more tools we checked", f'<div class="tablewrap"><table><thead><tr><th scope="col">Tool</th><th scope="col">Category</th><th scope="col">License</th><th scope="col">Why no score</th></tr></thead><tbody>{ul}</tbody></table></div>')}
"""
write("leaderboard.html", page("leaderboard.html", "Weighted feature assessment / Harness Bench", "Weighted feature assessment of 13 agent orchestrators from docs and feature testing; not a measured performance leaderboard.", lbody, 0, "leaderboard.html"))


tbody = f"""<section class="phead"><div class="wrap"><span class="lab">Tier list / weighted feature assessment</span><h1>Feature-assessment tiers</h1>
<p class="lede">The {len(tools)} scored orchestrators grouped by their weighted feature assessment. Cutoffs: S 90 and up, A 75 to 89.9, B 70 to 74.9, C 60 to 69.9, D below 60. The score is the midpoint of each tool's range.</p></div></section>
{band()}
{sec("Tiers", "", TNOTE + f'<div class="tiers">{tierrows()}</div><p class="cap">Click a tool for its criteria, evidence and range. Cutoffs are fixed round numbers chosen before grouping; a tool one point either side of a cutoff is effectively tied with its neighbour.</p>')}
"""
write("tiers.html", page("tiers.html", "Feature-assessment tier list / Harness Bench", "S to D tiers from the weighted feature assessment of 13 agent orchestrators; not a performance ranking.", tbody, 0, "tiers.html"))


# ---------- TOOL PAGES ----------
FL = [("platforms","Platforms"),("agents","Supported agents"),("parallel","Parallelism"),("isolation","Isolation"),("review","Review, merge, PR"),("remote","Remote, cloud, mobile"),("mcp","MCP"),("cost","Cost visibility"),("models","Model choice"),("setup","Setup")]
for t in tools:
    i = t["id"]; raw = T[i]
    crow = "".join(f'<li><span class="ck">{c["k"]}</span><span class="cl">{esc(c["label"])}<small>weight {c["w"]}</small></span><span class="meter" data-meter="{t["crit"][c["k"]] if t["crit"][c["k"]] is not None else 0}" data-max="5" data-none="{1 if t["crit"][c["k"]] is None else 0}" role="img" aria-label="{esc(c["label"])}: {cv(t["crit"][c["k"]])} of 5"></span><b class="cv">{cv(t["crit"][c["k"]]) if t["crit"][c["k"]] is not None else "n/r"}</b></li>' for c in crit)
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
<div class="bigscore"><span class="lab">Weighted feature assessment</span><b>{t['score']:.1f}</b><span class="lab">range {t['range'][0]} to {t['range'][1]}</span><span class="lab">doc coverage {t['coverage']}% / {esc(t['validation'])}</span><span class="lab">measured: {esc(t['measured'])}</span><span class="meter" data-meter="{t['score']}" data-max="100" data-hl="1" role="img" aria-label="{t['score']} of 100"></span></div></div>
<div class="wrap"><dl class="meta">{mh}</dl></div></section>
{band()}
{sec("Scores by category", "Rubric breakdown", (NOTE if i in ("orca","t3") else "") +  f'<div class="split"><ul class="crit">{crow}</ul><figure class="radarfig"><canvas class="radar" data-radar="{i}" role="img" aria-label="Radar chart of {esc(t["name"])} scores by criterion"></canvas><figcaption class="cap">{esc(t["why"])}</figcaption></figure></div>')}
{band()}
{sec("Verdict", "Strengths and weaknesses", '<div class="pc"><div><h3 class="lab">Strengths</h3><ul>' + "".join(f"<li>{esc(x)}</li>" for x in t["pros"]) + '</ul></div><div><h3 class="lab">Weaknesses</h3><ul>' + "".join(f"<li>{esc(x)}</li>" for x in t["cons"]) + '</ul></div></div>')}
{band()}
{sec("Evidence", "What we saw and where it came from", f'<div class="split"><dl class="ev">{evh}</dl>{shot}</div>' + (f'<h3 class="lab srch">Sources</h3><ul class="srcs">{sl}</ul>' if sl else ""))}
{band()}
{sec("Feature facts", "From docs, repos and our probes", f'<dl class="facts">{facts}</dl><p class="cap">"unknown" means we found no source and did not guess.</p>{pn}')}
"""
    write(f"tools/{i}.html", page(f"tools/{i}.html", f"{t['name']} / Harness Bench", f"{t['name']}: weighted feature assessment {t['score']} of 100 (range {t['range'][0]} to {t['range'][1]}), from docs and feature testing.", body, 1, ""))

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
<p class="lede">This is a feature and orchestration benchmark, not a model leaderboard. The ranking is a weighted feature assessment, not measured performance. Scores are editorial judgement on a 0 to 5 scale per criterion, backed by vendor docs, repos, a GitHub snapshot (2026-10-19 17:25 UTC) and hands-on probes on one Linux box. There are no real-model task results in any score: no Claude, Codex, Cursor or Grok agent CLI was logged in on the box.</p></div></section>
{band()}
{sec("Rubric", "Nine criteria, 100 points of weight", f'<div class="tablewrap"><table><thead><tr><th scope="col">Key</th><th scope="col">Criterion</th><th scope="col">Weight</th><th scope="col">What a 5 means</th></tr></thead><tbody>{rub}</tbody></table></div><div class="chart dk-theme-dark" data-bars="{bars_attr([(c["label"], c["w"]) for c in crit], 0)}" data-max="15" style="--h:300px" role="img" aria-label="Criterion weights"></div><p class="cap">Score = sum(weight x criterion score) / 100 x 20. A criterion with no evidence is unranked (shown as n/r). Each tool gets a range: the minimum treats unranked criteria as 0, the maximum as 5. The point score is the midpoint of that range; read it together with the range and the doc coverage, hands-on validation and measured-results columns.</p>')}
{band()}
{sec("Box", "Test environment", '<dl class="facts"><div><dt>Machine</dt><dd>Linux x86_64, 8 vCPU, 16 GB, no Docker.</dd></div><div><dt>Accounts</dt><dd>No authenticated agent CLIs. We did not buy credits or sign up for anything.</dd></div><div><dt>Fixture</dt><dd>A small Python repo with 6 tasks: bug fix, feature, refactor, test-writing checked against seeded mutants, and two deliberately conflicting edits (t5a, t5b). Hidden verifiers decide pass or fail.</dd></div><div><dt>Verifier self-test</dt><dd>All verifiers fail on the base repo, all pass on reference solutions, and t5a + t5b really conflict.</dd></div></dl>')}
{band()}
{sec("Feature testing / Lane A", "Orchestrator mechanics with a stub agent", f'<p class="body">A deterministic stub agent stands in for a model so we can measure the orchestrator itself: parallel launch, isolation, crash behaviour and merge. It says nothing about how well a real model codes inside each tool.</p><div class="tablewrap"><table><thead><tr><th scope="col">Harness</th><th scope="col">Runs</th><th scope="col">All launched (s)</th><th scope="col">Mean wall (s)</th><th scope="col">Verified</th><th scope="col">Peak RSS MB</th></tr></thead><tbody>{lane_rows}</tbody></table></div>')}
{band()}
{sec("Launch probes", "Time to first window on Xvfb", f'<div class="split"><div class="tablewrap"><table><thead><tr><th scope="col">Tool</th><th scope="col">First window (s)</th><th scope="col">RSS MB</th></tr></thead><tbody>{pr}<tr><th scope="row">T3 Code server</th><td class="num">1.01 (port)</td><td class="num">394</td></tr></tbody></table></div><div class="chart dk-theme-dark" data-bars="{bars_attr([(n, v["first_window_s"]) for n, v in probes], 0)}" data-unit=" s" style="--h:290px" role="img" aria-label="First-window seconds per tool, lower is faster"></div></div>')}
{band()}
{sec("Limitations", "What we could not test", f'<ul class="lims"><li><b>No real-model task success.</b> No Claude, Codex, Cursor or Grok CLI was logged in. The only key was a Groq free tier (7 to 8k tokens per minute) and one opencode request was 7.3 to 8.6k tokens. 0 of {len(lb)} attempts passed ({n_rate} rate-limit, {n_large} too-large and {n_schema} tool-schema errors in the logs). Those attempts are shown below for transparency and are not used in any score.</li><li><b>T3 Code and Synara sessions.</b> Both orchestrate agent CLIs that must be installed and authenticated; none were.</li><li><b>Cloudroom core.</b> Its installer needs root and systemd on a fresh Ubuntu 24.04 VM, which we did not do on a shared box.</li><li><b>Closed or macOS-only tools</b> (Conductor and others) were scored from docs and secondary sources only.</li><li><b>Judgement.</b> Criterion scores are one reviewer\'s reading of the evidence. Use the sensitivity table, the score range and the coverage columns to see how much a ranking depends on it.</li><li><b>Snapshot.</b> Stars, releases and pricing are as of 2026-10-19 and several tools ship daily.</li></ul><div class="tablewrap"><table><caption class="lab capt">Lane B attempts (not scored)</caption><thead><tr><th scope="col">Model</th><th scope="col">Task</th><th scope="col">Exit</th><th scope="col">Wall s</th><th scope="col">Verified</th></tr></thead><tbody>{lbr}</tbody></table></div>')}
"""
write("methodology.html", page("methodology.html", "Methodology / Harness Bench", "Rubric, weights and limitations.", mbody, 0, "methodology.html"))

# ---------- ABOUT / FAQ ----------
faq = [
 ("Who made this?", "Arjun Shah ran the benchmark on 2026-10-19. Every number on this site comes from the logs under runs/ and the curated data file in the benchmark repo."),
 ("Is this a test of which tool writes the best code?", "No. Code quality depends on the model and agent inside the orchestrator. We measured orchestration features and mechanics, and no real-model task runs feed the scores."),
 ("Why did real-model runs not happen?", f"No agent CLI was logged in on the box. A Groq free-tier key was tried through opencode, and 0 of {len(lb)} attempts passed because a single request exceeded the per-minute token limit."),
 ("Which tool is David Ondrej's?", f"Cloudroom (cloudroom.dev; davidondrej/cloudroom-core and cloudroom-gui, Apache-2.0). Its weighted feature assessment is 72.0 (range {TJ['cloudroom']['range'][0]} to {TJ['cloudroom']['range'][1]}) with 80% doc coverage. There is a public dispute on X between its maker and T3 Code's author; we cite neither side's claims as evidence."),
 ("Why is Orca's star count flagged?", "GitHub reports about 97.9k stars, which is unusually high for a 7-month-old repo. We did not audit star provenance, and stars are only one input to the maturity criterion."),
 ("What does n/r in the table mean?", "No evidence for that criterion, so it is unranked. The score range shows the result if it were 0 or full marks; the point score is the midpoint."),
 ("Is Orca really better than T3 Code?", "Not proven. Orca was run end-to-end with stub agents; T3 Code was not run through an equivalent session. 93 vs 90 is a difference in assessed features and evidence."),
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

# ---------- REPRODUCE ----------
REPO = "https://github.com/arjunkshah12345-hash/agent-orchestrator-bench"; BL = REPO + "/blob/main/"; TR = REPO + "/tree/main/"
VERS = [("Orca", "v1.4.230 (Linux AppImage, extracted); headless runtime orcad 0.1.0+7a87e80a2a8a", "runs/F-orca/serve.log"),
        ("Claude Squad", "v1.0.20 release binary (claude-squad version 1.0.20)", "runs/C-claude-squad/install.log"),
        ("T3 Code", "v0.1.0 linux-x64 server tarball", "runs/D-t3code/probe.log"),
        ("opencode (Lane B agent)", "1.19.3", "runs/00-setup/opencode-install.log"),
        ("GUI apps (launch probes)", "Synara 1.0.7, Superset 1.39.0, Emdash 1.2.8, OpenChamber 2.5.0, Paseo 0.12.0, Cloudroom GUI v110-beta, Mux/Xum 0.31.0", "runs/00-setup/gui-probes-summary.log"),
        ("Fixture repo", "commit 377fb426b834ede261ddfe7e70a6301aeaf31b5e (\"fixture base\")", "fixture/repo"),
        ("Python / git / tmux", "Python 3.13.5, git 2.47.3, tmux 3.5a", None)]
ENVR = [("OS", "Debian GNU/Linux 13 (trixie), kernel 6.12, x86_64"), ("Hardware", "8 vCPU, 16 GB RAM, no GPU, no Docker"), ("Display", "Xvfb virtual display for GUI apps and orca serve"),
        ("Accounts", "No authenticated agent CLI (Claude, Codex, Cursor, Grok). Nothing bought, no sign-ups."), ("GitHub snapshot", "data/gh_snapshot.json, 2026-10-19 17:25 UTC")]
STEPS = [
 ("Clone and check the fixture", "git clone " + REPO + ".git && cd agent-orchestrator-bench\n# verifiers must fail on the base repo and pass on the references\nfor t in t1 t2 t3 t4 t5a t5b; do python3 harness/verify.py fixture/repo $t; done"),
 ("Baseline (plain git worktree + stub agent)", "python3 harness/baseline_run.py A-baseline-stub 'env STUB_SLEEP=8 python3 harness/benchagent.py {prompt}'"),
 ("Install the orchestrators", "# Orca v1.4.230 AppImage from github.com/stablyai/orca/releases, extract to tools/orca-x\n./orca-linux.AppImage --appimage-extract && mv squashfs-root tools/orca-x/\n# Claude Squad v1.0.20 from github.com/smtg-ai/claude-squad/releases into tools/cs/claude-squad"),
 ("Orca, 3 runs", "Xvfb :90 &\nHOME=/tmp/home-orca-cli DISPLAY=:90 tools/orca-x/squashfs-root/resources/bin/orca-ide serve &\npython3 harness/orca_run.py   # repeat 3x; copy runs/F-orca/result.json + resources.csv per run\nSTUB_CRASH=t3 python3 harness/orca_run.py   # crash test"),
 ("Claude Squad, 3 runs", "python3 harness/cs_run.py   # drives the TUI through tmux; repeat 3x\nSTUB_CRASH=t3 python3 harness/cs_run.py"),
 ("Merge check", "python3 harness/merge_eval.py   # expects 5/6 clean, t5b conflicting in shelf/config.py"),
 ("GUI launch probes", "python3 harness/gui_probe.py <name> <path-to-AppImage>   # first window time + RSS on Xvfb"),
 ("Rebuild the site from the logs", "python3 site/build.py && python3 -m http.server -d site 8000"),
]
RAW = [("runs/repeat/", "Orca and Claude Squad, 3 runs each: run JSON + 1 s resource CSVs"), ("runs/F-orca/", "Orca crash test, merge, serve readiness and restarts"),
       ("runs/C-claude-squad/", "Claude Squad screens, crash test, tmux-kill recovery, merge"), ("runs/A-baseline-stub/", "plain worktree baseline"),
       ("runs/E-gui-*/", "GUI launch probes with screenshots"), ("runs/D-t3code/", "T3 Code server probe"), ("runs/B*/", "Lane B real-model attempts (all failed, not scored)"),
       ("runs/R-real-round-DRYRUN-stub/", "real-agent harness plumbing check with the stub agent (not a result)"),
       ("matrix.csv", "full feature matrix and assessment data"), ("report/tools_data.py", "rubric, criterion scores and rationale"), ("data/gh_snapshot.json", "GitHub API snapshot")]
RR_CMD = "python3 harness/real/real_round.py \\\n  --agent-cmd 'claude -p {prompt} --model {model} --output-format json --dangerously-skip-permissions' \\\n  --model <one model id> --tools baseline,orca,cs --tasks t1,t2,t3 --reps 3"
RR_NEED = ["One authenticated agent CLI on the box, used for all 27 cells. For example Claude Code logged in with `claude login` (Claude subscription) or `ANTHROPIC_API_KEY` set; or Codex CLI with `codex login` / `OPENAI_API_KEY`; or opencode with a provider key whose rate limit fits one request (the Groq free tier at 7 to 8k tokens per minute does not: one opencode request was 7.3 to 8.6k tokens).",
           "`orca serve` running on an Xvfb display (step 4) and tmux for Claude Squad.",
           "Budget for 27 agent runs (3 tools x 3 tasks x 3 reps). Tokens are taken from the CLI's own JSON usage output; if a CLI prints none, tokens are recorded as empty, never estimated."]
vh = "".join(f'<tr><th scope="row">{esc(a)}</th><td>{esc(b)}</td><td>' + (f'<a href="{BL if "." in c.split("/")[-1] else TR}{c}">{esc(c)}</a>' if c else "-") + "</td></tr>" for a, b, c in VERS)
eh = "".join(f'<div><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>' for a, b in ENVR)
sh = "".join(f'<li><h3>{esc(a)}</h3><pre><code>{esc(b)}</code></pre></li>' for a, b in STEPS)
rh = "".join(f'<li><a href="{(TR if p.endswith("/") else BL)}{p.replace("*", "")}">{esc(p)}</a> <span>{esc(d)}</span></li>' for p, d in RAW)
tasks_h = "".join(f'<li><b>{k}</b> {esc(v)}</li>' for k, v in json.load(open(BENCH + "/fixture/tasks.json")).items())
nh = "".join(f"<li>{esc(x).replace('`', '')}</li>" for x in RR_NEED)
rbody = f"""<section class="phead"><div class="wrap"><span class="lab">Reproduce</span><h1>Reproduce this benchmark</h1>
<p class="lede">Everything behind the numbers is in the public repo: fixture, hidden verifiers, harness scripts, raw logs and scoring data. These steps rerun the measured stub-agent test on a Linux box.</p>
<p class="cta"><a class="mb" href="{REPO}">Open the repo</a><a class="mb o" href="{BL}REPRODUCE.md">REPRODUCE.md</a><a class="mb o" href="{BL}matrix.csv">matrix.csv</a></p></div></section>
{band()}
{sec("Versions", "Exact tool versions", f'<div class="tablewrap"><table><thead><tr><th scope="col">Component</th><th scope="col">Version</th><th scope="col">Evidence</th></tr></thead><tbody>{vh}</tbody></table></div><p class="cap">Tools were installed from release binaries, so we record release tags and build ids; we did not record source commits for them.</p>')}
{band()}
{sec("Environment", "The box", f'<dl class="facts">{eh}</dl>')}
{band()}
{sec("Fixture", "Six tasks, hidden verifiers", f'<ul class="lims tasks">{tasks_h}</ul><p class="cap"><a href="{TR}fixture">fixture/</a> holds the repo, <a href="{BL}fixture/tasks.json">tasks.json</a>, the hidden verifiers and reference solutions. The stub agent is <a href="{BL}harness/benchagent.py">harness/benchagent.py</a>.</p>')}
{band()}
{sec("Steps", "Rerun it", f'<ol class="steps">{sh}</ol>')}
{band()}
{sec("Raw data", "Logs and scoring data", f'<ul class="srcs">{rh}</ul>')}
{band()}
{sec("Real-agent round / coming next", "Ready to run, not yet run", f'<p class="body">3 orchestrators (plain git worktree as control, Orca, Claude Squad) x 1 model x 3 tasks (t1 bug fix, t2 feature, t3 refactor) x 3 repetitions. Each cell records verified success from the hidden verifiers, agent exit, wall time, tokens and peak RSS. A plumbing check with the stub agent passed all 27 cells; that only shows the harness works and is not a result.</p><pre><code>{esc(RR_CMD)}</code></pre><h3 class="lab srch">What it needs</h3><ul class="lims">{nh}</ul>', id_="real-round")}
"""
write("reproduce.html", page("reproduce.html", "Reproduce this benchmark / Harness Bench", "Versions, commands, fixture, raw logs and scoring data to rerun the agent orchestrator benchmark.", rbody, 0, "reproduce.html"))
md = ["# Reproduce this benchmark", "", "This is a feature and orchestration benchmark, not a model leaderboard. The measured part is a stub-agent test of Orca and Claude Squad on Linux. Live site: https://arjunkshah12345-hash.github.io/agent-orchestrator-bench/reproduce.html", "", "## Versions", "", "| Component | Version | Evidence |", "|---|---|---|"]
md += [f"| {a} | {b} | {('`' + c + '`') if c else '-'} |" for a, b, c in VERS]
md += ["", "Tools were installed from release binaries, so release tags and build ids are recorded, not source commits.", "", "## Environment", ""] + [f"- **{a}:** {b}" for a, b in ENVR]
md += ["", "## Fixture", "", "`fixture/repo` (6 tasks in `fixture/tasks.json`), hidden verifiers in `fixture/verify`, reference solutions in `fixture/ref`. Stub agent: `harness/benchagent.py` (deterministic, not an LLM).", "", "## Steps", ""]
for n, (a, b) in enumerate(STEPS, 1): md += [f"{n}. {a}", "", "```", b, "```", ""]
md += ["## Raw data", ""] + [f"- `{p}`: {d}" for p, d in RAW]
md += ["", "## Real-agent round (ready, not yet run)", "", "3 orchestrators (baseline worktree, Orca, Claude Squad) x 1 model x 3 tasks (t1, t2, t3) x 3 reps. Outputs `runs/R-real-round/results.csv`.", "", "```", RR_CMD, "```", "", "Plumbing check (stub agent, not a result): `python3 harness/real/real_round.py --dry-run`", "", "What it needs:", ""] + [f"- {x}" for x in RR_NEED] + [""]
txt = "\n".join(md); assert "\u2014" not in txt; open(BENCH + "/REPRODUCE.md", "w").write(txt)

print("ok", [(t["name"], t["score"]) for t in tools])
