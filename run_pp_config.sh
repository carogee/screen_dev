#!/bin/bash

source /cds/group/pcds/engineering_tools/R4.3.0/scripts/ctrlenv_setup.sh
ctrlenv-pathmunge ctrlenv-widgets/v0.2.0

# Run the PyDM application in the background
#./try_in_pydm.sh -m '{"prefix":"SH1L2:PP"}' /reg/g/pcds/epics-dev/cagee/screens/screen_dev/pp_widget3.ui &
pydm /cds/group/pcds/epics-dev/screens/pydm/xpp/dev/pp_config.sh &  
