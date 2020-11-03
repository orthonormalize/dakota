# dakota: main function

import sys
import dakotaLib as DL
import dakotaClass as DC
import pandas as pd
#import zTestHarness as Z

lookup_file = 'map_dakota.txt'


if __name__ == '__main__':
    # 0) Preliminary Data Ingestion, from lookup_file and command line:
    with open(lookup_file,'r') as f:
        mapfile = f.read().strip()
    CL = DL.commandLine2Dict(sys.argv)   # sys.argv collects all input args as strings
    proc = CL.get('proc',CL.get('p','B1'))    # default procedure is B1
    M = DL.readAllSheets(mapfile)
    assert (('proc'+proc) in M), "Procedure %s not found." % proc
    print('Executing Procedure %s' % proc)
    
    # 1) Transform data to X representation:
    X = dict.fromkeys(['data','procs','params','computes','fields'])
    X['procs'] = DL.nestSheets(M,'proc') # as dataframes
    X['procedure'] = {}
    for procname in X['procs']:
        X['procedure'][procname] = DC.Procedure(X,procname)
    X['data'] = DL.makeDatadicts(M,startswith='data')
    X['params'] = DL.makeParams(M)
    (X['computes'],X['fields']) = (M['computes'],M['fields'])
    
    # 2) Execute:
    #Z.executeTestHarness(X)
    X['procedure'][proc].execute()
    print('Completed Execution of Procedure %s' % proc)