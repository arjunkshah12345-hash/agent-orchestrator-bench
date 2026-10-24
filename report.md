# Agent orchestrators for coding agents: a hands-on benchmark (2026-10-19)

Box: Linux x86_64, 8 vCPU, 16 GB, no Docker, no authenticated agent CLIs. GitHub snapshot 2026-10-19T17:25 UTC. Every number comes from logs under `runs/`.

## Top line

- **Orca** is the only GUI orchestrator we drove end-to-end on Linux, headless via `orca serve` (ready in 2.79 to 3.06 s). It launched 6 worktree-isolated stub agents concurrently in 1.52 to 1.90 s and verified 18/18 over 3 runs, with about 1.1 GB peak RSS.
- **Claude Squad** was driven through its TUI via tmux and also verified 18/18, at about 100 MB peak RSS. It restored sessions as paused and resumable after we killed tmux.
- **T3 Code**'s server booted headless in 1.01 s (394 MB idle). It has the richest documented feature set, but we ran no agent session through it.
- Real-model lane: 0/9 attempts passed. The only key was a Groq free tier (7 to 8k TPM) and one opencode request was 7.3 to 8.6k tokens (3 rate-limit, 153 too-large, 3 tool-schema errors).

## Methodology

We ran a fixture repo with 6 tasks (bug fix, feature, refactor, test-writing with mutant checks, and two conflicting edits) and hidden verifiers. The verifiers were self-tested first: all fail on the base repo, all pass on the reference solutions, and t5a+t5b really conflict. Lane A uses a deterministic stub agent to measure orchestrator mechanics. Lane B uses opencode with a real model. GUI apps were probed on Xvfb for time to first window, RSS and a screenshot.

## Landscape

| Tool | URL | Repo | License | Stars | Latest release | Pricing |
|---|---|---|---|---|---|---|
| T3 Code | https://t3.codes | pingdotgg/t3code | MIT | 28576 | v0.1.0 2026-10-15 | Free, BYO subscriptions (site: 'doesn't resell tokens') |
| Synara | https://www.trysynara.com | Emanuele-web04/synara | MIT | 2126 | v1.0.7 2026-10-17 | Free; no account (install page). Maintainer seeking sponsorships (X, Oct 17 2026) |
| Orca | https://www.onorca.dev | stablyai/orca | MIT | 97922 | v1.4.230 2026-10-19 | Free |
| Cloudroom | https://www.cloudroom.dev | davidondrej/cloudroom-core (+ davidondrej/cloudroom-gui) | Apache-2.0 (core and GUI) | 906 | core-v0.1.65 2026-10-19 | Free, open source (maker's post); self-hostable core |
| Realm | https://realm.computer | 31Carlton7/realm | MIT (LICENSE added 2026-10-24, #221) | 116 | v2.5.0 2026-10-24 | Free; BYO subscriptions (each agent CLI signs in with your own account; no Realm account) |
| Conductor | https://www.conductor.build | closed | Proprietary | - | -  | Free local workspaces; Pro $50/mo (cloud, multiplayer, API, iPhone app); Teams $60/user/mo |
| Claude Squad | https://smtg-ai.github.io/claude-squad/ | smtg-ai/claude-squad | AGPL-3.0 | 8628 | v1.0.20 2026-08-20 | Free |
| Superset | https://superset.sh | superset-sh/superset | Elastic License 2.0 (source-available) | 15371 | desktop-v1.39.0 2026-10-19 | sec: Free for one user; Pro $20/user/mo |
| Emdash | https://emdash.com | generalaction/emdash | Apache-2.0 | 6028 | v1.2.8 2026-10-10 | Free (sec) |
| Paseo | https://paseo.sh | getpaseo/paseo | Apache-2.0 (LICENSE file; GitHub API shows 'Other') | 21421 | v0.12.0 2026-10-19 | Free |
| Vibe Kanban | https://www.vibekanban.com | BloopAI/vibe-kanban | Apache-2.0 | 28399 | v0.1.44-20260424091429 2026-04-24 | Free (paid subscriptions refunded at shutdown, sec) |
| Sculptor | https://imbue.com/product/sculptor/ | imbue-ai/sculptor | MIT (per GitHub API) | 240 | sculptor-v0.48.0 2026-09-21 | Free during beta; BYO Claude/OpenAI keys |
| OpenChamber | https://openchamber.dev | openchamber/openchamber | MIT | 11862 | v2.5.0 2026-10-19 | Free |
| Mux (now 'Xum') | https://xum.coder.com | coder/mux (redirects to coder/xum) | AGPL-3.0 | 2055 | v0.31.0 2026-10-09 | Free app; optional 'Xum Gateway' evaluation credits |
| Cursor (Agents Window) | https://cursor.com/docs/agent/agents-window | closed | Proprietary | - | -  | sec: plan changes on Oct 12 2026 bundling Cursor with an X subscription; verify on cursor.com |
| Codex (CLI + ChatGPT app) | https://github.com/openai/codex | openai/codex | Apache-2.0 (CLI); app proprietary | 129920 | rust-v0.163.0 2026-10-15 | Included in ChatGPT plans (sec) |
| Claude Code desktop | https://claude.com | closed | Proprietary | - | -  | Paid Claude plan (sec) |
| opencode | https://opencode.ai | anomalyco/opencode | MIT | 217493 | v1.19.3 2026-10-16 | Free; BYO provider |
| Warp (Oz) | https://docs.warp.dev/platform/orchestration/ | warpdotdev/warp | AGPL-3.0 (client) | 65538 | v0.2026.06.03.09.49.stable_00 2026-06-03 | Free tier; Build $20/mo; Max; Business (per search summary of warp.dev/pricing) |
| Amp | https://ampcode.com | closed | Proprietary (not verified) | - | -  | Free w/ own compute/keys; Individual $20/mo incl. 45,000 orb minutes (docs/pricing) |
| Crystal -> Nimbalyst | https://nimbalyst.com | stravu/crystal | MIT (Crystal) | 3134 | v0.3.5 2026-02-26 | Nimbalyst: free individual, Teams $20/user/mo (sec) |
| Terragon | https://www.terragonlabs.com | terragon-labs/terragon-oss | Apache-2.0 (as-is snapshot) | 261 | -  | Service shut down Feb 9 2026 |
| Omnara | https://www.omnara.com | omnara-ai/omnara | Apache-2.0 | 2942 | omnarad-v0.2.7 2026-10-16 | Self-host free; cloud pay-as-you-go ($0.0414/GiB-hour machines per pricing page summary) |

