# Agent orchestrator bench

A hands-on look at the apps that run several coding agents (Claude Code, Codex, Cursor, OpenCode and others) in parallel with worktrees, sessions and review. 22 tools were checked, 13 scored on a 9-part rubric, 2 driven end-to-end. Snapshot date: 2026-10-19.

**Live site:** https://arjunkshah12345-hash.github.io/agent-orchestrator-bench/

## Leaderboard

| # | Tool | Score /100 | Evidence coverage |
|---|---|---|---|
| 1 | Orca | 93.0 | 100% |
| 2 | T3 Code | 90.0 | 100% |
| 3 | Synara | 79.0 | 100% |
| 4 | Emdash | 74.5 | 95% |
| 5 | Paseo | 74.5 | 65% |
| 6 | OpenChamber | 74.0 | 80% |
| 7 | Superset | 72.5 | 95% |
| 8 | Cloudroom (David Ondrej) | 72.0 | 80% |
| 9 | Vibe Kanban | 69.0 | 100% |
| 10 | Claude Squad | 65.0 | 100% |
| 11 | Conductor | 62.5 | 85% |
| 12 | Sculptor | 60.0 | 90% |
| 13 | Mux (now Xum) | 58.5 | 55% |

Per-criterion scores, weights and a sensitivity check are in [report.md](report.md) and on the site.

## Methodology, honestly

- Scores are editorial judgement (0 to 5 per criterion, weighted to 100) built from vendor docs, repos, a GitHub snapshot and feature testing on one Linux box (8 vCPU, 16 GB, no Docker).
- Feature testing means launch probes on Xvfb and a deterministic **stub agent** driving 6 parallel tasks through Orca and Claude Squad, with hidden verifiers. That measures orchestration mechanics, not code quality.
- **There are no real-model runs in any score.** No Claude, Codex, Cursor or Grok agent CLI was logged in on the box. Nine attempts through opencode on a Groq free tier all failed on rate and token limits; they are logged in `runs/` and shown on the site as not scored.
- A criterion without evidence counts as a neutral 2.5, and the coverage column says how much weight a score rests on.

## Layout

- `site/`: the static site (HTML, CSS, JS, fonts) and its generator `site/build.py`
- `report/`: `tools_data.py` (curated data), `build.py` (original report builder), screenshots, draft X thread
- `report.md`, `matrix.csv`: the written report and the full feature matrix
- `data/gh_snapshot.json`: GitHub API snapshot
- `fixture/`: test repo, tasks, hidden verifiers, reference solutions
- `harness/`: stub agent and drivers
- `runs/`: raw logs and JSON behind every number

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
