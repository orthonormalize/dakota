# 20200601:
# gamma main

import sys
import wfLib as WL
import wfClass as WC
import pickle
import pandas as pd
#import zTestHarness as Z

lookup_file = 'sleekmap.txt'


if __name__ == '__main__':
    # 0) Preliminary Data Ingestion, from lookup_file and command line:
    with open('sleekmap.txt','r') as f:
        mapfile = f.read().strip()
    CL = WL.commandLine2Dict(sys.argv)   # sys.argv collects all input args as strings
    proc = CL.get('proc',CL.get('p','B1'))    # default procedure is B1
    M = WL.readAllSheets(mapfile)
    assert (('proc'+proc) in M), "Procedure %s not found." % proc
    print('Executing Procedure %s' % proc)
    
    # 1) Transform data to X representation:
    X = dict.fromkeys(['data','procs','params','computes','fields'])
    X['procs'] = WL.nestSheets(M,'proc') # as dataframes
    X['procedure'] = {}
    for procname in X['procs']:
        X['procedure'][procname] = WC.Procedure(X,procname)
    X['data'] = WL.makeDatadicts(M,startswith='data')
    X['params'] = WL.makeParams(M)
    (X['computes'],X['fields']) = (M['computes'],M['fields'])
    
    # 2) Execute:
    #Z.executeTestHarness(X)
    X['procedure'][proc].execute()
    print('Completed Execution of Procedure %s' % proc)