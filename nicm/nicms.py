#!/usr/local/epd/bin/python

#Python script that finds the center of mass for all anatomy scans in .nii file format under /home/jagust/UCSF/AD-v1, /home/jagust/UCSF/Control-v1 and writes the results to a csv file for each directory. 

import nicm as cm
import os
from glob import glob

UCSF_PATH = '/home/jagust/UCSF'
AD = {'dir':'AD-v1', 'out':'ad_data.csv'}
C = {'dir':'Controls-v1', 'out':'c_data.csv'}

for dct in [AD, C]:
    writer = cm.CSVOut()
    writer.init(dct['out'])
    
    os.chdir(UCSF_PATH)
    os.chdir(dct['dir'])
    ids = glob('B[0-9][0-9]-[0-9][0-9][0-9]')
    print ids
    ids.sort()
    for id in ids:
       cm.main(id, dct['out']) 
