# Draft X thread (not posted)

1/
I benchmarked "agent orchestrators" for coding agents this week: the apps that run Claude Code, Codex and friends in parallel with worktrees, sessions and review.

22 tools checked, 11 installed on a Linux box, 2 driven end to end. Every number below comes from a logged run.

2/
Setup: a tiny Python repo with 6 tasks (bug fix, feature, refactor, tests checked against seeded mutants, plus two agents editing the same function on purpose). Hidden verifiers decide pass or fail.

3/
Caveat up front: the box had no logged-in Claude, Codex or Cursor. The only model key was a free tier capped at about 8k tokens per minute, and a single opencode request was 7.3k to 8.6k tokens. Real-model runs went 0 for 9.

So I tested the orchestrators with a deterministic stub agent instead.

4/
Orca was the only GUI orchestrator I could drive fully headless. `orca serve` was ready in about 3 s, it launched 6 worktree-isolated agents concurrently in under 2 s, and it passed 18 of 18 across 3 runs. Its terminals survived 3 server restarts. Peak memory was about 1.1 GB.

5/
Claude Squad also passed 18 of 18, at about 100 MB. When I killed tmux under it, every session came back paused and resumable. One rough edge: the -p flag was not picked up by the new-session form until I added a profile.

6/
T3 Code has the deepest documented feature set: cross-provider delegate_task, an MCP for agents, a PR flow, mobile. Its server booted in 1 s. I could not run a session through it without an authenticated agent CLI, so it gets no task numbers from me.

7/
Desktop apps on Linux, time to first window: Cloudroom 3.3 s, Paseo 4.7 s, Orca 4.8 s, OpenChamber 5.3 s, Mux 6.1 s, Emdash 6.6 s, Synara 8.4 s, Superset 11.4 s.

Idle memory ranged from about 0.8 GB to 3.9 GB (Emdash).

8/
Account walls: Superset needs GitHub or Google sign-in before anything else. Emdash and Mux ask but let you skip. Orca, Synara, Paseo and OpenChamber just open.

9/
Merges: every tool hands you branches and leaves merging to git. The designed conflict showed up exactly where expected, and no tool warned that two sessions were editing the same function.

10/
Not tested: Conductor (macOS only), first-party apps that need logins, Sculptor (needs Docker), Cloudroom core (needs root on a fresh VM).

Full report with the matrix, rubric weights and raw logs is linked below.
