import nicm
import os
t = nicm.CMTransform('/home/jagust/UCSF/AD-v1/B05-206/fs_ss_anatomy/rad_nu_mri.nii')
print t.dtransform()
print t.cmtransform()
#t.run('~/test.nii')
t.run()
os.chdir('/home/jagust/UCSF/')
s = nicm.CMTransform('AD-v1/B05-206/fs_ss_anatomy/rad_nu_mri.nii')
s.run()
