import nicm
import os
from glob import glob

basepath = '/home/jagust/UCSF'
writepath = os.path.join(basepath, 'userguide')
os.chdir(basepath)
for path in glob('NIFD-LBL-*'):
    outfile1 = path + '-fdg-ss.csv'
    outfile2 = path + '-pib-ss.csv'
    analyze = nicm.CMAnalyze(os.path.join(writepath, outfile1), 'w')
    analyze2 = nicm.CMAnalyze(os.path.join(writepath, outfile2), 'w')
    for file in glob(os.path.join(path, 'B*/fdg_ss_nifti/B*frame*.nii')):
        analyze.run(file)
    for file in glob(os.path.join(path, 'B*/pib_ss_nifti/B*frame*.nii')):
        analyze2.run(file)

     
