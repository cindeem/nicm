import nicm
import os
t = nicm.CMTransform('/home/jagust/UCSF/AD-v1/B05-206/fs_ss_anatomy/rad_nu_mri.nii')
print t.dtransform()
print t.cmtransform()
filepath = os.path.join(os.path.abspath(os.getcwd()), 'test.nii')
t.fix(filepath)
cm = nicm.CenterMass(filepath)
cm.run()
