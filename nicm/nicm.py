# Requires nipype, numpy, nibabel, and fsl

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

        Requires nipype and fsl to run.
        """

        self.filename = filename
        self.thresh = 20
        if use_mm:
            self._op = '-c'
        else:
            self._op = '-C'

    def _calc_dist(self, vector):
        """ calculates distance of vector from (0,0,0)
        returns dist"""
        warning = '' # default warning is empty
        dist = sqrt(float(sum([x**2 for x in vector])))
        if dist > self.thresh:
            warning = '!off center'
        return dist, warning

    def run(self):
        """ calculates center of mass of input image, and distance
        returns tuple (cm, dist, warning)"""
        ##!! note of other package used
        cwd = os.getcwd()
        com = fsl.ImageStats()
        com.inputs.in_file = os.path.abspath(self.filename)
        com.inputs.op_string = self._op
        output = com.run()
        if output.runtime.returncode != 0:
            print output.runtime.stderr
            return (('na', 'na', 'na'), 'na', 'FAILED with errorcode ' + output.runtime.returncode)
        self.cm = output.outputs.out_stat
        return_val = (tuple(self.cm), 
                      self._calc_dist(self.cm)[0],
                      self._calc_dist(self.cm)[1])
        print os.path.abspath(self.filename) + ':\n' + str(return_val) + '\n'
        os.remove(os.path.join(cwd, 'stat_result.json'))
        return return_val 


class CSVIO:

    def __init__(self, filename, mode = 'w'):
        """
        Modes:
        'w' = (over)write
        'a' = append
        'r' = read
        """
        self.mode = mode
        filename = os.path.abspath(filename)
        if not re.search('.csv', filename):
            filename = filename + '.csv'

        self.file = open(filename, mode)
        self.initialized = False
        if self.mode == 'w':
            self.writer = csv.writer(self.file, delimiter = ',')  
        elif self.mode == 'a':
            self.initialized = True
            self.writer = csv.writer(self.file, delimiter = ',')  
        elif self.mode == 'r':
            self.reader = csv.reader(self.file, delimiter = ',')

    def _setup(self): ##!! better name?
        """Sets up file for read/write.
        In write mode, overwrites file and creates header in new file.
        In read mode, skips first line.
        """
        if self.initialized:
            return
        if self.mode == 'a':
            self.initialized = True
            return
        if self.mode == 'r':
            self.reader.next()
            self.initialized = True
            return
        self.writer.writerow(['path','id', 'x', 'y', 'z', 'distance', 'warning flags'])
        self.initialized = True

    def writeline(self, output):
        if not self.initialized:
            self._setup()
        self.writer.writerow(output)

    def readline(self):
        if not self.initialized:
            self._setup() ##!! skip first (header) line 
        return self.reader.next()

    def close(self):
        """Closes the file"""
        self.file.close()


class CMTransform:
    
    def __init__(self, filename):
        """Calculates transform that maps the center of mass of a brain 
        at filepath to (0, 0, 0), and writes a copy of the brain 
        to a new .nii file with the calculated transform.
        
        Params
        ------
        filename
            location of .nii file for which to create transform matrix

        Seems to work with relative filepaths.
        Works with .nii.gz and .nii files
        
        >> t = CMTransform('/home/jagust/UCSF/AD-v1/B05-206/fs_ss_anatomy/rad_nu_mri.nii')
        >> t.run('/home/jagust/output.nii')
        """
        self.filename = os.path.abspath(filename)
        self.dir, self.file = os.path.split(filename)
        self.img = ni.load(self.filename)
        if 'nii.gz' in filename:
            self.fileext = '.nii.gz'
        else:
            self.fileext = '.nii'

    def dtransform(self):
        """returns affine transform that maps the center
        of the matrix (i/2, j/2, k/2) to (0, 0, 0)""" 
        zooms = self.img.get_header().get_zooms()
        shape = self.img.get_shape()
        self.old_affine = self.img.get_affine()
        new_affine = np.identity(4)
        for k, zoom in enumerate(zooms):
            new_affine[k, k] = zoom
            new_affine[k, 3] = -1 * shape[k]/2
        return new_affine

    def cmtransform(self):
        """returns affine transform that maps the center
        of mass of the brain to (0, 0, 0)"""
        new_affine = self.dtransform()
        tempdir = tempfile.mkdtemp()
        newfile = os.path.join(tempdir, 'tmp.nii.gz')
        newimg = ni.Nifti1Image(self.img.get_data(), new_affine)
        temppath = os.path.join(os.path.abspath(tempdir), 'tmp.nii.gz')
        newimg.to_filename(temppath)
        cmfinder = CenterMass(temppath)
        output = cmfinder.run()
        cm = output[0]
        for k, v in enumerate(cm):
            new_affine[k][3] = new_affine[k][3] - v
        return new_affine

    def fix(self, new_file=''):
        """Creates copy of source .nii file with a transform
        mapping the center of mass of the brain to (0, 0, 0) at new_file.
        
        Parameters
        ----------
        new_file:
            Destination of new file with a center of mass transform.
        """
        if new_file == '':
            new_file = os.path.abspath(self.filename.split(self.fileext)[0] +\
                                       '_centered' + self.fileext)
        print new_file
        new_affine = self.cmtransform() 
        newimg = ni.Nifti1Image(self.img.get_data(), new_affine)
        newimg.to_filename(new_file)
        return new_file


class CMAnalyze:
   
    def __init__(self, outputfile, mode='w', use_mm = True, threshold = 20,\
                 overwrite = True):
        """
        Checks a .nii file for center of mass, and writes output to
        a .csv file.

        Parameters
        ----------
        outputfile : str
            str representing output file
        use_mm : Bool
            if True, use real space coordinates, else voxel coordinates 
        threshold : int
            maximum amount for center of mass of brain to differ
            from the origin of the coordinates
            specified by use_mm
        overwrite : Bool
            if overwrite is True, will overwrite all data in outputfile


        """
        self.donotrun = False
        self.threshold = threshold
        self.use_mm = use_mm
        self.overwrite = overwrite
        if os.path.exists(outputfile) and not self.overwrite:
            print 'Need permission to overwrite: ' + outputfile +\
                  ', please run without --no-overwrite option'
            self.donotrun = True
            return
        self.writer = CSVIO(outputfile, mode) 

    def flags(self, file):
        if self.donotrun:
            return True
        if not os.path.exists(file):
            print file + ' does not exist!'
            self.flag('path', file)
            return True
        if not re.search('B[0-9]{2}-[0-9]{3}', file):
            print file + ' not in valid directory'
            self.flag('dir', file)
            return True
        dir, filename = os.path.split(file)
        if '.nii' not in filename:
            print file + ' is not a valid nifti file'
            self.flag('filename', file)
            return True

    def flag(self, arg, file):
        d = {'path': [file, 'na', 'na', 'na', 'na', 'na',
                      '!path does not exist'],
             'dir': [file, 'na', 'na', 'na', 'na', 'na',
                     '!file not in a valid directory'],
             'file': [file, 'na', 'na', 'na', 'na', 'na',
                      '!invalid filetype']}
        self.writer.writeline(d[arg])

    def run(self, filename):
        """
        Checks the center of mass of the file at path using options
        specified by constructor
        and writes output to the file specified in the constructor
        """
        filename = os.path.abspath(filename)
        if self.flags(filename):
            return

        idsearch = re.search('B[0-9]{2}-[0-9]{3}', filename)
        id = idsearch.group()
        cm = CenterMass(filename, self.use_mm, self.threshold)
        (x, y, z), dist, flags = cm.run()
        newline = [filename, id, x, y, z, dist, flags]
        self.writer.writeline(newline)
        return newline

    def runlist(self, masterfile):
        """
        Reads a file containing a list of paths to .nii files
        and runs run() on each
        """
        files = open(masterfile).readlines()
        for file in files:
            self.run(file.rstrip('\n'))


def main(input, outputfile, writemode, fix, threshold,
         overwrite = True, use_mm = True):
    """outputs center of mass of a file to a csv file

    Usage:
        python nicm.py input output
    """
    if outputfile == None:
        outputfile = os.path.join(os.path.split(input)[0], 'data.csv')
    m = CMAnalyze(outputfile, writemode, use_mm, threshold, overwrite)    
    m.run(input)
    if fix:
        t = CMTransform(input)
        t.fix()
    print os.path.abspath(outputfile)
    return os.path.abspath(outputfile)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('-o')
    parser.add_argument('-m', choices = ['w', 'a'], default = 'w') #specify a write mode
    ##!! look at parser.add_argument(...choices=['r','w']
    ##!! http://docs.python.org/dev/library/argparse.html#choices
    statsoption = parser.add_mutually_exclusive_group()
    statsoption.add_argument('-c', action = 'store_true')
    statsoption.add_argument('-C', action = 'store_true')

    parser.add_argument('-f', action = 'store_true', help = 'fix')
    parser.add_argument('--no-overwrite', action = 'store_true')
    parser.add_argument('-t', default = 20,
                        help = 'specify a threshold for flagging a'\
                        ' file as off center')
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = parser.parse_args()

        if args.C:
            use_mm = False
        else:
            use_mm = True
        main(args.input, args.o, args.m, args.f, args.t, not args.no_overwrite, use_mm)
