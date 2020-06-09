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
    print(CL)
    M = WL.readAllSheets(mapfile)
    X = dict.fromkeys(['data','params','proc'])
    (X['data'],X['params']) = (WL.makeDicts(M),WL.makeParams(M))
    print(X['params'])
    print('Done')