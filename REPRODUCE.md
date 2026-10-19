# Reproduce this benchmark

This is a feature and orchestration benchmark, not a model leaderboard. The measured part is a stub-agent test of Orca and Claude Squad on Linux. Live site: https://arjunkshah12345-hash.github.io/agent-orchestrator-bench/reproduce.html

## Versions

| Component | Version | Evidence |
|---|---|---|
| Orca | v1.4.230 (Linux AppImage, extracted); headless runtime orcad 0.1.0+7a87e80a2a8a | `runs/F-orca/serve.log` |
| Claude Squad | v1.0.20 release binary (claude-squad version 1.0.20) | `runs/C-claude-squad/install.log` |
| T3 Code | v0.1.0 linux-x64 server tarball | `runs/D-t3code/probe.log` |
| opencode (Lane B agent) | 1.19.3 | `runs/00-setup/opencode-install.log` |
| GUI apps (launch probes) | Synara 1.0.7, Superset 1.39.0, Emdash 1.2.8, OpenChamber 2.5.0, Paseo 0.12.0, Cloudroom GUI v110-beta, Mux/Xum 0.31.0 | `runs/00-setup/gui-probes-summary.log` |
| Fixture repo | commit 377fb426b834ede261ddfe7e70a6301aeaf31b5e ("fixture base") | `fixture/repo` |
| Python / git / tmux | Python 3.13.5, git 2.47.3, tmux 3.5a | - |

Tools were installed from release binaries, so release tags and build ids are recorded, not source commits.

## Environment

- **OS:** Debian GNU/Linux 13 (trixie), kernel 6.12, x86_64
- **Hardware:** 8 vCPU, 16 GB RAM, no GPU, no Docker
- **Display:** Xvfb virtual display for GUI apps and orca serve
- **Accounts:** No authenticated agent CLI (Claude, Codex, Cursor, Grok). Nothing bought, no sign-ups.
- **GitHub snapshot:** data/gh_snapshot.json, 2026-10-19 17:25 UTC

## Fixture

`fixture/repo` (6 tasks in `fixture/tasks.json`), hidden verifiers in `fixture/verify`, reference solutions in `fixture/ref`. Stub agent: `harness/benchagent.py` (deterministic, not an LLM).

## Steps

1. Clone and check the fixture

```
git clone https://github.com/arjunkshah12345-hash/agent-orchestrator-bench.git && cd agent-orchestrator-bench
# verifiers must fail on the base repo and pass on the references
for t in t1 t2 t3 t4 t5a t5b; do python3 harness/verify.py fixture/repo $t; done
```

2. Baseline (plain git worktree + stub agent)

```
python3 harness/baseline_run.py A-baseline-stub 'env STUB_SLEEP=8 python3 harness/benchagent.py {prompt}'
```

3. Install the orchestrators

```
# Orca v1.4.230 AppImage from github.com/stablyai/orca/releases, extract to tools/orca-x
./orca-linux.AppImage --appimage-extract && mv squashfs-root tools/orca-x/
# Claude Squad v1.0.20 from github.com/smtg-ai/claude-squad/releases into tools/cs/claude-squad
```

4. Orca, 3 runs

```
Xvfb :90 &
HOME=/tmp/home-orca-cli DISPLAY=:90 tools/orca-x/squashfs-root/resources/bin/orca-ide serve &
python3 harness/orca_run.py   # repeat 3x; copy runs/F-orca/result.json + resources.csv per run
STUB_CRASH=t3 python3 harness/orca_run.py   # crash test
```

5. Claude Squad, 3 runs

```
python3 harness/cs_run.py   # drives the TUI through tmux; repeat 3x
STUB_CRASH=t3 python3 harness/cs_run.py
```

6. Merge check

```
python3 harness/merge_eval.py   # expects 5/6 clean, t5b conflicting in shelf/config.py
```

7. GUI launch probes

```
python3 harness/gui_probe.py <name> <path-to-AppImage>   # first window time + RSS on Xvfb
```

8. Rebuild the site from the logs

```
python3 site/build.py && python3 -m http.server -d site 8000
```

## Raw data

- `runs/repeat/`: Orca and Claude Squad, 3 runs each: run JSON + 1 s resource CSVs
- `runs/F-orca/`: Orca crash test, merge, serve readiness and restarts
- `runs/C-claude-squad/`: Claude Squad screens, crash test, tmux-kill recovery, merge
- `runs/A-baseline-stub/`: plain worktree baseline
- `runs/E-gui-*/`: GUI launch probes with screenshots
- `runs/D-t3code/`: T3 Code server probe
- `runs/B*/`: Lane B real-model attempts (all failed, not scored)
- `runs/R-real-round-DRYRUN-stub/`: real-agent harness plumbing check with the stub agent (not a result)
- `matrix.csv`: full feature matrix and assessment data
- `report/tools_data.py`: rubric, criterion scores and rationale
- `data/gh_snapshot.json`: GitHub API snapshot

## Real-agent round (ready, not yet run)

3 orchestrators (baseline worktree, Orca, Claude Squad) x 1 model x 3 tasks (t1, t2, t3) x 3 reps. Outputs `runs/R-real-round/results.csv`.

```
python3 harness/real/real_round.py \
  --agent-cmd 'claude -p {prompt} --model {model} --output-format json --dangerously-skip-permissions' \
  --model <one model id> --tools baseline,orca,cs --tasks t1,t2,t3 --reps 3
```

Plumbing check (stub agent, not a result): `python3 harness/real/real_round.py --dry-run`

What it needs:

- One authenticated agent CLI on the box, used for all 27 cells. For example Claude Code logged in with `claude login` (Claude subscription) or `ANTHROPIC_API_KEY` set; or Codex CLI with `codex login` / `OPENAI_API_KEY`; or opencode with a provider key whose rate limit fits one request (the Groq free tier at 7 to 8k tokens per minute does not: one opencode request was 7.3 to 8.6k tokens).
- `orca serve` running on an Xvfb display (step 4) and tmux for Claude Squad.
- Budget for 27 agent runs (3 tools x 3 tasks x 3 reps). Tokens are taken from the CLI's own JSON usage output; if a CLI prints none, tokens are recorded as empty, never estimated.
