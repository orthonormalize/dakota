# 20200601:
# gamma main

import numpy as np
import pandas as pd
#import re
import sys
import os
import datetime
import wfLib as WL

mapfile = r'C:\Users\rek\Desktop\lightwave\sleekdata\maps v800.xlsx'


if __name__ == '__main__':
    CL = WL.commandLine2Dict(sys.argv)   # sys.argv collects all input args as strings
    proc = CL.get('proc',CL.get('p','B1'))    # default procedure is B1
    M = WL.readAllSheets(mapfile)
    assert (('proc'+proc) in M), "Procedure %s not found." % proc
    print('Executing Procedure %s' % proc)
    X = dict.fromkeys(['data','procs','params','computes','fields'])
    (X['data'],X['params']) = (WL.makeDatadicts(M),WL.makeParams(M))
    X['proc'] = WL.Procedure(proc,M)
    print(X['params'])    
    print(X['proc'])
    print(X['proc'].name)
    print(X['proc'].instructions.head(3))
    print('Done')