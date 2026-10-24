Runner:    GitHub-hosted ubuntu-latest, image ubuntu24 20261012.334.1, run 40114216116 attempt 1  
Realm:     v2.5.0 release (https://github.com/31Carlton7/realm/releases/download/v2.5.0): Realm-2.5.0.AppImage 259636285 bytes, sha256 61ecf73c7cf37640243b7ed8f0320cebf1890b5810722277a92b416c9a4e43c0; realm_2.5.0_amd64.deb sha256 59c5f1d7d6149e7ea84ea3d05872a89cbda95eaf458835b9c2206910cc45a8e7  
Harness:   github.com/31Carlton7/realm commit fbf3af497129122b808dc3cc43787fc931602743 (ci/linux-bench), bench/ and this workflow  
Orca:      v1.4.230 orca-linux.AppImage 265514790 bytes, sha512 checked against its latest-linux.yml  
OS:        Ubuntu 24.04.5 LTS, kernel 6.17.0-1022-azure, x86_64  
CPU:       4 vCPU, AMD EPYC 7763 64-Core Processor  
Memory:    15989 MB  
Tools:     Python 3.12.3, git version 2.55.0, tmux 3.4, Xvfb 2:21.1.12-1ubuntu1.9  
Agent CLI: none on PATH (checked: claude codex gemini cursor-agent opencode copilot goose qwen grok amp aider)  
FUSE:      fuse3 3.14.0-5build1; /dev/fuse present  

| | Realm | Orca |
|---|---|---|
| First window, warm-up launch, not counted (s) | 3.32 | 11.0 |
| First window (s) | 3.32 | 4.1 to 4.36 |
| RSS tree 12 s later (MB) | 965 to 969 | 922 to 937 |
| Processes | 8 | 7 |
| Server ready (s) | 0.51 to 0.52 | 3.24 to 3.34 |
| Server idle RSS (MB) | 163 to 165 | 385 to 412 |
| Server with no DISPLAY | lane A ran without one | {'ready_s': 3.64, 'exit_code': None} |
| Lane A verified | 18/18 | 18/18 |
| All 6 launched (s) | 0.51 to 0.57 | 2.58 to 2.67 |
| Wall, launch to verified (s) | 15.46 to 15.55 | 17.58 to 17.71 |
| Peak RSS (MB) | 342.0 to 345.0 | 1227.0 to 1347.0 |

realm: crash t3: others verified 5/5, t3 partial kept True, t3 reported {'running': False, 'exitCode': 0, 'signal': 9}; merge: 5/6 clean, post-merge verify 5/5

orca: crash t3: others verified 5/5, t3 partial kept True, t3 reported None; merge: 5/6 clean, post-merge verify 5/5
