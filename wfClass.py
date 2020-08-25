import numpy as np
import pandas as pd
#import re
import sys
import os
import io
import datetime
from collections import Counter

globs = {k:globals()[k] for k in globals() if not (k.startswith('_'))}
import builtins
builts = {s:getattr(builtins,s) for s in builtins.__dir__()}
import wfLib as WL
objs_WL = {k:getattr(WL,k) for k in WL.__dir__() if not (k.startswith('_'))}



# Define Constants:
FT_splitch = '_'
defaultDateFormat = '%Y/%m/%d'
empties = {'str':'','int':0,'bool':False,'date':np.datetime64('1970-01-01'),'float':np.nan}
typeFunctions = {'str':str,'int':int,'bool':bool,'float':float,'date':np.datetime64}
setDigits = set([chr(j) for j in range(48,58)])
setAlpha = set([chr(j) for j in range(65,91)] + [chr(j) for j in range(97,123)])
setAlphaUS = setAlpha.copy()
setAlphaUS.update('_')
setAlphaUSDigit = setAlphaUS.copy()
setAlphaUSDigit.update(setDigits)


# Type Converters:
def is_date(x):
    return (isinstance(x,np.datetime64) or (isinstance(x,datetime.date)) or isinstance(
                                            x,pd._libs.tslibs.timestamps.Timestamp))

def forceType(x,targetString,dateformatStr=defaultDateFormat):
    # x === scalar object. type of x must be in {int, float, bool, str, or date}
    # targetString must be in var typeFunctions
    x = (np.nan if (x=='') else x)
    if (pd.isna(x)):
        return(empties[targetString])
    if (targetString=='date'):
        if (isinstance(x,str)):
            return(np.datetime64(datetime.datetime.strptime(x,dateformatStr)))
        assert is_date(x), 'Cannot convert %s %s to date' % (str(type(x)),str(x))
        return(np.datetime64(x))
    elif (is_date(x) and (targetString=='str')):
        x=pd.to_datetime(x).strftime(dateformatStr)
    elif (isinstance(x,str)):
        x=x.strip()
        x = (False if (x.lower()=='false') else (True if (x.lower()=='true') else x))
    if (targetString!='str'):
        x=float(x)
    if (targetString in ['int','bool']):
        x=round(x)
    return(typeFunctions[targetString](x))

def convertTypePS(ps0,targetString,dateformatStr=defaultDateFormat):
    return ps0.apply(lambda x: forceType(x,targetString,dateformatStr)).astype(typeFunctions[targetString])


# Define lots of object types, with inheritances
    # Not used for data storage, just to define types and relationships

class o4StrJoin:                          # item handle needs conversion from charList to str, via (''.join())
                                                # two options: either (1) LITERAL or (2) IDENTIFIER
    def D_s2o():
        D = dict([(a,oPKM) for a in setAlphaUS])          # assume alphaUS_identifier is an Attribute until proven otherwise
        D.update(dict([(a,oInt) for a in setDigits]))
        D.update({'@':oXat,'#':oHashat})
        D.update({k:oGrouper.BG_2_objtype(k) for k in oGrouper.BG}) # FLAG: includes some irrelevant BGs here
        return(D)
    
    def starter2objtype(ch0):
        return(o4StrJoin.D_s2o()[ch0])
    
    def initiation_prechar(self):
        return(self.initiation_prechar)

class oGrouper:                           # any object that is closed by a specific specialCharacter
    groupers_OC = (('()','[]','{}','""',"''"))
    BG = [goc[0] for goc in groupers_OC]
    EG = [goc[1] for goc in groupers_OC]
    def BG_2_objtype(bg):
        D_bg2obj = {'(':oCallable,'[':oList,'{':oDict,"'":oStr1,'"':oStr2}
        return(D_bg2obj[bg])
    def endGrouper():
        return(self.closingChar)

class oAttr:                              # item follows '.'
    pass
class oNonAttr:                           # item occurring at start of expression, or following ',', or following any BG
    pass

