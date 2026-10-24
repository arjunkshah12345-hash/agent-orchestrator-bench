#!/usr/bin/env python3
"""Builds index.html, report.md, matrix.csv from tools_data.py + raw run logs in ../runs. No network, no CDN."""
import json, csv, os, glob, base64, html, datetime, statistics as st
from tools_data import *
R = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(R); RUNS = B + "/runs"
J = lambda p: json.load(open(p))
esc = html.escape
gh = J(B + "/data/gh_snapshot.json")
snap_day = gh["snapshot_utc"][:10]

# ---------- collect hands-on data (only from files) ----------
def peak(f, col="match_rss_mb"):
    rows = list(csv.DictReader(open(f))); return max(float(r[col]) for r in rows) if rows else None
lane = {}
LANE_PRE = {"Claude Squad": "cs", "Orca (orca serve CLI)": "orca", "Realm (realm serve CLI)*": "realm"}
for tool, pre in LANE_PRE.items():
    runs = []
    for i in (1, 2, 3):
        d = J(f"{RUNS}/repeat/{pre}-run{i}.json"); s = d["sessions"]
        runs.append(dict(verified=sum(1 for v in s.values() if v.get("verified")), launch=d.get("all_sessions_created_s") or d.get("all_launched_s"), total=d["total_wall_s"], rss=peak(f"{RUNS}/repeat/{pre}-res{i}.csv")))
    lane[tool] = runs
base = J(f"{RUNS}/A-baseline-stub/result.json")
cs_one = J(f"{RUNS}/repeat/cs-run1.json"); orca_one = J(f"{RUNS}/repeat/orca-run1.json")
cs_crash = J(f"{RUNS}/C-claude-squad/result-crash.json"); orca_crash = J(f"{RUNS}/F-orca/result-crash.json")
cs_merge = J(f"{RUNS}/C-claude-squad/merge.json"); orca_merge = J(f"{RUNS}/F-orca/merge.json")
orca_ready = J(f"{RUNS}/F-orca/serve-ready.json")["orca_serve_ready_s"]
realm_one = J(f"{RUNS}/repeat/realm-run1.json"); realm_crash = J(f"{RUNS}/F-realm/result-crash.json"); realm_merge = J(f"{RUNS}/F-realm/merge.json")
realm_ready = J(f"{RUNS}/F-realm/serve-ready.json")["realm_serve_ready_s"]
# Realm's lane A and its launch probe were run by Realm's author on a GitHub-hosted runner, not on the box above, with Orca
# measured on the same runner in the same job; every table that shows them says so.
RUNNER = "a GitHub-hosted ubuntu-latest runner (x86_64, 4 vCPU, 16 GB, Ubuntu 24.04)"
REALM_NOTE = (f"* Realm: run by Realm's author (a disclosed conflict of interest) on {RUNNER}, not on the 8 vCPU box the other rows come from, "
              "through the `realm` command the v2.5.0 release's Linux AppImage ships (squashfs-root/resources/bin/realm). Same harness shape (harness/realm_run.py), "
              "same fixture, stub and verifiers. Orca 1.4.230 ran on the same runner in the same job (harness/orca_suite.py, runs/F-orca-same-runner/). "
              "Earlier runs are in runs/F-realm-ci-build/ (a pre-release CI build), runs/F-realm-container/ (a Debian 13 container) and runs/F-realm-macos/.")
