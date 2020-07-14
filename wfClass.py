import numpy as np
import pandas as pd
#import re
import sys
import os
import io
import datetime

globs = {k:globals()[k] for k in globals() if not (k.startswith('_'))}


# Define lots of object types, with inheritances
    # Not used for obj storage, just to define relationships

class o4StrJoin:                          # item handle needs conversion from charList to str, via (''.join())
                                                # two options: either (1) LITERAL or (2) IDENTIFIER
    pass

class oAttr:                              # item follows '.'
    pass
class oNonAttr:                           # item occurring at start of expression, or following ',', or following any BG
    pass

class oLiteral(o4StrJoin):                # item that explicitly states its value w/o references (e.g str, int, bool)
    def converter(self):
        return(self.target_type)

class oStr(oLiteral):
    target_type = str   
class oStr1(oStr):
    pass
class oStr2(oStr):
    pass
class oInt(oLiteral):          
    target_type=int
    
class oIntAttr(oInt,oAttr):               # index into list, or dict key (if key is type int) 
    pass
class oBool(oLiteral):
    target_type=bool

class oIdent(o4StrJoin):                  # {@,#,P,K,M,W} {xat,hashat,property,key(dict),method,callable keyword}
    invalidLowers = {'false':(oBool(),False),'true':(oBool(),True)}
class oXat(oIdent):                       # {@}
    pass
class oHashat(oIdent):                    # {#}
    pass
class oPKMW(oIdent):                      # {P,K,M,W}
    pass
class oKeyword(oPKMW,oNonAttr):           # string representing the keyword for a callable kwarg 
    pass
class oPKM(oPKMW,oAttr):                  # {P,K,M} {obj property, dict key, method (either instanceM, or staticM from a lib)}
    pass
class oCallable(oPKM,oAttr):              # {M}: either instance method (df.sort_values()) or static method (pd.concat())
    pass

class oInternal:                          # object type is internal only (i.e. never visible at mT[-1])
    pass
class oList(oInternal):
    pass
class oDict(oInternal):
    pass
class oCallable(oInternal):
    pass
    
class oPre:
    pass
class oPreAttr(oPre):                     # invoked after '.'
    pass
class oPreNonAttr(oPre):                  # invoked (1) at $ (2) after ',' or (3) after any BG
    pass

class oPost:
    pass
class oPostList(oPost):                   # invoked after ']' 
    pass
class oPostCallable(oPost):               # invoked after ')'
    pass
class oPostDict(oPost):                   # invoked after '}' (placeholder)
    pass
class oPostStr(oPost,oLiteral):           # invoked after endstring character
    target_type=str


def getter(parent,item):
    if (isinstance(parent,dict)):
        return dict.get(parent,item)
    elif (isinstance(item,int)):
        return parent[item]
    else:
        return getattr(parent,item)
    

class Instruction:
    def __init__(self,*args,**kwargs):
        self.a=args
        self.k=kwargs
        self.X=self.k['X']
        self.procname=self.k['procname']
       
    
    def getObj7(self,s,obj0=None,ifEmpty=None,ignoreLevels=0):
        # s === string that refers to a chain that can be resolved into objects and/or methods
        # Find and return the corresponding object within the dataStructure.
        # s can be empty. If so, return ifEmpty
        
        def executeCallable():
            # input state: (uses vars from scope:getObj7)
                # callableDictStack[-1] must be dict {kwQ,keyList,cur}. Keywords obtained here. ===> D
                # final two elements of container[-1] should be:
                    # method (either boundMethod of instance, or staticMethod of another class): ===> objFUNK
                    # list of arguments to be passed into the callable: ===> argList
            # output state:
                # callableDictStack has popped off one used item
                # container[-1]: two items popped off (objFUNK, argList); then one item pushed (output from method call)
                
            D = callableDictStack.pop()
            argList = container[-1].pop()
            objFUNK = container[-1].pop()
            assert (len(argList)==len(D['keyList'])), 'length mismatch: keys:%d, args:%d' % (len(D['keyList']),len(argList))
            dex=0
            while dex in D['keyList']:
                dex+=1
            A = argList[:dex]
            K = dict(zip(D['keyList'][dex:],argList[dex:]))
            container[-1].append(objFUNK(*A,**K))
        
        def resolve():
            # i.e. stepOut
            # input state: ch is in {EG, ',', '.', '='}
            # output: resolved container[-1] into previous level of stack 
            # function: 
                # 1) Pop container[-1]. Assemble: Combine / interpret / convert / etc., if necessary. 
                # 2) Drop as one object into the parent level of the container stack.
                # 3) Attribute processing: (a) get attr if PKM, or (b) execute if postcallable
                        # (c) if neither, but destination is callable: update callableDictStack
                # 4) Pop mT
            R = container.pop()
            if (isinstance(mT[-1],o4StrJoin)):
                R=''.join(R)
                if (isinstance(mT[-1],oIdent) and (R.lower() in mT[-1].invalidLowers)): # hack: detect and typeConvert booleans
                    (mT[-1],R) = mT[-1].invalidLowers[R.lower()]
                if (isinstance(mT[-1],oLiteral)):
                    R = mT[-1].converter()(R)
                elif (isinstance(mT[-1],oXat)):
                    R = (self.X['@'][int(R)])
            container[-1].append(R)
            if (isinstance(mT[-1],oAttr)):
                attribute = container[-1].pop()
                baseObj = container[-1].pop()
                container[-1].append(getter(baseObj,attribute))
            elif (isinstance(mT[-1],oPostCallable)):
                executeCallable()
            elif (isinstance(mT[-2],oCallable)):
                D = callableDictStack[-1]
                assert (D['cur'] is not None), 'only keyword args may follow a keyword arg'
                D['keyList'].append(D['cur'])
                if (D['kwQ']): # kwarg:
                    D['cur']=None
                else: # numbered arg:
                    D['cur']+=1
            mT.pop()
            
        def stepIn():
            pass
               
        mT = [None,oPre()]
        container = [[obj0],[]]
        callableDictStack = []
        
        # temporary testing framework:
        print()
        mT = self.X['mT']
        container = self.X['container']
        callableDictStack = self.X['callableDictStack']
        
        
        print('before resolve:')
        print((mT,[type(x) for x in container[-2]],[type(x) for x in container[-1]],callableDictStack))
        resolve()
        print('after resolve:')
        print((mT,[type(x) for x in container[-2]],[type(x) for x in container[-1]],callableDictStack))
        print((mT,[type(x) for x in container[-2]],[x for x in container[-1]],callableDictStack))
        # will process input string char by char here
        return(container[-1]) # placeholder: eventually need to return the correct object here  
        
    
class Statement(Instruction):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.TASK = self.k['TFT'].TASK
        self.GET = self.k['TFT'].GET
        self.SET = self.k['TFT'].SET
    
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
        
    def execute(self):
        print('placeholder: begin executing ' + self.TASK)
        self.X['@'] = self.parseExpr('GET')
        self.X['@'] = self.parseExpr('TASK',self.X['@'])
        self.parseExpr('SET',self.X['@'])
        print('placeholder: done executing ' + self.TASK)
    
class Loop(Instruction):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.controlString=self.k['controlString']
        self.body = InstructionList(self.X,self.procname,self.k['body'])
        
    def parseExpr(self,attr):
        s = getattr(self,attr)
        print('placeholder: loop parse %s' % s)
        return(s)
        
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