class oLiteral(o4StrJoin):                # item that explicitly states its value w/o references (e.g str, int, bool)
    def converter(self):
        return(self.target_type)

class oStr(oLiteral,oGrouper):
    target_type = str   
    initiation_prechar = ''
    keepEntranceCharacter = False
    validContinuationCharacters = None    # FLAG: actually any char should be allowed. But oStr append doesn't check VCC
class oStr1(oStr):
    openingChar="'"
    closingChar="'"
class oStr2(oStr):
    openingChar='"'
    closingChar='"'
class oInt(oLiteral):          
    target_type=int
    initiation_prechar = ''              
    keepEntranceCharacter = True 
    validContinuationCharacters = setDigits
class oIntAttr(oInt,oAttr):               # index into list, or dict key (if key is type int) 
    pass
class oBool(oLiteral):
    target_type=bool

class oIdent(o4StrJoin):                  # {@,#,P,K,M,W} {xat,hashat,property,key(dict),method,callable keyword}
    invalidLowers = {'false':(oBool(),False),'true':(oBool(),True)}
class oXat(oIdent):                       # {@}
    initiation_prechar = '0'
    keepEntranceCharacter = False
    validContinuationCharacters = setDigits
class oHashat(oIdent):                    # {#}
    initiation_prechar = ''
    keepEntranceCharacter = False
    validContinuationCharacters = setAlphaUSDigit
class oPKMW(oIdent):                      # {P,K,M,W}: any identifier that starts with a letter or an underscore
    initiation_prechar = ''
    keepEntranceCharacter = True
    validContinuationCharacters = setAlphaUSDigit
class oKeyword(oPKMW,oNonAttr):           # string representing the keyword for a callable kwarg 
    pass
class oPKM(oPKMW,oAttr):                  # {P,K,M} {obj property, dict key, method (either instanceM, or staticM from a lib)}
    pass

class oInternal:                          # object type is internal only (i.e. never visible at mT[-1])
    def obj2postobj(inclass):
        D_o2po = {oCallable:oPostCallable,oList:oPostList,oDict:oPostDict}
        # FLAG: could fail if those keys ever become superclasses
        return(D_o2po[inclass])
class oList(oInternal,oGrouper):
    openingChar='['
    closingChar=']'
class oDict(oInternal,oGrouper):
    openingChar='{'
    closingChar='}'
class oCallable(oInternal,oGrouper,oPKM,oAttr):  # either instance method (df.sort_values()) or static method (pd.concat())
    openingChar='('
    closingChar=')'
    
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
    if ((isinstance(parent,dict)) and (item in parent)):
        return dict.get(parent,item)
    elif (isinstance(item,int)): # list
        return parent[item]
    else:
        return getattr(parent,item)
    

