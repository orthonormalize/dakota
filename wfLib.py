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


class Instruction:
    
    def parseExpr(self,attr,temp=[]): # temp===workspace of objects currently being processed (i.e. variable '@' in excel file)
        s = getattr(self,attr)
        if (not(s)):
            return([])
        elif (attr in ['GET','SET']):
            # ########## assert ((attr!='SET') or (len(s)==1)), 'Only one object value can be set per row of excel file'
            E = [e.split('.')[::-1] for e in s.split(',') if e]
            out=[]
            for (i,variable) in enumerate(E):
                obj=self.X
                e1 = variable.pop()
                while variable:  # i.e.: while there exist further levels of variable name
                    obj = ((getattr(obj,e1)) if (hasattr(obj,'__getattr__')) else (obj.get(e1)))
                    e1 = variable.pop()
                if (attr=='GET'):
                    assert e1 in obj, "Cannot find var or field: %s" % e1
                    obj = ((getattr(obj,e1)) if (hasattr(obj,'__getattr__')) else (obj.get(e1)))
                    out.append(obj)
                else: # (attr=='SET')
                    obj = ((setattr(obj,e1,temp[i])) if (hasattr(obj,'__getattr__')) else (obj.__setitem__(e1,temp[i])))
            return (out or None)
        else: # (attr=='TASK')
            return(s) # placeholder
    
    
class Statement(Instruction):
    def __init__(self,X,TFT,procname,*args,**kwargs):
        self.X=X
        self.TASK = TFT.TASK
        self.GET = TFT.GET
        self.SET = TFT.SET
        self.procname = procname
        self.a = args
        self.k = kwargs
    
    def execute(self):
        print('placeholder: execute ' + self.TASK)
    
    
class Loop(Instruction):
    def __init__(self,X,controlString,body,procname,*args,**kwargs):
        self.X=X
        self.controlString=controlString
        self.body = InstructionList(self.X,procname,body)
        self.procname = procname
        self.a = args
        self.k = kwargs
        
    def execute(self):
        print('placeholder loop exec ' + self.controlString)
      
    
class InstructionList:
    def __init__(self,X,procname,myInput):
        self.X = X
        self.procname = procname
        self.instructions=[]
        if (isinstance(myInput,list)):  # placeholder
            self.instructions=myInput
        if ((isinstance(myInput,dict)) and ('procs' in myInput) and (procname in myInput.get('procs'))):
            # reading from procedure df. So extract df:
            myInput = myInput['procs'][procname]
        if (isinstance(myInput,pd.DataFrame)):
            self.instructions = self.parseDF(myInput)
    
    def execute(self):
        print('placeholder: now executing an instruction list:')
        assert(isinstance(self.instructions,list))
        for instruction in self.instructions:
            instruction.execute()
        print()
        
    def parseDF(self,df):
        (nest,bodies,loopEntranceTuplist)=(0,[[]],[])
        for T in df.itertuples():
            if InstructionList.isLoopEntrance(T):
                assert ((not(T.GET)) and (not(T.SET))), 'proc%s: Loop Entrance must have empty GET and SET' % self.procname
                nest+=1
                bodies.append([])
                loopEntranceTuplist.append(T)
            elif InstructionList.isLoopExit(T):
                assert ((not(T.GET)) and (not(T.SET))), 'proc%s: Loop Exit must have empty GET and SET' % self.procname
                assert (nest>0), 'proc%s: Too many Loop Exits' % self.procname
                bodies[nest-1].append(
                    Loop(X=self.X,controlString=loopEntranceTuplist.pop().TASK,body=bodies[nest],procname=self.procname))
                nest-=1
            else:
                bodies[nest].append(Statement(X=self.X,TFT=T,procname=self.procname))
        assert ((nest==0) and (not(loopEntranceTuplist))), 'proc%s: Unclosed Loop' % self.procname
        return bodies[0]
    
    @staticmethod
    def isLoopEntrance(T):
        return (T.TASK.startswith('for '))
    
    @staticmethod
    def isLoopExit(T):
        return (T.TASK.startswith('end for'))

    
class Procedure(InstructionList):
    def __init__(self,X,procname):
        assert ((procname) and isinstance(procname,str)), 'procedure name %s must be type str' % (str(procname))
        assert (('procs' in X) and (procname in X['procs'])), 'proc%s not found' % procname
        super().__init__(X,procname,X)

        
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
            # ignore empty sheets
            pass
    return D

def nestSheets(M,startswith):
    # input: dict of DFs generated from reading all sheets of map file
    # output: smaller dict of DFs, consisting only of the sheets whose names begin with string 'startswith'
        # that string will be chopped off of the new dictionary names
    outD = {}
    for k in M.keys():
        if (k.startswith(startswith)):
            shortName = k[len(startswith):]
            outD[shortName] = M[k]
    return outD

def df2dict(df,keys,fullsheetname):
    # Function: create a dictionary of function mappings from a DF and a list of which fields are keys
    # input: pandas DataFrame
    # output: Triply nested dict
        # lev 1 keys = keys arg
        # lev 2 keys = each other field in the DF
        # lev 3 keys = DF values of the key field. Enforces uniqueness
        # values     = DF values of the field (lev2 key)
    D=dict.fromkeys(keys,0)
    for k1 in keys:
        pS = getattr(df,k1)
        assert pS.is_unique,('Found at least one duplicate value in %s:%s' % (fullsheetname,k1))
        df_k1 = df.set_index(k1,drop=True,inplace=False)
        D[k1] = {col:(df_k1[col].to_dict()) for col in df_k1}
    return D
        
        
def makeDatadicts(M,startswith='data'):
    # input: dict of DFs generated from reading all sheets of map file
        # should contain one sheet called 'dicts' that lists all key fields in format: sheet name, field name
        # optional input argument 'startswith' appends a string to the beginning of each sheet name string
    # generate a hash table from each entry in 'dicts'
        # assert uniqueness of corresponding table/field
    # then output: a dict parent pointing to all keyfields, then valuefields as nested hash tables 
    D = {table:{} for table in getattr(M.get('dicts'),'SHEET').unique()}
    for (_,(sh,key)) in M.get('dicts').iterrows():
        D[sh][key]={}
    for sh in D:
        fullsheetname=startswith+sh
        df = M.get(fullsheetname)
        D[sh] = df2dict(df,D[sh].keys(),fullsheetname)
    return D

def makeParams(M,sheetname='params'):
    return (M.get(sheetname).set_index('Parameter',drop=True)['Value'].to_dict())