def median_probe(d):
    ps = sorted((J(p) for p in sorted(glob.glob(f"{d}/probe-run*.json"))), key=lambda p: p["first_window_s"]); return ps[len(ps) // 2]
realm_gui, orca_gui_same = median_probe(f"{RUNS}/F-realm/gui"), median_probe(f"{RUNS}/F-orca-same-runner/gui")
orca_same = [J(f"{RUNS}/F-orca-same-runner/repeat/orca-run{i}.json") for i in (1, 2, 3)]
orca_same_rss = [peak(f"{RUNS}/F-orca-same-runner/repeat/orca-res{i}.csv") for i in (1, 2, 3)]
orca_same_ready = J(f"{RUNS}/F-orca-same-runner/serve-ready.json")["orca_serve_ready_s"]
span = lambda xs, f="{:.2f}": f.format(min(xs)) if min(xs) == max(xs) else f"{f.format(min(xs))} to {f.format(max(xs))}"
gui = {os.path.basename(d)[6:]: J(d + "/probe.json") for d in sorted(glob.glob(f"{RUNS}/E-gui-*"))}
t3 = J(f"{RUNS}/D-t3code/probe.json")
lb = []
for lab, model in [("B-baseline-opencode-gptoss120b", "groq/openai/gpt-oss-120b (6 parallel)"), ("B3-baseline-opencode-gptoss20b-t1", "groq/openai/gpt-oss-20b (serial)")]:
    d = J(f"{RUNS}/{lab}/result.json")
    for k, v in d.items():
        if not k.startswith("_"): lb.append(dict(model=model, task=k, exit=v["agent_exit"], wall=v["wall_s"], ok=v["verified"]))
lb.append(dict(model="groq/qwen/qwen3.8-27b (serial)", task="t1", exit="aborted", wall=None, ok=False))
def grep_count(pattern, files):
    n = 0
    for f in files: n += open(f, errors="ignore").read().count(pattern)
    return n
b_logs = glob.glob(f"{RUNS}/B*/*.log")
n_rate = grep_count("Rate limit reached", b_logs); n_large = grep_count("Request too large", b_logs); n_schema = grep_count("Tool call validation failed", b_logs)

# ---------- scoring ----------
W = {k: w for k, _, w, _ in CRITERIA}
def score(tid, weights=W):
    s = SCORES[tid]; known = {k: v for k, v in s.items() if v is not None}
    tw = sum(weights[k] for k in known); tot = sum(weights.values())
    val = sum(weights[k] * (v if v is not None else 2.5) for k, v in s.items()) / tot * 20
    return round(val, 1), round(100 * tw / tot)
PROFILES = {
 "Default (ours)": W,
 "Solo terminal hacker": {**W, "D": 3, "G": 20, "C": 8, "E": 15},
 "Team shipping PRs": {**W, "C": 30, "F": 20, "D": 10, "E": 5},
 "Remote / phone-first": {**W, "D": 30, "G": 5},
}
T = {t["id"]: t for t in TOOLS}
ranked = sorted(SCORED, key=lambda i: -score(i)[0])

# ---------- SVG helpers ----------
INK = "#1a1a1a"; ACC = "#b4441c"; MUT = "#8a8577"; GRID = "#e4dfd3"
def hbar(rows, unit="", w=640, maxv=None, fmt="{:.1f}", accent_first=False, note=None):
    rh = 26; lw = 170; h = rh * len(rows) + 30; mx = maxv or max(v for _, v in rows if v is not None) * 1.12
    o = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img">']
    for gx in range(0, 5):
        x = lw + (w - lw - 60) * gx / 4; o.append(f'<line x1="{x:.0f}" y1="4" x2="{x:.0f}" y2="{h-22}" stroke="{GRID}"/>')
        o.append(f'<text x="{x:.0f}" y="{h-6}" class="ax">{fmt.format(mx*gx/4)}{unit}</text>')
    for i, (lab, v) in enumerate(rows):
        y = 6 + i * rh; o.append(f'<text x="{lw-8}" y="{y+15}" text-anchor="end" class="lb">{esc(lab)}</text>')
        if v is None: o.append(f'<text x="{lw+4}" y="{y+15}" class="na">not measured</text>'); continue
        bw = (w - lw - 60) * v / mx; c = ACC if (accent_first and i == 0) else INK
        o.append(f'<rect x="{lw}" y="{y+4}" width="{bw:.1f}" height="15" fill="{c}"/>')
        o.append(f'<text x="{lw+bw+5:.1f}" y="{y+16}" class="vl">{fmt.format(v)}{unit}</text>')
    o.append("</svg>"); s = "".join(o)
    return s + (f'<p class="cap">{note}</p>' if note else "")
def line_chart(series, w=640, h=220, ylab="MB"):
    pad = 46; allx = [x for _, pts in series for x, _ in pts]; ally = [y for _, pts in series for _, y in pts]
    mx, my = max(allx), max(ally) * 1.1
    o = [f'<svg viewBox="0 0 {w} {h}" class="chart">']
    for g in range(5):
        y = h - pad + -(h - 2 * pad + 10) * g / 4 + 0; val = my * g / 4
        o.append(f'<line x1="{pad}" y1="{y:.0f}" x2="{w-10}" y2="{y:.0f}" stroke="{GRID}"/><text x="{pad-6}" y="{y+4:.0f}" text-anchor="end" class="ax">{val:.0f}</text>')
    cols = [ACC, INK, MUT]
    for si, (name, pts) in enumerate(series):
        P = " ".join(f"{pad+(w-pad-10)*x/mx:.1f},{h-pad-(h-2*pad+10)*y/my:.1f}" for x, y in pts)
        o.append(f'<polyline points="{P}" fill="none" stroke="{cols[si]}" stroke-width="1.8"/>')
        o.append(f'<text x="{w-12}" y="{18+16*si}" text-anchor="end" class="lb" fill="{cols[si]}">{esc(name)}</text>')
    o.append(f'<text x="{pad}" y="{h-12}" class="ax">0 s</text><text x="{w-10}" y="{h-12}" text-anchor="end" class="ax">{mx:.0f} s</text><text x="8" y="16" class="ax">{ylab}</text></svg>')
    return "".join(o)
def series(f):
    return [(float(r["t_s"]), float(r["match_rss_mb"])) for r in csv.DictReader(open(f))]

# ---------- tables ----------
def table(head, rows, cls=""):
    o = [f'<table class="{cls}"><thead><tr>' + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead><tbody>"]
    for r in rows: o.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    return "".join(o) + "</tbody></table>"
def mark(v):
    if v in (None, "unknown"): return '<span class="unk">unknown</span>'
    s = esc(str(v)); return s.replace("sec:", '<span class="sec">secondary</span>')
def repo_link(t):
    if not t["repo"]: return '<span class="unk">closed source</span>'
    r = t["repo"].split(" ")[0]; return f'<a href="https://github.com/{r}">{esc(t["repo"])}</a>'
def ghfield(t, k):
    if not t["repo"]: return None
    r = t["repo"].split(" ")[0].replace("coder/mux", "coder/mux").replace("sst/opencode", "anomalyco/opencode")
    return gh["repos"].get(r, {}).get(k)
def cadence(t):
    r = t["repo"].split(" ")[0] if t["repo"] else None; g = gh["repos"].get(r) if r else None
    if not g or not g["oldest_of_those"] or not g["releases_in_last_30_returned"]: return None
    a = datetime.datetime.fromisoformat(g["oldest_of_those"].replace("Z", "+00:00")); b = datetime.datetime.fromisoformat(gh["snapshot_utc"][:19] + "+00:00")
    days = max(1, (b - a).days); n = g["releases_in_last_30_returned"]
    return f"{n} in {days} d"

matrix_cols = [("name","Tool"),("group","Category"),("url","Official URL"),("repo","Repo"),("license","License"),("oss","Open source"),("price","Pricing"),("platforms","Platforms"),("agents","Supported agents"),("parallel","Parallelism model"),("isolation","Isolation"),("review","Diff review / merge / PR"),("remote","Remote / mobile / cloud"),("mcp","MCP"),("cost","Cost / token visibility"),("models","Model choice"),("setup","Setup"),("hands_on","Hands-on status (this box)"),("bugs","Known issues / caveats"),("notes","Notes")]
# CSV
with open(B + "/matrix.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow([c for _, c in matrix_cols] + ["GitHub stars", "Open issues+PRs", "Latest release", "Latest release date (UTC)", "Releases (last 30 listed)", "Score /100", "Score evidence coverage %"])
    for t in TOOLS:
        sc = score(t["id"]) if t["id"] in SCORES else ("", "")
        w.writerow([t.get(k) or "" if t.get(k) != U else "unknown" for k, _ in matrix_cols] + [ghfield(t, "stars") or "", ghfield(t, "open_issues_and_prs") or "", ghfield(t, "latest_release") or "", ghfield(t, "latest_release_date") or "", cadence(t) or "", sc[0], sc[1]])
import shutil; shutil.copy(B + "/matrix.csv", R + "/matrix.csv")

# ---------- HTML ----------
img = lambda n: "data:image/jpeg;base64," + base64.b64encode(open(f"{R}/img/{n}.jpg", "rb").read()).decode()
CSS = """
:root{--paper:#f6f3ec;--ink:#1a1a1a;--mut:#6f6a5e;--rule:#d9d3c4;--acc:#b4441c;--card:#fffdf8}
*{box-sizing:border-box}html{background:var(--paper)}body{margin:0;color:var(--ink);font:16px/1.6 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:56px 40px 90px}
header.mast{border-bottom:3px double var(--ink);padding-bottom:22px;margin-bottom:34px}
.kicker{font:600 11.5px/1 ui-monospace,"SF Mono",Menlo,Consolas,monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--acc)}
h1{font-size:50px;line-height:1.05;margin:14px 0 14px;font-weight:600;letter-spacing:-.01em;max-width:900px}
.dek{font-size:20px;color:#3a3833;max-width:820px;margin:0}
.byline{margin-top:18px;font:12.5px/1.5 ui-monospace,Menlo,monospace;color:var(--mut)}
h2{font-size:30px;margin:62px 0 6px;font-weight:600;border-top:1px solid var(--ink);padding-top:16px}
h2 .n{font:600 13px ui-monospace,Menlo,monospace;color:var(--acc);margin-right:10px;vertical-align:middle}
h3{font-size:20px;margin:30px 0 6px}
p{max-width:780px}.lede{font-size:18.5px}
a{color:var(--ink);text-decoration-color:var(--acc);text-underline-offset:2px}
table{border-collapse:collapse;width:100%;margin:14px 0 8px;font:13px/1.45 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;background:var(--card)}
th{text-align:left;font:600 10.5px/1.3 ui-monospace,Menlo,monospace;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);border-bottom:1.5px solid var(--ink);padding:8px 8px;vertical-align:bottom}
td{border-bottom:1px solid var(--rule);padding:7px 8px;vertical-align:top}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;font-family:ui-monospace,Menlo,monospace;font-size:12.5px}
.matrix{font-size:12px}.matrix td:first-child{font-weight:600;white-space:nowrap}
.scroll{overflow-x:auto;border:1px solid var(--rule)}
.unk{color:#a39d8d;font-style:italic}.sec{font:600 9.5px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.06em;color:var(--acc);border:1px solid var(--acc);padding:0 3px;margin-right:4px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:34px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.stat{border-top:2px solid var(--ink);padding-top:10px}.stat b{display:block;font-size:34px;line-height:1.1;font-weight:600}.stat span{font:12px/1.4 ui-monospace,Menlo,monospace;color:var(--mut)}
.chart{width:100%;height:auto;background:var(--card);border:1px solid var(--rule)}
.chart .lb{font:12px -apple-system,Helvetica,Arial,sans-serif;fill:var(--ink)}.chart .ax{font:10px ui-monospace,Menlo,monospace;fill:#8a8577}.chart .vl{font:11px ui-monospace,Menlo,monospace;fill:var(--ink)}.chart .na{font:italic 11px Georgia;fill:#a39d8d}
.cap{font:12.5px/1.45 -apple-system,Helvetica,Arial,sans-serif;color:var(--mut);margin-top:6px}
.callout{border-left:3px solid var(--acc);padding:4px 0 4px 18px;margin:22px 0;max-width:820px}
.tool{border-top:1px solid var(--ink);padding-top:14px;margin-top:30px;display:grid;grid-template-columns:280px 1fr;gap:28px}
.tool h3{margin:0 0 4px}.meta{font:12px/1.6 ui-monospace,Menlo,monospace;color:var(--mut)}.meta a{color:var(--mut)}
.shot{width:100%;border:1px solid var(--rule);margin-top:10px}
.pill{display:inline-block;font:600 10.5px ui-monospace,monospace;letter-spacing:.05em;text-transform:uppercase;border:1px solid var(--ink);padding:1px 6px;margin:6px 6px 0 0}
.pill.ok{background:var(--ink);color:var(--paper)}.pill.no{border-color:#a39d8d;color:#8a8577}
ul.tight{margin:6px 0;padding-left:18px}ul.tight li{margin:3px 0}
.score{font:600 15px ui-monospace,monospace}
.verdict{display:grid;grid-template-columns:240px 1fr;border-bottom:1px solid var(--rule);padding:12px 0;gap:22px}.verdict b{font-size:17px}
footer{margin-top:70px;border-top:3px double var(--ink);padding-top:16px;font:12px ui-monospace,Menlo,monospace;color:var(--mut)}
code{font:12.5px ui-monospace,Menlo,monospace;background:#ece7db;padding:1px 4px}
.toc{columns:3;font:13px/1.9 -apple-system,Helvetica,Arial,sans-serif;margin:8px 0 0;padding:0;list-style:none}
"""
H = []; add = H.append
add(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Agent orchestrators for coding agents: a hands-on benchmark (Oct 2026)</title><style>{CSS}</style></head><body><div class='wrap'>")
add(f"""<header class='mast'><div class='kicker'>Field report · Coding-agent orchestrators · {snap_day}</div>
<h1>Who should run your fleet of coding agents?</h1>
<p class='dek'>A landscape of {len(TOOLS)} tools that run Claude Code, Codex and friends in parallel, a {len(CRITERIA)}-part scored rubric, and a hands-on benchmark on a Linux box where every number comes from a logged run.</p>
<div class='byline'>Snapshot: GitHub API {gh['snapshot_utc'][:16]} UTC · Box: Linux x86_64, 8 vCPU, 16 GB, no Docker, no authenticated agent CLIs · Raw logs: <code>runs/</code></div></header>""")
add("<ul class='toc'>" + "".join(f"<li><a href='#{a}'>{b}</a></li>" for a, b in [("tldr","Top line"),("method","Methodology"),("landscape","Landscape"),("matrix","Feature matrix"),("rubric","Scored rubric"),("hands","Hands-on results"),("deep","Per-tool deep dives"),("verdicts","Verdicts by use case"),("gaps","What we couldn't test"),("sources","Sources")]) + "</ul>")

# TL;DR
cs_l = [r["launch"] for r in lane["Claude Squad"]]; or_l = [r["launch"] for r in lane["Orca (orca serve CLI)"]]
add("<h2 id='tldr'><span class='n'>01</span>Top line</h2>")
add(f"""<div class='grid3'>
<div class='stat'><b>{len(TOOLS)}</b><span>tools verified to exist ({len(SCORED)} scored orchestrators, {len(TOOLS)-len(SCORED)} adjacent, first-party or status-changed)</span></div>
<div class='stat'><b>{sum(1 for g in gui.values() if g['alive_after_12s'])+1+1+1}</b><span>tools installed and launched on this Linux box (8 desktop apps under Xvfb, T3 Code server, Vibe Kanban, Claude Squad)</span></div>
<div class='stat'><b>2</b><span>orchestrators driven end-to-end through the 6-task suite: Claude Squad (TUI via tmux) and Orca (headless CLI). Both 18/18 verified over 3 logged runs</span></div>
</div>""")
add(f"""<div class='callout'><p><b>Our pick for most people on Linux or Windows: Orca</b>, if you want one open-source tool you can script and also click through. It was the only GUI orchestrator we could drive end-to-end without an account. It has a headless runtime (<code>orca serve</code>, ready in {min(orca_ready):.1f} to {max(orca_ready):.1f} s), launched 6 worktree-isolated agents concurrently in {min(or_l):.1f} to {max(or_l):.1f} s, and kept its terminals through 3 server restarts. The cost is memory: about 1.1 GB peak, against roughly 0.1 GB for Claude Squad.</p>
<p><b>T3 Code</b> has the deepest documented feature set: event-sourced orchestration, cross-harness <code>delegate_task</code>, an MCP for agents, a PR flow and real remote/mobile clients. Its server booted headless in {t3['ready_s']} s, but we could not run an agent session through it here. <b>Synara</b> is close behind on features and is MIT, but it is a smaller, self-described early-stage project. <b>Claude Squad</b> is still the lightest and most scriptable choice if you live in a terminal. <b>Conductor</b> is the review-UX reference on a Mac, and we could not test it.</p>
<p><b>Real-model runs were not possible here.</b> No Claude, Codex or Cursor login existed on the box. The one available key, a Groq free tier, caps a model at 7,000 to 8,000 tokens per minute, and a single opencode request was 7.3k to 8.6k tokens. Across {len(lb)} task attempts, 0 passed verification (error lines in the logs: {n_rate} rate-limit, {n_large} request-too-large, {n_schema} tool-schema). So the task-success numbers below measure <i>orchestrator mechanics</i> with a deterministic stub agent. They do not measure model quality.</p></div>""")

# Methodology
add("<h2 id='method'><span class='n'>02</span>Methodology</h2>")
add("""<p class='lede'>We split the work into three layers so that no number rests on something we did not observe.</p>
<h3>1 · Landscape verification</h3><p>A tool counts as verified when we found an official site or repository. GitHub stars, licenses, open issue counts and release dates come from one GitHub API snapshot (<code>data/gh_snapshot.json</code>). Claims that only appear in third-party roundups are tagged <span class='sec'>secondary</span>. One of those roundups was written by a competitor's author, who disclosed it. Anything we could not confirm says <span class='unk'>unknown</span>. X posts were read with the X API and are cited by URL.</p>
<h3>2 · Fixture and task suite</h3><p>The fixture is <code>fixture/repo</code>, a tiny Python package (<code>shelf</code>) with a 3-test smoke suite. It has six tasks (<code>fixture/tasks.json</code>), each checked by a hidden verifier (<code>fixture/verify</code>) that runs on a copy of the agent's worktree. A task passes only if its hidden checks <i>and</i> the existing tests pass.</p>
<table><thead><tr><th>Task</th><th>Kind</th><th>Pass condition</th></tr></thead><tbody>
<tr><td>t1</td><td>Bug fix</td><td>paginate() is 1-indexed and page_count() rounds up. 5 hidden assertions</td></tr>
<tr><td>t2</td><td>Feature</td><td>New shelf/slug.py slugify(). 6 hidden cases incl. max_len edge</td></tr>
<tr><td>t3</td><td>Refactor</td><td>Byte-identical output, and the column formatting appears only once in source</td></tr>
<tr><td>t4</td><td>Test writing</td><td>Agent's tests pass on the real code and catch all 3 seeded mutants</td></tr>
<tr><td>t5a / t5b</td><td>Conflicting edits</td><td>Two agents edit load_config() in parallel. Each passes alone; merging both must conflict</td></tr></tbody></table>
<p>We self-tested the verifiers before any run: all 6 fail on the base repo and all 6 pass on the reference solutions (<code>fixture/ref</code>). Merging t5a then t5b produces a real conflict in <code>shelf/config.py</code>.</p>
<h3>3 · Two benchmark lanes</h3>
<p><b>Lane A, orchestrator mechanics.</b> Each orchestrator launches <code>harness/benchagent.py</code>, a deterministic stub "agent CLI" (it is not an LLM). The stub reads the prompt, waits 10 s to simulate work, then writes the reference solution. It can be told to SIGKILL itself halfway (<code>STUB_CRASH</code>). This isolates what the orchestrator controls: session launch latency, worktree creation, concurrency, isolation, crash containment, restart recovery, branch output and footprint. Claude Squad was driven by sending real keystrokes to its TUI through tmux (<code>harness/cs_run.py</code>). Orca was driven through its own CLI against <code>orca serve</code> (<code>harness/orca_run.py</code>). The baseline is plain <code>git worktree</code> plus parallel processes (<code>harness/baseline_run.py</code>).</p>
<p><b>Lane B, real model.</b> The same suite ran with <code>opencode run</code> on the only usable model path (Groq free tier), through the plain-worktree harness. Its purpose was to find out whether an end-to-end run with a real model is possible on this box at all.</p>
<p><b>Startup probes.</b> Every installable GUI ran from its AppImage on Xvfb with a fresh HOME (<code>harness/gui_probe.py</code>). We recorded time to first visible X window, process-tree RSS after 12 s idle, and a screenshot. Server tools were probed by time-to-port (<code>harness/probe.py</code>).</p>
<p><b>Resources.</b> <code>harness/sampler.py</code> sampled once per second the summed RSS of processes matching each tool, plus system CPU. System CPU is noisy because other agents share this box, so we report only per-tool RSS.</p>""")

# Landscape
add("<h2 id='landscape'><span class='n'>03</span>Landscape: what exists, verified</h2>")
rows = []
for t in TOOLS:
    rows.append([f"<b>{esc(t['name'])}</b><br><span class='meta'>{esc(t['maker'])}</span>", esc(t["group"]), f"<a href='{esc(t['url'])}'>{esc(t['url'].split('//')[1].rstrip('/'))}</a>", repo_link(t), mark(t["license"]),
      f"<span class='num'>{ghfield(t,'stars'):,}</span>" if ghfield(t, "stars") else "–", esc(ghfield(t, "latest_release") or "–") + ("<br><span class='meta'>" + (ghfield(t, "latest_release_date") or "")[:10] + "</span>" if ghfield(t, "latest_release_date") else ""), cadence(t) or "–", mark(t["price"])])
add("<div class='scroll'>" + table(["Tool", "Category", "Official URL", "Repo", "License", "Stars", "Latest release", "Release cadence", "Pricing"], rows, "matrix") + "</div>")
add(f"<p class='cap'>Release cadence = how many of the last 30 releases GitHub lists, over how many days (this includes nightly/canary tags where a project publishes them). Stars are not audited. Orca's ~98k stars in seven months is an outlier, and we did not try to check how they were gained. Also mentioned in sources but not verified or scored: {esc('; '.join(SECONDARY_MENTIONS))}.</p>")
add("""<div class='callout'><p><b>Identity checks requested in the brief.</b> <b>T3 Code</b> is Theo Browne's (t3.gg) project at pingdotgg/t3code, MIT, site t3.codes. <b>Synara</b> is Emanuele Di Pietro's MIT desktop app at trysynara.com. <b>Orca</b> is Stably AI's MIT app at onorca.dev. <b>David Ondrej's tool is Cloudroom</b> (cloudroom.dev): an Apache-2.0 Rust runtime, <code>cloudroom-core</code>, plus a desktop GUI, <code>cloudroom-gui</code>, that moves a running Claude Code, Codex or Pi session from your laptop to a cloud VM. He confirmed on X on Oct 19, 2026 that it is generally available. His separate <code>davidondrej/skills</code> repo holds agent skills (subagents, worktrees, goal loops). It is not an orchestrator app.</p></div>""")

# Matrix
add("<h2 id='matrix'><span class='n'>04</span>Feature matrix</h2><p>Every dimension the brief asked for. The same data is in <code>matrix.csv</code>. Scroll sideways.</p>")
rows = [[esc(t["name"])] + [mark(t.get(k)) for k, _ in matrix_cols[6:]] for t in TOOLS]
add("<div class='scroll'>" + table([c for _, c in matrix_cols[:1]] + [c for _, c in matrix_cols[6:]], rows, "matrix") + "</div>")

# Rubric
add("<h2 id='rubric'><span class='n'>05</span>Scored rubric</h2>")
add("<p>Each criterion is scored 0 to 5 and weighted to a 100-point total. If we had no evidence for a criterion, it scores a neutral <b>2.5</b>. This deliberately pulls thinly documented tools toward the middle instead of rewarding them for what we could not see. The <b>coverage</b> column shows how much of the weight rests on real evidence. Treat low-coverage scores as provisional. The scores are our judgement from the evidence on this page. They are not measurements.</p>")
add(table(["", "Criterion", "Weight", "What a 5 means"], [[k, esc(l), f"<span class='num'>{w}</span>", esc(d)] for k, l, w, d in CRITERIA]))
add("<p class='cap'>Why these weights: agent breadth, isolation, review/merge flow and maturity carry 15 each because they decide whether a fleet stays productive past day one. Reach and openness carry 10 each. Measured Linux friction carries 10 because it is the only criterion grounded in our own runs. Pricing and docs carry 5 each because nearly every tool here is free with your own subscription, so pricing barely separates them. One bias to note: tools we could exercise (Orca, Claude Squad) have measured friction scores, while untestable ones get judged or neutral values. Orca's lead over T3 Code comes mostly from that criterion.</p>")
rows = []
for i in ranked:
    s, cov = score(i); sc = SCORES[i]
    rows.append([f"<b>{esc(T[i]['name'])}</b>"] + [f"<span class='num'>{sc[k] if sc[k] is not None else '·'}</span>" for k, *_ in CRITERIA] + [f"<span class='score'>{s}</span>", f"<span class='num'>{cov}%</span>", esc(WHY[i])])
add("<div class='scroll'>" + table(["Tool"] + [k for k, *_ in CRITERIA] + ["Score", "Coverage", "Why"], rows, "matrix") + "</div>")
add(hbar([(T[i]["name"], score(i)[0]) for i in ranked], maxv=100, fmt="{:.0f}", accent_first=True, note="Weighted score out of 100 with our default weights. '·' in the table means no evidence (scored as a neutral 2.5)."))
add("<h3>Sensitivity: does the ranking survive other weightings?</h3>")
prow = []
for pn, pw in PROFILES.items():
    order = sorted(SCORED, key=lambda i: -score(i, pw)[0])[:5]
    prow.append([f"<b>{esc(pn)}</b>", ", ".join(f"{esc(T[i]['name'])} ({score(i,pw)[0]})" for i in order)])
add(table(["Weight profile", "Top 5"], prow))
add("<p class='cap'>Profiles: Solo terminal hacker = friction 20, openness 15, review 8, reach 3. Team shipping PRs = review 30, maturity 20. Remote/phone-first = reach 30, friction 5. Unlisted criteria keep their default weight.</p>")

# Hands-on
add("<h2 id='hands'><span class='n'>06</span>Hands-on results</h2>")
add("<h3>6.1 · Install and first launch on Linux</h3>")
rows = []
order = ["orca", "synara", "superset", "emdash", "openchamber", "paseo", "cloudroom-gui", "mux"]
names = {"orca": "Orca 1.4.230", "synara": "Synara 1.0.7", "superset": "Superset 1.39.0", "emdash": "Emdash 1.2.8", "openchamber": "OpenChamber 2.5.0", "paseo": "Paseo 0.12.0", "cloudroom-gui": "Cloudroom GUI v110-beta", "mux": "Mux/Xum 0.31.0"}
gate = {"orca": "none (agent picker; detected OpenCode)", "synara": "none ('No account')", "superset": "<b>GitHub/Google sign-in required</b>", "emdash": "GitHub connect, skippable", "openchamber": "none", "paseo": "none", "cloudroom-gui": "none seen in 12 s", "mux": "gateway login offered, skippable"}
for k in order:
    g = gui[k]; rows.append([names[k], f"<span class='num'>{g['first_window_s']}</span>", f"<span class='num'>{g['rss_mb_tree']:,}</span>", f"<span class='num'>{g['procs']}</span>", gate[k]])
rows.append(["Realm 2.5.0*", f"<span class='num'>{realm_gui['first_window_s']}</span>", f"<span class='num'>{realm_gui['rss_mb_tree']:,}</span>", f"<span class='num'>{realm_gui['procs']}</span>", "none (agent picker; sign-in optional)"])
rows.append(["T3 Code 0.1.0 server (<code>t3 serve</code>)", f"<span class='num'>{t3['ready_s']}</span> (port open)", f"<span class='num'>{t3['idle_rss_mb']}</span>", f"<span class='num'>{t3['procs']}</span>", "pairing token printed (local)"])
rows.append(["Vibe Kanban 0.1.44 (<code>npx</code>, cold)", "about 10 (port open, incl. 49.9 MB download)", "about 684", "–", "none; analytics on by default"])
rows.append(["Claude Squad 1.0.20", f"<span class='num'>{cs_one['ui_ready_s']}</span> (TUI drawn)", f"{min(r['rss'] for r in lane['Claude Squad']):.0f} to {max(r['rss'] for r in lane['Claude Squad']):.0f} (peak under load)", "–", "none"])
add(table(["Tool", "Time to UI (s)", "RSS (MB)", "Procs", "First-run gate"], rows))
REALM_GUI_NOTE = (f"* Realm: author-run on {RUNNER}, the median of 3 launches after one that was not counted. Orca 1.4.230 on the same runner, "
                  f"same probe: {orca_gui_same['first_window_s']} s, {orca_gui_same['rss_mb_tree']:,} MB. Logs: runs/F-realm/gui/, runs/F-orca-same-runner/gui/.")
add(f"<p class='cap'>{esc(REALM_GUI_NOTE)}</p>")
add("<div class='grid2'>" + hbar([(names[k], gui[k]["first_window_s"]) for k in order], unit=" s", note="Time from AppImage launch to first visible window (Xvfb, fresh HOME, one run each).") + hbar([(names[k], gui[k]["rss_mb_tree"]) for k in sorted(order, key=lambda k: gui[k]["rss_mb_tree"])], unit="", fmt="{:,.0f}", note="Process-tree RSS in MB after 12 s idle. Emdash ran 23 processes.") + "</div>")
add("<p class='cap'>Downloads: 8 release artifacts (about 1.9 GB total) came down in 14.6 s with <code>gh release download</code>. Synara's AppImage and server tarball took a further 2.3 s. Other install timings: opencode via npm 6.4 s, the Claude Squad binary 0.25 s, the T3 Code server tarball 3.0 s, extracting Orca's AppImage 2.3 s. Logs: <code>runs/00-setup/</code>.</p>")
add("<div class='grid3'>" + "".join(f"<figure style='margin:0'><img class='shot' src='{img(k)}' alt='{names[k]} first screen'><figcaption class='cap'>{names[k]}: first screen on Linux.</figcaption></figure>" for k in ["orca", "synara", "superset", "emdash", "paseo", "openchamber"]) + "</div>")

add("<h3>6.2 · Lane A: orchestrator mechanics (stub agent, 6 parallel tasks)</h3>")
rows = []
rows.append(["Baseline: plain git worktree + 6 processes", "1", f"<span class='num'>{base['_worktree_setup_s']}</span> (6 worktrees)", "–", f"<span class='num'>{base['_total_wall_s']}</span>", f"<span class='num'>{sum(1 for k,v in base.items() if not k.startswith('_') and v['verified'])}/6</span>", "–"])
for tool, runs in lane.items():
    one = {"cs": cs_one, "orca": orca_one, "realm": realm_one}[LANE_PRE[tool]]
    rows.append([tool, "3", f"<span class='num'>{min(r['launch'] for r in runs):.2f} to {max(r['launch'] for r in runs):.2f}</span>", f"<span class='num'>{(one['first_agent_running_s'] if 'Squad' in tool else min(v['since_start_s'] for v in one['sessions'].values())):.2f}</span>", f"<span class='num'>{st.mean(r['total'] for r in runs):.1f}</span>", f"<span class='num'>{sum(r['verified'] for r in runs)}/18</span>", f"<span class='num'>{min(r['rss'] for r in runs):.0f} to {max(r['rss'] for r in runs):.0f}</span>"])
add(table(["Harness", "Runs", "All 6 launched (s)", "First agent running (s)", "Mean wall, launch to verified (s)", "Verified", "Peak RSS (MB)"], rows))
add(f"<p class='cap'>{esc(REALM_NOTE)}</p>")
re_l = lane["Realm (realm serve CLI)*"]
SAME = [("First window, AppImage on Xvfb (s)", realm_gui["first_window_s"], orca_gui_same["first_window_s"]),
        ("Process-tree RSS 12 s later (MB)", realm_gui["rss_mb_tree"], orca_gui_same["rss_mb_tree"]),
        ("Headless server ready (s)", span(realm_ready), span(orca_same_ready)),
        ("All 6 launched (s)", span([r["launch"] for r in re_l]), span([d["all_launched_s"] for d in orca_same])),
        ("Mean wall, launch to verified (s)", f"{st.mean(r['total'] for r in re_l):.1f}", f"{st.mean(d['total_wall_s'] for d in orca_same):.1f}"),
        ("Verified", f"{sum(r['verified'] for r in re_l)}/18", f"{sum(sum(1 for v in d['sessions'].values() if v.get('verified')) for d in orca_same)}/18"),
        ("Peak RSS (MB)", span([r["rss"] for r in re_l], "{:.0f}"), span(orca_same_rss, "{:.0f}"))]
add(table(["Same GitHub runner, same job (author-run)", "Realm*", "Orca 1.4.230"], [[a, f"<span class='num'>{b}</span>", f"<span class='num'>{c}</span>"] for a, b, c in SAME]))
add(f"""<p class='cap'>How to read this: the stub "works" for 10 s, so about 10 s of every wall time is simulated work. Claude Squad creates sessions one at a time through a form. Our driver adds about 1.1 s of fixed keystroke delays per session, so roughly 6.6 s of its {min(cs_l):.1f} to {max(cs_l):.1f} s launch time is the driver, and Claude Squad's own cost is about 0.2 to 0.4 s per session. Orca's CLI accepted 6 concurrent <code>worktree create</code> calls (about 1.1 s each, in parallel), then a <code>terminal create</code> (about 0.34 s) each. Orca's peak RSS includes its runtime (orcad, a PTY daemon and the CLI processes). Claude Squad's includes tmux.</p>""")
add("<div class='grid2'>" + hbar([("Baseline (git worktree)", base["_total_wall_s"]), ("Orca CLI", st.mean(r["total"] for r in lane["Orca (orca serve CLI)"])), ("Claude Squad TUI", st.mean(r["total"] for r in lane["Claude Squad"])), ("Realm CLI*", st.mean(r["total"] for r in lane["Realm (realm serve CLI)*"]))], unit=" s", note="Mean wall time from start to all 6 tasks verified (10 s is simulated work).") +
    line_chart([("Orca run 1", series(f"{RUNS}/repeat/orca-res1.csv")), ("Claude Squad run 1", series(f"{RUNS}/repeat/cs-res1.csv"))], ylab="RSS MB") + "</div>")
add("<p class='cap' style='text-align:right'>Right: summed RSS of each tool's processes, sampled every second during run 1.</p>")

add("<h3>6.3 · Crash containment, restart recovery, worktrees and merges</h3>")
def crash_row(name, d):
    s = d["sessions"]; return [name, "t3 SIGKILLed at 5 s", f"{sum(1 for v in s.values() if v.get('verified'))}/5 others verified", "yes" if s["t3"]["partial_file"] else "no", "t3 not verified (expected)"]
add(table(["Tool", "Fault", "Other sessions", "Partial work kept in worktree", "Crashed task"], [crash_row("Claude Squad", cs_crash), crash_row("Orca", orca_crash), crash_row("Realm*", realm_crash)]))
add("""<ul class='tight'>
<li><b>Claude Squad restart.</b> We killed the whole tmux server under it and relaunched <code>cs</code>. All instances came back marked <i>paused</i> with their worktrees intact. The log says <code>tmux session for "t3" no longer exists; pausing instance so it can be resumed</code>, and the UI offered <code>r</code> to resume (<code>runs/C-claude-squad/restart-after-tmux-kill.txt</code>). In the TUI's text the crashed instance looked like the others. Only its diff count (+1,-0) gave it away. There is no explicit "crashed" label.</li>
<li><b>Orca restart.</b> We restarted <code>orca serve</code> 3 times. Every time the runtime was ready in """ + ", ".join(f"{x} s" for x in orca_ready) + """, and the managed terminals were still listed afterwards. Startup prints "terminals survive an orcad restart: yes". We did see 12 terminals listed for 6 worktrees after repeated remove-and-recreate cycles. We did not check whether those were stale.</li>
<li><b>Where worktrees go.</b> Claude Squad uses <code>~/.claude-squad/worktrees/&lt;prefix&gt;/&lt;name&gt;_&lt;hash&gt;</code> with branches <code>&lt;prefix&gt;/&lt;name&gt;</code>. Orca uses <code>~/orca/workspaces/&lt;repo&gt;/&lt;name&gt;</code> with a branch named after the task. Both left uncommitted changes in the worktree and committed nothing on their own during our runs.</li>
<li><b>Merge correctness.</b> We committed each tool's worktrees and merged the branches into main in task order with git, because neither tool merges locally in the paths we used. Results: """ + f"Claude Squad {sum(1 for m in cs_merge['merges'] if m['result']=='clean')}/6 clean, Orca {sum(1 for m in orca_merge['merges'] if m['result']=='clean')}/6 clean, Realm* {sum(1 for m in realm_merge['merges'] if m['result']=='clean')}/6 clean. The only conflict in each was t5b in <code>shelf/config.py</code>, the conflict we designed. After merging, t1 to t5a all still pass on the merged main for both tools. Neither tool warned that two sessions were editing the same function.</li></ul>")

add("<h3>6.4 · Lane B: real model (opencode + Groq free tier)</h3>")
add(table(["Model path", "Task", "Agent exit", "Wall (s)", "Verified"], [[esc(r["model"]), r["task"], esc(str(r["exit"])), f"<span class='num'>{r['wall'] if r['wall'] is not None else '–'}</span>", "pass" if r["ok"] else "fail"] for r in lb]))
add(f"""<p>Result: <b>0 of {len(lb)} attempts passed</b>. The logs explain why. Groq's free tier caps each model at 8,000 tokens per minute (7,000 input TPM for qwen3.8-27b, see <code>runs/00-setup/groq-limits.log</code>), and one opencode request with its system prompt and tool schemas was 7.3k to 8.6k tokens. Across the agent logs, the provider rejected requests for rate limits (<code>{n_rate}</code> error lines) and, much more often, because a single request was already over the per-minute cap (<code>{n_large}</code> error lines, mostly from opencode retrying). gpt-oss-120b also produced malformed tool calls (<code>{n_schema}</code> schema-validation error lines). gpt-oss-20b got partway through t1, correcting the start index, before it was cut off. Merging those branches was trivially clean only because they held no commits.</p><p>This is a limit of the model path we had, not of any orchestrator. It is also a practical warning: N parallel agents on one rate-limited key do not give you N times the throughput.</p>""")

# Deep dives
add("<h2 id='deep'><span class='n'>07</span>Per-tool deep dives</h2>")
DD = {
 "orca": ("Teams and solo builders on any OS who want a GUI they can also script.", ["Headless runtime and full CLI. We drove the whole suite without a display", "Concurrent worktree creation, crash isolation, terminals that survive restarts", "35+ agents, SSH remotes, mobile companion, MIT"], ["About 1.1 GB peak RSS for 6 tiny sessions", "Ships several builds a day and its orchestration layer is still experimental", "8.6k open issues+PRs, and a star count we cannot explain"]),
 "t3": ("Multi-harness power users, especially anyone mixing Claude and Codex subscriptions or driving agents from a phone.", ["Event-sourced orchestrator, durable queue, restart recovery (v0.1.0)", "delegate_task across providers, plus an MCP that lets agents manage threads", "One-click PR with draft and stacked PRs; web and mobile"], ["We could not run a session here: it controls agents that are installed and authenticated, and none were", "2.9k open issues+PRs; v0.1.0 is days old", "Users on X report the sidebar gets noisy at scale"]),
 "synara": ("Developers who want a T3-style workspace with a built-in browser for verification and a provider handoff inside one task.", ["10 runtimes incl. Droid, Devin and Pi", "Agent Gateway MCP for parent and child tasks", "No account, MIT, Linux AppImage"], ["Heavy at idle: 2.1 GB process tree", "Standalone server tarball would not install with npm", "Small team; the README itself says 'early-stage'"]),
 "cs": ("Terminal people, SSH boxes, CI-like scripting.", ["Single 4.8 MB binary, UI drawn in about 0.2 s, about 100 MB under load", "Any CLI via profiles; resumes cleanly after tmux dies", "Diff stats per session"], ["Profile config needed: -p alone was not picked up by the form in our run", "No PR creation, review comments or remote features", "Last release Aug 20, 2026"]),
 "cloudroom": ("People who want agents to keep running after the laptop lid closes, on infrastructure they own.", ["Teleport a running session to a VM with the same model and effort", "Apache-2.0 core and GUI, self-hostable", "Ships releases daily"], ["Core install needs root, systemd and a fresh Ubuntu 24.04 VM", "Review and PR flow unverified", "Public feud with T3 Code's author is noise to tune out"]),
 "conductor": ("Mac users who mainly review agent output.", ["Most consistently praised diff and PR flow (secondary sources)", "Cloud workspaces and multiplayer on Pro"], ["macOS only", "Closed source; $50/mo for cloud"]),
 "superset": ("Mac or Linux teams willing to sign in, who want automations and an SDK.", ["Very active (release on snapshot day)", "Claims 100+ parallel agents"], ["Sign-in wall at first launch", "Elastic License 2.0 is not OSI open source"]),
 "emdash": ("Cross-platform users who want issue-tracker-driven worktrees.", ["Apache-2.0, Win/mac/Linux", "SSH remotes"], ["3.9 GB idle footprint in our probe"]),
 "paseo": ("Phone-first users who want a daemon on their machine.", ["Pair a device, import sessions you started in a terminal, schedules", "Apache-2.0, light-ish at 852 MB"], ["Isolation and review model not verified"]),
 "vk": ("Kanban-minded users who accept community maintenance.", ["Boots from npx in seconds", "Worktree per attempt"], ["Vendor shut down in 2026; last release Apr 24", "Analytics on by default"]),
 "sculptor": ("Anyone who needs real sandboxing (containers).", ["Container per agent; pairing mode"], ["Docker required; narrow agent support; small community"]),
 "openchamber": ("OpenCode users who want a GUI and multi-model fan-out.", ["No-login, polished first run"], ["Tied to OpenCode"]),
 "mux": ("Coder users; not enough evidence to recommend more broadly.", ["Launched fine on Linux"], ["Rename to Xum; feature set unverified here"]),
 "realm": ("Anyone who wants every agent CLI in one window on a Mac or Linux, and anyone who wants to script parallel agents from a shell (`realm serve` + `realm run`, shipped inside the app).",
           [f"Headless server and CLI inside the app: six worktree-isolated sessions launched in {span([r['launch'] for r in lane['Realm (realm serve CLI)*']])} s, {span([r['rss'] for r in lane['Realm (realm serve CLI)*']], '{:.0f}')} MB peak for six; Orca on the same runner {span([d['all_launched_s'] for d in orca_same])} s and {span(orca_same_rss, '{:.0f}')} MB (author-run, see note)",
            f"Linux AppImage opens in {realm_gui['first_window_s']} s with {realm_gui['rss_mb_tree']:,} MB and no account wall (Orca on the same runner: {orca_gui_same['first_window_s']} s, {orca_gui_same['rss_mb_tree']:,} MB)",
            "Worktree plus port block per session, optional Seatbelt sandbox, crash isolation reported per session (signal and exit code)", "13 agent CLIs through Agent SDK, Codex app-server and one ACP adapter; ship-to-PR and PR review in app"],
           ["Young: about two months old, with few stars at the time of writing", "Linux and Windows builds are new (2.3), and the Linux numbers here are the author's own runs", "The iPhone app is a TestFlight beta"]),
}
shots = {"realm": "realm", "orca": "orca", "synara": "synara", "superset": "superset", "emdash": "emdash", "paseo": "paseo", "openchamber": "openchamber", "cloudroom": "cloudroom-gui", "mux": "mux"}
for i in ranked:
    t = T[i]; who, pros, cons = DD[i]; s, cov = score(i)
    tested = "ok" if i in ("orca", "cs", "realm") else ("" if i in ("t3", "synara", "superset", "emdash", "paseo", "vk", "openchamber", "mux", "cloudroom") else "no")
    tl = {"ok": "Driven end-to-end", "": "Installed / launched", "no": "Not testable here"}[tested]
    add(f"<div class='tool'><div><h3>{esc(t['name'])}</h3><div class='meta'>{esc(t['maker'])}<br><a href='{esc(t['url'])}'>{esc(t['url'])}</a><br>{repo_link(t)}<br>{esc(t['license'])}</div><span class='pill {tested}'>{tl}</span><span class='pill'>Score {s} · cov {cov}%</span>" + (f"<img class='shot' src='{img(shots[i])}' alt=''>" if i in shots else "") + "</div>")
    add(f"<div><p><b>Who it's for.</b> {esc(who)}</p><div class='grid2'><div><b>Strengths</b><ul class='tight'>" + "".join(f"<li>{esc(x)}</li>" for x in pros) + "</ul></div><div><b>Weaknesses</b><ul class='tight'>" + "".join(f"<li>{esc(x)}</li>" for x in cons) + "</ul></div></div>")
    add(f"<p class='cap'><b>Hands-on:</b> {esc(t['hands_on'])}<br><b>Caveats:</b> {mark(t['bugs'])} {esc(t['notes'])}</p></div></div>")
add("<h3>Adjacent, first-party and status-changed tools (not scored)</h3>")
add(table(["Tool", "Status", "Why not scored"], [[esc(T[i]["name"]), mark(T[i]["notes"] or T[i]["group"]), esc(T[i]["hands_on"])] for i in ["cursor", "codex", "ccdesk", "opencode", "warp", "amp", "crystal", "terragon", "omnara"]]))

# Verdicts
add("<h2 id='verdicts'><span class='n'>08</span>Verdicts by use case</h2>")
V = [("Linux or Windows, open source, scriptable", "Orca. The only GUI orchestrator we fully drove headless, and it is MIT."),
     ("Mixing Claude + Codex + Cursor subscriptions, remote/phone control", "T3 Code, with Synara as the MIT alternative that adds a built-in browser and an agent gateway. Both run your local CLIs, so you need them authenticated."),
     ("Terminal-only, SSH boxes, minimal footprint", "Claude Squad: about 100 MB, scriptable via tmux, recovers cleanly. Add your own PR tooling."),
     ("Mac, review-heavy workflow", "Conductor (by reputation; untested here). Open alternatives: T3 Code, Orca."),
     ("Agents that keep running with the laptop closed, self-hosted", "Cloudroom (core on your own VM), or T3 Code's headless server behind Tailscale."),
     ("Real sandboxing", "Sculptor (containers). Worktree tools isolate files, not processes, ports or credentials."),
     ("Kanban planning", "Vibe Kanban, only if you accept that it is community-maintained now."),
     ("You use one vendor only", "Its own app (Claude Code desktop, Codex in ChatGPT, Cursor Agents Window) may be enough.")]
add("".join(f"<div class='verdict'><b>{esc(a)}</b><div>{esc(b)}</div></div>" for a, b in V))

# Gaps
add("<h2 id='gaps'><span class='n'>09</span>What we couldn't test, and why</h2>")
G = [("Real-model task success for every tool", "No Claude/Codex/Cursor/Grok CLI was authenticated on the box. The only key (Groq free tier) cannot fit one opencode request per minute. We did not buy credits or sign up for anything."),
     ("T3 Code and Synara agent sessions", "Both orchestrate agent CLIs that are installed and authenticated; none were. We verified install and boot only. We could have pointed T3 at opencode+Groq, but that would hit the same rate wall."),
     ("Conductor, Claude Code desktop, Codex app", "macOS-only, or they need a vendor login."),
     ("Superset beyond the first screen", "Mandatory GitHub/Google sign-in. We did not create or link an account."),
     ("Cloudroom core", "The installer needs root, systemd and a fresh Ubuntu 24.04 VM. Running it would have changed a shared machine, so we did not."),
     ("Sculptor", "Needs Docker, which is not available."),
     ("Cursor, Warp Oz, Amp", "Account required; cloud execution."),
     ("Terragon, Omnara (old product)", "The service is shut down, or the product pivoted."),
     ("GUI diff/merge UX quality", "We captured first screens only. We did not click through each app's review flow, so review UX scores rest on vendor docs and secondary sources."),
     ("Token and cost tracking", "Needs real agent sessions; marked unknown or partial in the matrix."),
     ("Statistical power", "3 runs per lane-A harness and 1 run per startup probe on a shared VM. Treat differences under about 20% as noise.")]
add(table(["Gap", "Reason"], [[f"<b>{esc(a)}</b>", esc(b)] for a, b in G]))

add("<h2 id='sources'><span class='n'>10</span>Sources</h2><ul class='tight'>" + "".join(f"<li><a href='{esc(u)}'>{esc(n)}</a></li>" for n, u in SOURCES) + "</ul>")
add(f"<footer>Built {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} PT from raw logs by report/build.py · Fixture, harness and logs live under /workspace/orchestrator-bench · No CDN, no external assets.</footer></div></body></html>")
open(R + "/index.html", "w").write("".join(H))

# ---------- Markdown ----------
M = []; m = M.append
m(f"# Agent orchestrators for coding agents: a hands-on benchmark ({snap_day})\n")
m(f"Box: Linux x86_64, 8 vCPU, 16 GB, no Docker, no authenticated agent CLIs. GitHub snapshot {gh['snapshot_utc'][:16]} UTC. Every number comes from logs under `runs/`.\n")
m("## Top line\n")
m(f"- **Orca** is the only GUI orchestrator we drove end-to-end on Linux, headless via `orca serve` (ready in {min(orca_ready)} to {max(orca_ready)} s). It launched 6 worktree-isolated stub agents concurrently in {min(or_l):.2f} to {max(or_l):.2f} s and verified 18/18 over 3 runs, with about 1.1 GB peak RSS.")
m(f"- **Claude Squad** was driven through its TUI via tmux and also verified 18/18, at about 100 MB peak RSS. It restored sessions as paused and resumable after we killed tmux.")
m(f"- **T3 Code**'s server booted headless in {t3['ready_s']} s ({t3['idle_rss_mb']} MB idle). It has the richest documented feature set, but we ran no agent session through it.")
m(f"- Real-model lane: 0/{len(lb)} attempts passed. The only key was a Groq free tier (7 to 8k TPM) and one opencode request was 7.3 to 8.6k tokens ({n_rate} rate-limit, {n_large} too-large, {n_schema} tool-schema errors).\n")
m("## Methodology\n\nWe ran a fixture repo with 6 tasks (bug fix, feature, refactor, test-writing with mutant checks, and two conflicting edits) and hidden verifiers. The verifiers were self-tested first: all fail on the base repo, all pass on the reference solutions, and t5a+t5b really conflict. Lane A uses a deterministic stub agent to measure orchestrator mechanics. Lane B uses opencode with a real model. GUI apps were probed on Xvfb for time to first window, RSS and a screenshot.\n")
m("## Landscape\n\n| Tool | URL | Repo | License | Stars | Latest release | Pricing |\n|---|---|---|---|---|---|---|")
for t in TOOLS:
    m(f"| {t['name']} | {t['url']} | {t['repo'] or 'closed'} | {t['license']} | {ghfield(t,'stars') or '-'} | {(ghfield(t,'latest_release') or '-')} {(ghfield(t,'latest_release_date') or '')[:10]} | {t['price']} |")
m("\nDavid Ondrej's tool is **Cloudroom** (cloudroom.dev; davidondrej/cloudroom-core + cloudroom-gui, Apache-2.0).\n")
m("## Scored rubric\n\n| Criterion | Weight |\n|---|---|\n" + "\n".join(f"| {k} {l} | {w} |" for k, l, w, _ in CRITERIA))
m("\n| Tool | " + " | ".join(k for k, *_ in CRITERIA) + " | Score | Coverage |\n|---|" + "---|" * (len(CRITERIA) + 2))
for i in ranked:
    s, cov = score(i); m(f"| {T[i]['name']} | " + " | ".join(str(SCORES[i][k]) if SCORES[i][k] is not None else "·" for k, *_ in CRITERIA) + f" | {s} | {cov}% |")
m("\nScores are judgement from cited evidence. Criteria without evidence score a neutral 2.5; coverage shows how much weight a score rests on.\n")
m("## Hands-on\n\n### Launch probes\n\n| Tool | First window (s) | RSS MB | Gate |\n|---|---|---|---|")
for k in order: m(f"| {names[k]} | {gui[k]['first_window_s']} | {gui[k]['rss_mb_tree']} | {html.unescape(gate[k]).replace('<b>','').replace('</b>','')} |")
m(f"| Realm 2.5.0* | {realm_gui['first_window_s']} | {realm_gui['rss_mb_tree']} | none (agent picker; sign-in optional) |")
m(f"| T3 Code server | {t3['ready_s']} (port) | {t3['idle_rss_mb']} | none |\n")
m(REALM_GUI_NOTE + "\n")
m("### Lane A (stub agent, 6 parallel)\n\n| Harness | Runs | All launched (s) | Mean wall (s) | Verified | Peak RSS MB |\n|---|---|---|---|---|---|")
m(f"| Baseline git worktree | 1 | {base['_worktree_setup_s']} | {base['_total_wall_s']} | 6/6 | - |")
for tool, runs in lane.items():
    m(f"| {tool} | 3 | {min(r['launch'] for r in runs):.2f} to {max(r['launch'] for r in runs):.2f} | {st.mean(r['total'] for r in runs):.1f} | {sum(r['verified'] for r in runs)}/18 | {min(r['rss'] for r in runs):.0f} to {max(r['rss'] for r in runs):.0f} |")
m("\n" + REALM_NOTE)
m("\n| Same GitHub runner, same job (author-run) | Realm* | Orca 1.4.230 |\n|---|---|---|\n" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in SAME))
m("\nClaude Squad launch includes about 1.1 s per session of driver keystroke delays. Crash test (t3 SIGKILL): both tools kept the other 5 sessions verified and preserved the partial work. Merges done with git: 5/6 clean for both, with t5b conflicting in shelf/config.py as designed. Realm* matched both: 5/5 others verified with t3's partial work kept, and 5/6 clean merges.\n")
m("### Lane B (real model)\n\n| Model | Task | Exit | Wall s | Verified |\n|---|---|---|---|---|")
for r in lb: m(f"| {r['model']} | {r['task']} | {r['exit']} | {r['wall'] or '-'} | {'pass' if r['ok'] else 'fail'} |")
m("\n## Verdicts\n\n" + "\n".join(f"- **{a}**: {b}" for a, b in V))
m("\n## What we couldn't test\n\n" + "\n".join(f"- **{a}**: {b}" for a, b in G))
m("\n## Sources\n\n" + "\n".join(f"- [{n}]({u})" for n, u in SOURCES))
open(B + "/report.md", "w").write("\n".join(M) + "\n"); shutil.copy(B + "/report.md", R + "/report.md")
print("built", len("".join(H)) // 1024, "KB html;", "ranked:", [(T[i]['name'], score(i)) for i in ranked])