David Ondrej's tool is **Cloudroom** (cloudroom.dev; davidondrej/cloudroom-core + cloudroom-gui, Apache-2.0).

## Scored rubric

| Criterion | Weight |
|---|---|
| A Agent breadth | 15 |
| B Isolation and parallelism | 15 |
| C Review, merge and PR flow | 15 |
| D Remote, cloud and mobile reach | 10 |
| E Openness and license | 10 |
| F Maturity and momentum | 15 |
| G Linux setup friction (measured) | 10 |
| H Pricing and BYO model | 5 |
| I Docs and transparency | 5 |

| Tool | A | B | C | D | E | F | G | H | I | Score | Coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Realm | 5 | 5 | 5 | 5 | 5 | 3 | 5 | 5 | 5 | 94.0 | 100% |
| Orca | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 5 | 4 | 93.0 | 100% |
| T3 Code | 5 | 4 | 5 | 5 | 5 | 4 | 4 | 5 | 3 | 90.0 | 100% |
| Synara | 5 | 4 | 4 | 3 | 5 | 3 | 3 | 5 | 4 | 79.0 | 100% |
| Emdash | 4 | 4 | 3 | 3 | 5 | 4 | 3 | 5 | · | 74.5 | 95% |
| Paseo | 4 | · | · | 5 | 5 | 4 | 4 | 5 | · | 74.5 | 65% |
| OpenChamber | 3 | 4 | · | 4 | 5 | 4 | 4 | 5 | · | 74.0 | 80% |
| Superset | 4 | 4 | 4 | 4 | 3 | 4 | 2 | 4 | · | 72.5 | 95% |
| Cloudroom | 4 | 4 | · | 5 | 5 | 3 | 2 | 5 | · | 72.0 | 80% |
| Vibe Kanban | 4 | 4 | 3 | 2 | 5 | 2 | 4 | 5 | 3 | 69.0 | 100% |
| Claude Squad | 5 | 3 | 2 | 1 | 4 | 3 | 4 | 5 | 3 | 65.0 | 100% |
| Conductor | 3 | 4 | 5 | 4 | 1 | · | 1 | 3 | 4 | 62.5 | 85% |
| Sculptor | 2 | 5 | 3 | 2 | 4 | 2 | · | 4 | 3 | 60.0 | 90% |
| Mux (now 'Xum') | · | 3 | · | · | 4 | 3 | 3 | 4 | · | 58.5 | 55% |

Scores are judgement from cited evidence. Criteria without evidence score a neutral 2.5; coverage shows how much weight a score rests on.

## Hands-on

### Launch probes

