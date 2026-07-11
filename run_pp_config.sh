#!/bin/bash

source /cds/group/pcds/engineering_tools/R4.3.0/scripts/ctrlenv_setup.sh
ctrlenv-pathmunge ctrlenv-widgets/v0.2.0

# Directory this script lives in, so pp_config3.ui is found relative to it
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Launch PyDM fully detached so the window survives this launcher script exiting
# (when invoked as a PyDMShellCommand subprocess a plain '&' child can be reaped).
# Log output so any load failure is visible in /tmp/pp_config_<user>.log
LOG="/tmp/pp_config_${USER}.log"

# The parent process (LUCID/pp_widget PyDM) hands us a PYTHONPATH that points at
# an older pcdswidgets checkout lacking the 'motion' subpackage, which shadows the
# complete ctrlenv-widgets one and makes pp_config3.ui fail to load. Clear it so the
# ctrlenv-widgets pcdswidgets (with motion) is used.
unset PYTHONPATH

setsid pydm -m '{"prefix":"SH1L2:PP"}' "$HERE/pp_config3.ui" >"$LOG" 2>&1 < /dev/null &
disown 2>/dev/null || true
