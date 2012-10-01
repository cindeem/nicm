#!/usr/local/epd/bin/python

from math import sqrt
import sys
import csv
import os
import re
import nibabel as ni
import nipype.interfaces.fsl as fsl
import numpy as np
import argparse
import tempfile

class CenterMass():

    def __init__(self, filename, use_mm = True, thresh = 20):
        """ Calculate center of mass of brain in image volume using fslstats

        Parameters
        ----------
        filename : str
            Str representing image file
        use_mm : Bool
            Calc center of mass in mm space (default True)
            If False calculates center of mass in voxel space
        thresh : int
            Threshold for distance from 0,0,0 to center of mass

        Returns
        -------

        result : tuple (tuple, float, str)
            Returns (cm, dist, warning) 
            cm is calculated center of mass (x,y,z)
            dist is distance of center of mass from (0,0,0)
            warning is '' if dist < thresh, otherwise '!off center'

        """

        self.filename = filename
        self.thresh = 20
        if use_mm:
            self._op = '-c'
        else:
            self._op = '-C'

    def _calc_dist(self):
        """ calculates distance of center of mass from (0,0,0)
        returns dist"""
        warning = '' # default warning is empty
        dist = sqrt(float(sum([x**2 for x in self.cm])))
        if dist > self.thresh:
            warning = '!off center'
        return dist, warning

    def run(self):
        """ calculates center of mass of input image, and distance
        returns tuple (cm, dist, warning)"""
        com = fsl.ImageStats()
        com.inputs.in_file = self.filename
        com.inputs.op_string = self._op
        output = com.run()
        if not output.runtime.returncode == 0:
            return (('na', 'na', 'na'), 'na', 'FAILED')
        self.cm = output.outputs.out_stat
        return (tuple(self.cm), self._calc_dist()[0], self._calc_dist()[1])

class CSVIO:

    def __init__(self, filepath, mode = 'w'):
        """
        Modes:
        'w' = (over)write
        'a' = append
        'r' = read
        """
        self.mode = mode
        path, self.filename = os.path.split(filepath)
        if not re.search('.csv', self.file):
            self.filename = self.filename + '.csv'

        prevdir = os.getcwd()

        if writepath:
            os.chdir(writepath)
        self.file = open(filename, writemode)
        self.initialized = False
        if mode == 'w':
            self.writer = csv.writer(self.file, delimiter = ',')  
        elif mode == 'a':
            self.initialized = True
            self.writer = csv.writer(self.file, delimiter = ',')  
        elif mode == 'r':
            self.reader = csv.reader(self.file, delimiter = ',')

        os.chdir(prevdir)   

    def _init(self):
        """Initializes the file with a header, overwriting existing content"""
        if self.initialized:
            return
        if self.mode == 'a':
            self.initialized = True
            return
        if self.mode == 'r':
            self.reader.next()
            self.initialized = True
            return
        self.writer.writerow(['path','id', 'x', 'y', 'z', 'distance', 'flags?'])
        self.initialized = True

    def writeline(self, output):
        if not self.initialized:
            self._init()
        self.writer.writerow(output)

    def readline(self):
        if not self.initialized:
            self._init()
        return self.reader.next()

class CMTransform:
    
    def __init__(self, filepath):
        """Calculates transform that maps the center of mass of a brain 
        at filepath to (0, 0, 0), and writes a copy of the brain 
        to a new .nii file with the calculated transform.
        
        Params
        ------
        filepath
            location of .nii file for which to create transform matrix

        Seems to work with relative filepaths.
        
        >> t = CMTransform('/home/jagust/UCSF/AD-v1/B05-206/fs_ss_anatomy/rad_nu_mri.nii')
        >> t.run('/home/jagust/output.nii')
        """

        self.exists = True
        if os.path.exists(filepath):
            self.exists = False
        self.olddir = os.getcwd()
        self.filepath = filepath
        self.dir, self.file = os.path.split(filepath)
        if self.dir:
            os.chdir(self.dir)
        self.img = ni.load(self.file)
        os.chdir(self.olddir)

    def dtransform(self):
        """returns affine transform that maps the middle voxel (i/2, j/2, k/2) to (0, 0, 0)""" 
        self.zooms = self.img.get_header().get_zooms()
        self.shape = self.img.get_shape()
        self.old_affine = self.img.get_affine()
        new_affine = np.identity(4)
        i = 0
        for zoom in self.zooms:
            new_affine[i, i] = zoom
            new_affine[i, 3] = -1 * self.shape[i]/2
            i = i + 1
        return new_affine

    def cmtransform(self):
        """returns affine transform that maps the center of mass of the brain to (0, 0, 0)"""
        new_affine = self.dtransform()
        tempdir = tempfile.mkdtemp()
        newfile = os.path.join(tempdir, 'tmp.nii.gz')
        if (self.dir):
            os.chdir(self.dir)
        newimg = ni.Nifti1Image(self.img.get_data(), new_affine)
        os.chdir(tempdir)
        newimg.to_filename('tmp.nii.gz')
        cmfinder = CenterMass('tmp.nii.gz')
        output = cmfinder.run()
        print output
        cm = output[0]
        i = 0
        for axis in cm:
            new_affine[i][3] = new_affine[i][3] - axis
            i = i + 1
        os.chdir(self.olddir)
        return new_affine

    def run(self, filepath=''):
        """Creates copy of source .nii file with a transform mapping the center of mass of the brain to (0, 0, 0) at filepath.
        
        Parameters
        ----------
        filepath:
            Destination of new file with a center of mass transform.
        """
        print filepath
        if filepath == '':
            filepath = self.filepath.split('.nii')[0] + '_centered.nii'
        new_affine = self.cmtransform() 
        dir, file = os.path.split(filepath)
        newimg = ni.Nifti1Image(self.img.get_data(), new_affine)
        if dir:
            os.chdir(dir)
        newimg.to_filename(file)
        os.chdir(self.olddir)
        return filepath