| Tool | First window (s) | RSS MB | Gate |
|---|---|---|---|
| Orca 1.4.230 | 4.82 | 920 | none (agent picker; detected OpenCode) |
| Synara 1.0.7 | 8.37 | 2134 | none ('No account') |
| Superset 1.39.0 | 11.41 | 895 | GitHub/Google sign-in required |
| Emdash 1.2.8 | 6.59 | 3932 | GitHub connect, skippable |
| OpenChamber 2.5.0 | 5.32 | 1297 | none |
| Paseo 0.12.0 | 4.65 | 852 | none |
| Cloudroom GUI v110-beta | 3.3 | 795 | none seen in 12 s |
| Mux/Xum 0.31.0 | 6.08 | 1065 | gateway login offered, skippable |
| Realm 2.5.0* | 3.32 | 968 | none (agent picker; sign-in optional) |
| T3 Code server | 1.01 (port) | 394 | none |

* Realm: author-run on a GitHub-hosted ubuntu-latest runner (x86_64, 4 vCPU, 16 GB, Ubuntu 24.04), the median of 3 launches after one that was not counted. Orca 1.4.230 on the same runner, same probe: 4.1 s, 922 MB. Logs: runs/F-realm/gui/, runs/F-orca-same-runner/gui/.

### Lane A (stub agent, 6 parallel)

| Harness | Runs | All launched (s) | Mean wall (s) | Verified | Peak RSS MB |
|---|---|---|---|---|---|
| Baseline git worktree | 1 | 0.043 | 8.4 | 6/6 | - |
| Claude Squad | 3 | 11.18 to 11.89 | 24.6 | 18/18 | 102 to 118 |
| Orca (orca serve CLI) | 3 | 1.52 to 1.90 | 16.9 | 18/18 | 1124 to 1140 |
| Realm (realm serve CLI)* | 3 | 0.51 to 0.57 | 15.5 | 18/18 | 342 to 345 |

* Realm: run by Realm's author (a disclosed conflict of interest) on a GitHub-hosted ubuntu-latest runner (x86_64, 4 vCPU, 16 GB, Ubuntu 24.04), not on the 8 vCPU box the other rows come from, through the `realm` command the v2.5.0 release's Linux AppImage ships (squashfs-root/resources/bin/realm). Same harness shape (harness/realm_run.py), same fixture, stub and verifiers. Orca 1.4.230 ran on the same runner in the same job (harness/orca_suite.py, runs/F-orca-same-runner/). Earlier runs are in runs/F-realm-ci-build/ (a pre-release CI build), runs/F-realm-container/ (a Debian 13 container) and runs/F-realm-macos/.

| Same GitHub runner, same job (author-run) | Realm* | Orca 1.4.230 |
|---|---|---|
| First window, AppImage on Xvfb (s) | 3.32 | 4.1 |
| Process-tree RSS 12 s later (MB) | 968 | 922 |
| Headless server ready (s) | 0.51 to 0.52 | 3.24 to 3.34 |
| All 6 launched (s) | 0.51 to 0.57 | 2.58 to 2.67 |
| Mean wall, launch to verified (s) | 15.5 | 17.6 |
| Verified | 18/18 | 18/18 |
| Peak RSS (MB) | 342 to 345 | 1227 to 1347 |

Claude Squad launch includes about 1.1 s per session of driver keystroke delays. Crash test (t3 SIGKILL): both tools kept the other 5 sessions verified and preserved the partial work. Merges done with git: 5/6 clean for both, with t5b conflicting in shelf/config.py as designed. Realm* matched both: 5/5 others verified with t3's partial work kept, and 5/6 clean merges.

### Lane B (real model)

| Model | Task | Exit | Wall s | Verified |
|---|---|---|---|---|
| groq/openai/gpt-oss-120b (6 parallel) | t4 | 1 | 179.5 | fail |
| groq/openai/gpt-oss-120b (6 parallel) | t2 | 1 | 233.3 | fail |
| groq/openai/gpt-oss-120b (6 parallel) | t5b | 1 | 234.8 | fail |
| groq/openai/gpt-oss-120b (6 parallel) | t5a | 1 | 292.2 | fail |
| groq/openai/gpt-oss-120b (6 parallel) | t1 | 1 | 292.5 | fail |
| groq/openai/gpt-oss-120b (6 parallel) | t3 | 1 | 347.9 | fail |
| groq/openai/gpt-oss-20b (serial) | t1 | 1 | 131.7 | fail |
| groq/openai/gpt-oss-20b (serial) | t2 | timeout | 400.0 | fail |
| groq/qwen/qwen3.8-27b (serial) | t1 | aborted | - | fail |

## Verdicts

