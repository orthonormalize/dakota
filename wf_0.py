# 20200601:
# gamma main

import numpy as np
import pandas as pd
#import re
import sys
import os
import datetime
import wfLib as WL
import zTestHarness as Z

mapfile = r'C:\Users\rek\Desktop\lightwave\sleekdata\maps v800.xlsx'


if __name__ == '__main__':
    CL = WL.commandLine2Dict(sys.argv)   # sys.argv collects all input args as strings
    proc = CL.get('proc',CL.get('p','B1'))    # default procedure is B1
    M = WL.readAllSheets(mapfile)
    assert (('proc'+proc) in M), "Procedure %s not found." % proc
    print('Executing Procedure %s' % proc)
    
    # transform input data to representation X
    X = dict.fromkeys(['data','procs','params','computes','fields'])
    X['procs'] = WL.nestSheets(M,'proc')
    X['data'] = WL.makeDatadicts(M,startswith='data')
    X['params'] = WL.makeParams(M)
    (X['computes'],X['fields']) = (M['computes'],M['fields'])
    
    Z.executeTestHarness(X)
    print('Done')