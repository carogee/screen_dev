#!/bin/bash

# Navigate to the pcdswidgets directory
cd /cds/home/c/cagee/pcdswidgets

# Create/setup virtual environment
make venv

# Run the PyDM application in the background
./try_in_pydm.sh -m '{"prefix":"SL1L2:POWER"}' /reg/g/pcds/epics-dev/cagee/screens/screen_dev/pp_widget3.ui &
