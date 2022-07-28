# -*- coding: utf-8 -*-
"""
Created on Thu Nov 11 19:30:56 2021

@author: GarlefHupfer
"""
def get_config(path):
    file = open(path)
    
    lines = file.readlines()
    
    d = {}
    
    for l in lines:
        l = l.strip()
        if (len(l) > 0):
            if not (l[0] == '#'):
                d[l[:l.find('=')]] = float(l[l.find('=')+1:])
                
    return d