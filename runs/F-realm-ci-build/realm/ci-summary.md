Runner:    GitHub-hosted ubuntu-latest, image ubuntu24 20261012.334.1, run 40073363274 attempt 1  
Realm:     github.com/31Carlton7/realm commit 11bd431f3809ea0971234988c3999d845d4464ad (ci/linux-bench), Realm-2.4.0.AppImage 249601777 bytes  
Orca:      v1.4.230 orca-linux.AppImage 265514790 bytes, sha512 checked against its latest-linux.yml  
OS:        Ubuntu 24.04.5 LTS, kernel 6.17.0-1022-azure, x86_64  
CPU:       4 vCPU, AMD EPYC 7763 64-Core Processor  
Memory:    15989 MB  
Tools:     Python 3.12.3, git version 2.55.0, tmux 3.4, Xvfb 2:21.1.12-1ubuntu1.9  
Agent CLI: none on PATH (checked: claude codex gemini cursor-agent opencode copilot goose qwen grok amp aider)  
FUSE:      fuse3 3.14.0-5build1; /dev/fuse present  

| | Realm | Orca |
|---|---|---|
| First window, warm-up launch, not counted (s) | 3.3 | 5.24 |
| First window (s) | 3.3 to 3.31 | 3.82 to 4.08 |
| RSS tree 12 s later (MB) | 921 to 923 | 936 to 938 |
| Processes | 8 | 7 |
| Server ready (s) | 0.64 | 3.01 to 3.07 |
| Server idle RSS (MB) | 152 to 154 | 386 to 410 |
| Server with no DISPLAY | lane A ran without one | {'ready_s': 3.39, 'exit_code': None} |
| Lane A verified | 18/18 | 18/18 |
| All 6 launched (s) | 0.76 to 0.79 | 2.41 to 2.58 |
| Wall, launch to verified (s) | 15.69 to 15.74 | 17.32 to 17.51 |
| Peak RSS (MB) | 315.0 to 318.0 | 1242.0 to 1375.0 |

realm: crash t3: others verified 5/5, t3 partial kept True, t3 reported {'running': False, 'exitCode': 0, 'signal': 9}; merge: 5/6 clean, post-merge verify 5/5

orca: crash t3: others verified 5/5, t3 partial kept True, t3 reported None; merge: 5/6 clean, post-merge verify 5/5
