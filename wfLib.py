# 20200601:
# gamma main

import numpy as np
import pandas as pd
#import re
import sys
import os
import io
import datetime
from openpyxl import load_workbook

def commandLine2Dict(CL):
    # input: list of command line arguments
        # m: mapfile
        # f: rawfile
    # output: dict
    D={}
    CL=CL[::-1]
    key=None
    while(CL):
        s=CL.pop()
        if (s.startswith('-')):
            key = (s[1:] if s[1:] not in D else None)
        else:
            if key:
                D[key]=s
            key=None
    return D

def adjustDtypes_Map(M):
    # update 20200604: this function is probably irrelevant
    # input: Map is entirely string data
    # output: convert datatype of any column deemed necessary
    for (_,row) in M['dtypeMap'].iterrows():
        assert(row['Type'] not in ['date','datetime']) # do these later, if necessary
        if (row['Type']=='bool'):
            M[row['Sheet']][row['Field']] = M[row['Sheet']][row['Field']].astype(int).astype(bool)
        else:
            M[row['Sheet']][row['Field']] = M[row['Sheet']][row['Field']].astype(row['Type'])
    return M

def readAllSheets(xlFile):
    # input: path to MS xlsx file
    # output: dict of dataframes. One df for each sheet within xlsx file
    # all sheets must have a header row
    with open(xlFile, "rb") as f:
        in_mem_file = io.BytesIO(f.read())
    wb = load_workbook(in_mem_file, read_only=True)
    D = {}
    for sh in wb.sheetnames:
        #D[sh] = pd.read_excel(mapfile,sheet_name='Params',engine='openpyxl',usecols=[0,1],index_col=0)
        data = wb[sh].values
        try:
            columns = next(data)[0:] # get header line separately
            D[sh] = pd.DataFrame(data, columns=columns)
            D[sh] = D[sh][[c for c in columns if c]]  # rm extra columns (caused by sheets with cell colors / old edits ???)
            D[sh] = D[sh].applymap(lambda x: ('' if (x==None) else str(x)))  # converts all data to str. Revisit?
        except StopIteration:
            pass
    return D


def makeDicts(M,startswith='data'):
    # input: dict of DFs generated from reading all sheets of map file
        # should contain one sheet called 'dicts' that lists all key fields in format: sheet name, field name
        # optional input argument 'startswith' appends a string to the beginning of each sheet name string
    # generate a hash table from each entry in 'dicts'
        # assert uniqueness of corresponding table/field
    # then output: a dict parent pointing to all keyfields, then valuefields as nested hash tables
    
    D = {table:{} for table in getattr(M.get('dicts'),'SHEET').unique()}
    for (_,(sh,key)) in M.get('dicts').iterrows():
        fullsheetname = startswith+sh
        df = (M.get(fullsheetname))
        pS = getattr(df,key)
        assert pS.is_unique,('Found at least one duplicate value in %s:%s' % (fullsheetname,key))
        df_key = df.set_index(key,drop=True,inplace=False)
        D[sh][key]={col:(df_key[col].to_dict()) for col in df_key}
    return D

def makeParams(M,sheetname='params'):
    return (M.get(sheetname).set_index('Parameter',drop=True)['Value'].to_dict())