class CMAnalyze:
   
    def __init__(self, outputfile, use_mm = True, threshold = 20, overwrite = True):
        """
        Checks a .nii file for center of mass, and writes output to a .csv file.
        This class will be renamed (hopefully)

        Parameters
        ----------
        outputfile : str
            str representing output file
        use_mm : Bool
            if True, use real space coordinates, else voxel coordinates 
        threshold : int
            maximum amount for center of mass of brain to differ from the origin of the coordinates
            specified by use_mm
        overwrite : Bool
            if overwrite is True, will overwrite all data in outputfile


        """
        self.donotrun = False
        self.threshold = threshold
        self.use_mm = use_mm
        self.overwrite = overwrite
        if os.path.exists(outputfile) and not self.overwrite:
            print 'Need permission to overwrite: ' + outputfile + ', please run without --no-overwrite option'
            self.donotrun = True
            return
        self.writer = CSVWriter(outputfile) 

    def flags(self, path):
        if self.donotrun:
            return True
        if not os.path.exists(path):
            print path + ' does not exist!'
            self.flag('path', path)
            return True
        if not re.search('B[0-9]{2}-[0-9]{3}', path):
            print path + ' not in valid directory'
            self.flag('dir', path)
            return True
        dir, filename = os.path.split(path)
        if '.nii' not in filename:
            print path + ' is not a valid nifti file'
            self.flag('file', path)
            return True

    def flag(self, arg, path):
        d = {'path': [path, 'na', 'na', 'na', 'na', 'na', '!path does not exist'], 'dir': [path, 'na', 'na', 'na', 'na', 'na', '!file not in a valid directory'], 'file': [path, 'na', 'na', 'na', 'na', 'na', '!invalid filetype']}
        self.writer.writeline(d[arg])

    def run(self, path):
        """
        Checks the center of mass of the file at path using options specified by constructor
        and writes output to the file specified in the constructor
        """
        if self.flags(path):
            return

        prevdir = os.getcwd()
        idsearch = re.search('B[0-9]{2}-[0-9]{3}', path)
        id = idsearch.group()
        cm = CenterMass(path, self.use_mm, self.threshold)
        output = cm.run()
        
        cm, dist, flags = output[0], output[1], output[2]
        x, y, z = cm[0], cm[1], cm[2]
        newline = [path, id, x, y, z, dist, flags]
        self.writer.writeline(newline)
        return newline

    def runlist(self, masterfile):
        """
        Reads a file containing a list of paths to .nii files and runs run() on each
        """
        filepaths = open(masterfile).readlines()
        for file in filepaths:
            self.run(file.rstrip('\n'))

def main(inputtype, input, outputpath, threshold, overwrite = True, use_mm = True):
    m = CMAnalyze(outputpath, use_mm, threshold, overwrite)    
    if inputtype == 'list':
        m.runlist(input)
    elif inputtype == 'path':
        m.run(input)
    elif inputtype == 'dir': #this does not work
        m.runfilesin(input)
    else:
        print 'Please specify a valid input type' 



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    inputargs = parser.add_mutually_exclusive_group(required = True)
    outputargs = parser.add_mutually_exclusive_group(required = True)
    statsoption = parser.add_mutually_exclusive_group()

    inputargs.add_argument('-f', help = 'specify an input file') #run on paths in plaintext file
    inputargs.add_argument('-l', help = 'specify a file containing a list of input paths') #run on file at path
    inputargs.add_argument('-d', help = 'specify a directory containing files to run') #does not work

    statsoption.add_argument('-c', action = 'store_true')
    statsoption.add_argument('-C', action = 'store_true')

    outputargs.add_argument('-o', default = 'data.csv', help = 'specify an output file, defaults to ./data.csv') #output file
    parser.add_argument('--no-overwrite', action = 'store_true')
    parser.add_argument('-t', default = 20, help = 'specify a threshold for flagging a file as off center')

    args = parser.parse_args()

    if args.f:
        readmode = 'path'
        input = args.f 
    elif args.l:
        readmode = 'list'
        input = args.l
    elif args.d:
        readmode = 'dir'
        input = args.d
     
    if args.C:
        use_mm = False
    else:
        use_mm = True

    main(readmode, input, args.o, args.t, not args.no_overwrite, use_mm)