- **Linux or Windows, open source, scriptable**: Orca. The only GUI orchestrator we fully drove headless, and it is MIT.
- **Mixing Claude + Codex + Cursor subscriptions, remote/phone control**: T3 Code, with Synara as the MIT alternative that adds a built-in browser and an agent gateway. Both run your local CLIs, so you need them authenticated.
- **Terminal-only, SSH boxes, minimal footprint**: Claude Squad: about 100 MB, scriptable via tmux, recovers cleanly. Add your own PR tooling.
- **Mac, review-heavy workflow**: Conductor (by reputation; untested here). Open alternatives: T3 Code, Orca.
- **Agents that keep running with the laptop closed, self-hosted**: Cloudroom (core on your own VM), or T3 Code's headless server behind Tailscale.
- **Real sandboxing**: Sculptor (containers). Worktree tools isolate files, not processes, ports or credentials.
- **Kanban planning**: Vibe Kanban, only if you accept that it is community-maintained now.
- **You use one vendor only**: Its own app (Claude Code desktop, Codex in ChatGPT, Cursor Agents Window) may be enough.

## What we couldn't test

- **Real-model task success for every tool**: No Claude/Codex/Cursor/Grok CLI was authenticated on the box. The only key (Groq free tier) cannot fit one opencode request per minute. We did not buy credits or sign up for anything.
- **T3 Code and Synara agent sessions**: Both orchestrate agent CLIs that are installed and authenticated; none were. We verified install and boot only. We could have pointed T3 at opencode+Groq, but that would hit the same rate wall.
- **Conductor, Claude Code desktop, Codex app**: macOS-only, or they need a vendor login.
- **Superset beyond the first screen**: Mandatory GitHub/Google sign-in. We did not create or link an account.
- **Cloudroom core**: The installer needs root, systemd and a fresh Ubuntu 24.04 VM. Running it would have changed a shared machine, so we did not.
- **Sculptor**: Needs Docker, which is not available.
- **Cursor, Warp Oz, Amp**: Account required; cloud execution.
- **Terragon, Omnara (old product)**: The service is shut down, or the product pivoted.
- **GUI diff/merge UX quality**: We captured first screens only. We did not click through each app's review flow, so review UX scores rest on vendor docs and secondary sources.
- **Token and cost tracking**: Needs real agent sessions; marked unknown or partial in the matrix.
- **Statistical power**: 3 runs per lane-A harness and 1 run per startup probe on a shared VM. Treat differences under about 20% as noise.

## Sources

- [T3 Code site](https://t3.codes/)
- [T3 Code repo + v0.1.0 notes](https://github.com/pingdotgg/t3code/releases)
- [T3 Code architecture](https://github.com/pingdotgg/t3code/blob/main/docs/internals/overview.md)
- [Synara site/docs](https://www.trysynara.com/docs)
- [Synara install](https://www.trysynara.com/install)
- [Synara repo](https://github.com/Emanuele-web04/synara)
- [Orca repo](https://github.com/stablyai/orca)
- [Orca orchestration docs](https://www.onorca.dev/docs/cli/orchestration)
- [David Ondrej GitHub (Cloudroom)](https://github.com/davidondrej)
- [Cloudroom announcement (LinkedIn)](https://www.linkedin.com/posts/davidondrej_i-just-built-an-app-that-makes-it-possible-activity-7509398919173292032-hMLI)
- [David Ondrej on X: Cloudroom GA](https://x.com/DavidOndrej1/status/2111990305155396010)
- [Theo on X re: T3 Code](https://x.com/theo/status/2111975231518867705)
- [Synara maintainer on X](https://x.com/emanueledpt/status/2111396829908869248)
- [Conductor pricing](https://www.conductor.build/pricing)
- [Claude Squad repo](https://github.com/smtg-ai/claude-squad)
- [Superset](https://superset.sh)
- [Emdash](https://emdash.com)
- [Paseo](https://paseo.sh)
- [Vibe Kanban repo](https://github.com/BloopAI/vibe-kanban)
- [Sculptor](https://imbue.com/product/sculptor/)
- [Terragon shutdown](https://www.terragonlabs.com/)
- [Omnara pricing](https://www.omnara.com/pricing)
- [Realm site](https://realm.computer)
- [Realm repo + releases](https://github.com/31Carlton7/realm/releases)
- [Realm architecture](https://github.com/31Carlton7/realm/blob/main/docs/architecture/README.md)
- [Realm on Linux and Windows (platform status)](https://github.com/31Carlton7/realm/blob/main/docs/platforms.md)
- [Cursor Agents Window](https://cursor.com/docs/agent/agents-window)
- [Warp orchestration](https://docs.warp.dev/platform/orchestration/)
- [Amp pricing](https://ampcode.com/docs/pricing)
- [Secondary: appmorphy roundup (author builds a competitor, disclosed)](https://www.appmorphy.com/blog/best-tools-run-multiple-ai-coding-agents)
- [Secondary: Augment Code OSS orchestrators](https://www.augmentcode.com/tools/open-source-agent-orchestrators)
- [Secondary: Nimbalyst roundup (vendor)](https://nimbalyst.com/blog/best-ai-agent-orchestration-platforms-2026/)
