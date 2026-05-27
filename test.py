#!/usr/bin/env python
import os
os.environ['QT_XCB_GL_INTEGRATION'] = 'none'

# Fix EPICS import order
from epicscorelibs.path import pyepics

# Now launch PyDM
from pydm import PyDMApplication
import sys

if __name__ == '__main__':
    app = PyDMApplication(ui_file='test.ui')
    app.exec_()
