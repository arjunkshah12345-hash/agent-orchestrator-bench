export ORCA_HOME=/tmp/home-orca-cli
alias_orca(){ HOME=$ORCA_HOME DISPLAY=:90 /workspace/orchestrator-bench/tools/orca-x/squashfs-root/resources/bin/orca-ide "$@"; }
