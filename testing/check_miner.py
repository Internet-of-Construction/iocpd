# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 08:59:17 2022

@author: GarlefHupfer
"""

import os
import pm4py
os.chdir('C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.3 Gesamtwirtschaftlichkeitsanalyse/3 IoC-Ontologie/python/')
import pandas

path = 'testing/progress_processes/'

proc = pandas.read_csv(path + '1.csv')
proc2 = pandas.read_csv(path + '2.csv')

from Checker.check import check_updates
updates = check_updates(proc, proc2)



#from Miner.miner import Miner

#miner = Miner('testing/Datenbank erstellen/logs/log.csv')
#dfg = miner.get_dfg()
#miner.visualize_dfg(dfg)




# tbr
'''
from pm4py.algo.discovery.alpha import algorithm as alpha_miner

net, initial_marking, final_marking = alpha_miner.apply(log)

from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
replayed_traces = token_replay.apply(log, net, initial_marking, final_marking)
'''
#tree = pm4py.discover_process_tree_inductive(log)


#from pm4py.objects.conversion.process_tree import converter

#bpmn_graph = converter.apply(tree, variant=converter.Variants.TO_BPMN)
#pm4py.write_bpmn(bpmn_graph, "testing/a.bpmn", enable_layout=True)