Nifti Center of Mass Utility
============================
nicm.py is a python package that does center of mass calculations
and center of mass corrections, for both single nifti files and large
batches of files.

Using nicm
----------
Most of the functionality of nicm can be accessed through the script
in the scripts directory, scripts/nicm\_cmd.py

* To calculate cm for a file:
``python nicm\_cmd.py samplefile.nii``

* Calculate cm and write to new log file:
``python nicm\_cmd.py samplefile.nii -o log.csv``

* Calculate cm and write to existing log file:
``python nicm\_cmd.py samplefile.nii -o log.csv -m a``

* Create copy of file with corrected transform
``pyton nicm\_cmd.py samplefile.nii -f``
 

Finding center of mass for a single file
----------------------------------------
nicm.CenterMass calculates the center of mass in millimeter 
space for a single nifti file, the distance of the center of mass from the origin,
as well as flags if the distance from the center of mass 
to the current origin in mm space exceeds a certain threshold. 

Example: ::  

import nicm
cm\_finder = nicm.CenterMass(sample\_file.nii, thresh = 20)
cm\_finder.run()

The first line below the import initializes a center of mass finder 
for the file sample\_file, and indicates that the file should be 
flagged if the distance from the origin exceeds 20mm.
The second line runs the calculations, and returns a triple
containing the coordinates of the center of mass, the distance
from the center of mass, and flags, if any.
``cm\_finder.run()`` returns ((x, y, z), distance, flag)

Finding center of mass for many files
-------------------------------------
nicm.CMAnalyze calculates the center of mass for many files, and writes output to a log file.
Files should be passed into nicm.CMAnalyze via a plaintext file 
which lists files, one file per line.
Example::

import nicm
analyzer = nicm.CMAnalyze(log.csv, thresh = 20)
analyzer.run(filelist)

log.csv will contain data listing the files that were processed,
their center of mass, the distance from the origin, and if they were flagged or not.

Correcting a file:
nicm.CMTransform will calculate the center of mass of a .nii file,
and write a new (automatically named, but can also be specified)n file with a coordinate mapping such that the center
of mass will coincide with the origin.

Example: ::

import nicm
transformer = nicm.CMTransform('sample.nii')
transformer.fix()

The new file will be at sample\_DATE.nii, where DATE is a datestamp. 