class Instruction:
    def __init__(self,*args,**kwargs):
        self.a=args
        self.k=kwargs
        self.X=self.k['X']
        self.procname=self.k['procname']
       
    def prop2typeparse(self,nameof_targetDF,propName,splitchar=FT_splitch):
        F=self.X['fields']
        rowMatched = F.loc[(F['proc']==self.procname) & (F['object']==nameof_targetDF) & (F['property']==propName)]
        assert (len(rowMatched)==1), '"Fields" has %d matches for (proc,obj,prop) = (%s,%s,%s)' % (
                                                                    len(rowMatched),self.procname,nameof_targetDF,propName)
        row = next(rowMatched.itertuples())
        sType = row.type
        L = re.split(re.escape(splitchar),sType)
        return(L)
    
    def prop2typestr(self,nameof_targetDF,propName,splitchar=FT_splitch):
        L = self.prop2typeparse(nameof_targetDF,propName,splitchar=FT_splitch)
        return(L[0])
    
    def prop2typeconverter(self,nameof_targetDF,propName,mode_ico='c',splitchar=FT_splitch):
        # propName: official name of pd Series object, from X['fields'].property
        # mode_ico: one of {'i','c','o'}, for {'input','computations','output'}.
            # Allows objects to be represented in different formats for I/O than they are in internal operations 'C'
        # Date Formats are the only special formats fully customizable yet by this function (2020 August)
        # OUTPUT: lambda function, taking pd Series arg, that applies the correct type conversion to the arg
        L = self.prop2typeparse(nameof_targetDF,propName,splitchar=FT_splitch)
        targetString = L[0]
        dateformatString = None
        for s in L[1:]:
            assert (s[0] in 'ico')
            assert (s[1] == '=')
            if s.startswith(mode_ico):
                dateformatString = s[2:]
        if ((targetString=='date') and (dateformatString is None)):
            dateformatString = defaultDateFormat
        return (lambda pandasSeries: convertTypePS(pandasSeries,targetString,dateformatStr=dateformatString))
    def getObj0(self,obj2find):
        # obj2find === string, name of desired object
        # return a dict pointing to the obj2find's parent 
            # Search priority: {X, globs, builts, objs_WL, self.__dir__()}
            # This function can only return 1 of 5 dicts: {X, globs, builts, objs_WL, instanceAttrs}
                # Not an instance method. All instance data must reach getObj in one of two ways:
                    # through X['@'], OR
                    # through Hashats (e.g. X['data'])
        for searchSpace in [self.X,globs,builts,objs_WL]:
            if (obj2find in searchSpace):
                return(searchSpace)
        # if not yet found, it had better be in self.__dir__() (e.g. it's a direct call of an Instruction instance method)
        instanceAttrs = {k:getattr(self,k) for k in self.__dir__() if not (k.startswith('_'))}
        assert (obj2find in instanceAttrs), 'Cannot find object: %s' % obj2find
        return(instanceAttrs)
    
    def getObj(self,s,obj0=None,ifEmpty=None,ignoreLevels=0):
        # s === string that refers to a chain that can be resolved into objects and/or methods
        # Find and return the corresponding object within the dataStructure.
        # s can be empty. If so, return ifEmpty
        
        def retrieveArgumentName_Callable():
            D = callableDictStack[-1]
            assert (D['cur'] is not None), 'only keyword args may follow a keyword arg'
            D['keyList'].append(D['cur'])
            if (D['kwQ']): # kwarg:
                D['cur']=None
            else: # numbered arg:
                D['cur']+=1
                
        def executeCallable():
            # input state: (uses vars from scope:getObj7)
                # callableDictStack[-1] must be dict {kwQ,keyList,cur}. Keywords obtained here. ===> D
                # final two elements of container[-1] should be:
                    # method (either boundMethod of instance, or staticMethod of another class): ===> objFUNK
                    # list of arguments to be passed into the callable: ===> argList
            # output state:
                # callableDictStack has popped off one used item
                # container[-1]: two items popped off (objFUNK, argList); then one item pushed (output from method call)
            # This function DOES NOT change len(container), DOES NOT modify mT at all
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
                if (isinstance(mT[-1],oIdent) and (R.lower() in mT[-1].invalidLowers)): # hack: detects/typeConverts booleans
                    (mT[-1],R) = mT[-1].invalidLowers[R.lower()]
                if (isinstance(mT[-1],oLiteral)):
                    R = mT[-1].converter()(R)
                elif (isinstance(mT[-1],oXat)):
                    R = (self.X['@'][int(R)])
                elif (isinstance(mT[-1],oHashat)):
                    R = self.executeHashat(R)
            container[-1].append(R)
            if (isinstance(mT[-1],oAttr)):
                attribute = container[-1].pop()
                baseObj = ((container[-1].pop()) if (container[-1]) else (None))
                if (baseObj is None):
                    baseObj = self.getObj0(attribute)
                    if (isinstance(mT[-2],oCallable)): 
                        # ancestor was never written as callableArg, so CDS still needs update!
                        retrieveArgumentName_Callable()
                container[-1].append(getter(baseObj,attribute))
            elif (isinstance(mT[-1],oPostCallable)):
                executeCallable()
            elif (isinstance(mT[-2],oCallable)):
                retrieveArgumentName_Callable()
            mT.pop()
            
        def stepIn(initiateType):
            mT.append(initiateType())
            container.append([])
               
        assert ((isinstance(s,str))), 's must be type <str>'
        if (not(s)):
            return(ifEmpty)
        if (ignoreLevels):
            ccc = Counter(s)
            numLevels = ccc.get('.',0)
            if (numLevels==(ignoreLevels-1)):
                if (obj0 is None):
                    return(self.getObj0(s.split('.')[0]))  # possible cryptic error/non-error if s is malformed
                else:
                    return(obj0)
            assert (numLevels>=ignoreLevels), 'Error: ignoreLevels = %d but input string has %d levels' % (ignoreLevels,numLevels)
            assert (not(any([ch in (set('()[]{},="'+"'")) for ch in ccc]))), 'specialCharacters only permitted when ignoreLevels=0'
            s = '.'.join(s.split('.')[:-ignoreLevels])
            assert (s), 'Bad input string'
            
        # 0) initialize:
        (mT,container,callableDictStack) = ([None],[[obj0]],[])      
        stepIn(oPre)
        
        # 1) process each char:
        for ch in s:
            # A)
            if (isinstance(mT[-1],oStr)):
                if (ch==mT[-1].closingChar):
                    mT[-1] = oPostStr()
                else:
                    container[-1].append(ch)
            # B)
            elif (ch=='.'):
                resolve()
                stepIn(oPreAttr)
            # C)
            elif (ch==','):
                resolve()
                stepIn(oPreNonAttr)
            # D)
            elif (ch=='='):
                keyword=(''.join(container.pop()))
                container.append([])  # not a stepOut: restart a fresh container to hold the value of this argument
                assert (isinstance(mT[-1],oPKMW)), 'Attempted to create keyword name %s but it is not an Identifier' % keyword
                assert (isinstance(mT[-2],oCallable)), 'Attempted keyword assignment %s but target is not a Callable' % keyword
                callableDictStack[-1].update({'kwQ':True,'cur':keyword}) # stage name of keyword into 'cur'
                mT[-1] = oPreNonAttr()
            # E)
            elif ((ch in oGrouper.EG) and (ch not in oGrouper.BG)):
                assert (isinstance(mT[-2],oGrouper)), 'End groupers are not valid when mT[-2] is %s' % str(mT[-2]) 
                assert (ch==mT[-2].closingChar), 'Character "%s" is not a valid closer for %s' % (ch,str(mT[-2]))
                if (isinstance(mT[-1],oPre)): # don't resolve() if contents are still empty, stepOut via pops alone
                    mT.pop()
                    container.pop()
                else:
                    resolve()
                assert (isinstance(mT[-1],oInternal)), 'Object closed by end grouper must be oInternal, not %s' % str(mT[-1])
                mT[-1] = oInternal.obj2postobj(type(mT[-1]))()
            # F)
            elif (isinstance(mT[-1],oPre)):
                if ((ch in oGrouper.BG) and (ch not in oGrouper.EG)): # Q: better way to reject stringGroupers here?
                    assert (ch!='('), "Literal Tuples Disabled. Callable must interrupt oIdent, not %s" % str(mT[-1])
                    mT[-1] = oGrouper.BG_2_objtype(ch)()
                    stepIn(oPreNonAttr)
                else:
                    mT[-1] = o4StrJoin.starter2objtype(ch)()
                    container[-1].append((ch) if (mT[-1].keepEntranceCharacter) else mT[-1].initiation_prechar)
            # G)
            elif (ch in oGrouper.BG): # i.e. '(' entering a callable
                assert (ch=='('), 'Illegal character "%s" interrupting %s'  %  (ch,str(mT[-1]))
                resolve()
                stepIn(oCallable)
                stepIn(oPreNonAttr)
                callableDictStack.append({'kwQ':False,'keyList':[],'cur':0})
            # H)
            else:
                assert (ch in mT[-1].validContinuationCharacters), 'Illegal char "%s" in %s' % (ch,str(mT[-1]))
                container[-1].append(ch)
            
        # Final resolve():
        resolve()
        return(container[-1][-1]) 
        
    
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