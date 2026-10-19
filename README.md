# Agent orchestrator bench

A feature and orchestration benchmark (not a model leaderboard) of the apps that run several coding agents (Claude Code, Codex, Cursor, OpenCode and others) in parallel with worktrees, sessions and review. 22 tools were checked, 13 scored on a 9-part rubric, 2 driven end-to-end. Snapshot date: 2026-10-19.

**Live site:** https://arjunkshah12345-hash.github.io/agent-orchestrator-bench/

## Measured: stub-agent test on Linux (3 runs each)

There's no universal winner. Orca is faster to launch; Claude Squad is far lighter.

| | Orca | Claude Squad |
|---|---|---|
| Verified stub tasks | 18/18 | 18/18 |
| Six-agent launch (s) | 1.52 to 1.90 | 11.18 to 11.89 (includes about 1.1 s per session of our tmux driver delays) |
| Peak RSS (MB) | 1124 to 1140 (about 1.1 GB) | 102 to 118 |

The stub agent is a deterministic script, not an LLM. It measures the orchestrator, not code quality. Logs: `runs/repeat/`.

## Secondary research: weighted feature assessment

This is a weighted feature assessment from docs, repos and feature testing, not a measured performance leaderboard. Orca was run end-to-end with stub agents; T3 Code was not run through an equivalent session, so 93 vs 90 is not experimentally proven. Criteria without evidence are unranked; the range shows the score with them at 0 or at full marks, and the point score is the midpoint.

| # | Tool | Assessed /100 | Range | Doc coverage | Hands-on validation |
|---|---|---|---|---|---|
| 1 | Orca | 93.0 | 93.0 to 93.0 | 100% | Stub end-to-end |
| 2 | T3 Code | 90.0 | 90.0 to 90.0 | 100% | Launched |
| 3 | Synara | 79.0 | 79.0 to 79.0 | 100% | Launched |
| 4 | Emdash | 74.5 | 72.0 to 77.0 | 95% | Launched |
| 5 | Paseo | 74.5 | 57.0 to 92.0 | 65% | Launched |
| 6 | OpenChamber | 74.0 | 64.0 to 84.0 | 80% | Launched |
| 7 | Superset | 72.5 | 70.0 to 75.0 | 95% | Launched |
| 8 | Cloudroom (David Ondrej) | 72.0 | 62.0 to 82.0 | 80% | Launched |
| 9 | Vibe Kanban | 69.0 | 69.0 to 69.0 | 100% | Launched |
| 10 | Claude Squad | 65.0 | 65.0 to 65.0 | 100% | Stub end-to-end |
| 11 | Conductor | 62.5 | 55.0 to 70.0 | 85% | None |
| 12 | Sculptor | 60.0 | 55.0 to 65.0 | 90% | None |
| 13 | Mux (now Xum) | 58.5 | 36.0 to 81.0 | 55% | Launched |

Per-criterion scores, weights and a sensitivity check are in [report.md](report.md) and on the site.

## Methodology, honestly

- Scores are editorial judgement (0 to 5 per criterion, weighted to 100) built from vendor docs, repos, a GitHub snapshot and feature testing on one Linux box (8 vCPU, 16 GB, no Docker).
- Feature testing means launch probes on Xvfb and a deterministic **stub agent** driving 6 parallel tasks through Orca and Claude Squad, with hidden verifiers. That measures orchestration mechanics, not code quality.
- **There are no real-model runs in any score.** No Claude, Codex, Cursor or Grok agent CLI was logged in on the box. Nine attempts through opencode on a Groq free tier all failed on rate and token limits; they are logged in `runs/` and shown on the site as not scored.
- A criterion without evidence is unranked. Each tool shows a range (unranked criteria at 0 or at 5); the point score is the midpoint.
- A real-agent round (3 orchestrators x 1 model x 3 tasks x 3 reps) is ready in `harness/real/` but has not been run; see [REPRODUCE.md](REPRODUCE.md).

## Layout

- `site/`: the static site (HTML, CSS, JS, fonts) and its generator `site/build.py`
- `report/`: `tools_data.py` (curated data), `build.py` (original report builder), screenshots, draft X thread
- `report.md`, `matrix.csv`: the written report and the full feature matrix
- `data/gh_snapshot.json`: GitHub API snapshot
- `fixture/`: test repo, tasks, hidden verifiers, reference solutions
- `harness/`: stub agent and drivers
- `runs/`: raw logs and JSON behind every number

## Reproduce

See [REPRODUCE.md](REPRODUCE.md) or the live page: https://arjunkshah12345-hash.github.io/agent-orchestrator-bench/reproduce.html

## Rebuild

```
python3 site/build.py      # regenerates site/*.html and site/assets/data.js
python3 -m http.server -d site 8000
```

No dependencies beyond Python 3. The site needs no CDN.

## Credits

Charts use dither-kit-lite from the SuperCompress brand pack (MIT), a vanilla canvas port of [Tripwire dither-kit](https://www.tripwire.sh/dither-kit). See [site/assets/vendor/NOTICE.md](site/assets/vendor/NOTICE.md). Fonts: Host Grotesk and Geist Mono (SIL Open Font License).

## Not included

The downloaded third-party app binaries and AppImages used for testing (about 3.5 GB under `tools/`) are left out; get them from each vendor.

## License

MIT, see [LICENSE](LICENSE).
