# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 13:50:12 2022

@author: GarlefHupfer
"""


import time
import importlib.util
spec = importlib.util.spec_from_file_location('BPMNRunner', 'C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.2 Quantifizierung des Nutzens/5 LogCreation/bpmn_runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

import os
os.chdir('C:/Users/GarlefHupfer/OneDrive - ipri-institute.com/H/02-Projekte/40180003_IoC/03_Projektergebnisse/AP 9.3 Gesamtwirtschaftlichkeitsanalyse/3 IoC-Ontologie/python/')



bpmn_path = 'testing/bpmns/data model.bpmn'
output_file = 'testing/Datenbank erstellen/logs/log.csv'
config_path = 'testing/Datenbank erstellen/res/config.cfg'

times_path = 'testing/Datenbank erstellen/res/times.cfg'
transmission_times_path = 'testing/Datenbank erstellen/res/transmission_times.cfg'

run = runner.BPMNRunner(wf_spec_path=bpmn_path, output_file=output_file, config_path=config_path, times_path=times_path, transmission_times_path=transmission_times_path)

append = False
first_case_id = 1
while True:
    try:
        run.create_cases(1000, append=append, first_case_id=first_case_id)
        break
    except PermissionError:
        print('Coulnd\'t access file, retrying...')
        time.sleep(1)
        
        append=True
        file = open(output_file, 'r')
        for last_line in file:
            pass
        
        first_case_id = int(last_line[:last_line.find('|')]) + 1