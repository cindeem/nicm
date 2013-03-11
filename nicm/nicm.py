# Requires nipype, numpy, nibabel, and fsl

from math import sqrt, copysign
import csv
import os
from os.path import (splitext, join)
import re
import nibabel as ni
from nipype.interfaces.base import CommandLine
import nipype.interfaces.fsl as fsl
from nipype.utils.filemanip import split_filename
import argparse
from datetime import datetime
from tempfile import mkdtemp

def timestamp(filename):
    pth, name, ext = split_filename(filename)
    now = datetime.now().strftime('%Y-%m-%d-%H-%M')
    return join(pth, '_'.join([name, now]) +  ext)


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
        self.thresh = thresh
        if use_mm:
            self._op = '-c'
        else:
            self._op = '-C'

    def _calc_dist(self, vector):
        """ calculates distance of vector from (0,0,0)
        returns dist

        >>> from nicm import CenterMass
        >>> cm = CenterMass('somefile.nii')
        >>> cm._calc_dist([0,1,0])
        (1.0, '')

        """
        warning = '' # default warning is empty
        dist = sqrt(float(sum([x**2 for x in vector])))
        if dist > self.thresh:
            warning = '!off center'
        return dist, warning


    def find_center_of_mass(self):
        """ uses nipype CommandLine to call fslstats and
        retrieve center of mass

        Returns
        -------
        center_of_mass : list of floats
        """
        cmd = 'fslstats %s %s'%(self.filename, self._op)
        output = CommandLine(cmd).run()
        if output.runtime.returncode == 0:
            return [float(x) for x in output.runtime.stdout.split()]
        else:
            print output.runtime.stderr
            return None
        
        
    def run(self):
        """ calculates center of mass of input image, and distance
        returns tuple (cm, dist, warning)"""
        ##!! note of other package used
        com = self.find_center_of_mass()
        if com is None:
            return (('na', 'na', 'na'), 'na', 'FAILED with errorcode ' + output.runtime.returncode)
        self.cm = com
        return_val = (tuple(self.cm), 
                      self._calc_dist(self.cm)[0],
                      self._calc_dist(self.cm)[1])
        print os.path.abspath(self.filename) + ':\n' + str(return_val) + '\n'        
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
        try:
            return self.reader.next()
        except:
            return ''

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
        shape = self.img.get_shape()
        new_affine = self.img.get_affine()
        for k in range(3):
            new_affine[k, 3] = -1 * copysign(shape[k]/2, new_affine[k, k])
        return new_affine

    def cmtransform(self):
        """returns affine transform that maps the center
        of mass of the brain to (0, 0, 0)"""
        new_affine = self.dtransform()
        tempdir = mkdtemp()
        newimg = ni.Nifti1Image(self.img.get_data(), new_affine)
        tmpfile = os.path.join(os.path.abspath(tempdir), 'tmp.nii.gz')
        newimg.to_filename(tmpfile)
        cmfinder = CenterMass(tmpfile)
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
            new_file = timestamp(os.path.abspath(self.filename.split(self.fileext)[0] +\
                                       '_centered' + self.fileext))
        print new_file
        new_affine = self.cmtransform() 
        newimg = ni.Nifti1Image(self.img.get_data(), new_affine)
        newimg.to_filename(new_file)
        return new_file

    def fix_batch(self, file_list):
        """
        Calculates center of mass for self.img, applies new affine to all
        .nii files in file_list
        Returns list of output files
        """
        new_affine = self.cmtransform()
        outlist = []
        for infile in file_list:
            outlist.append(apply_affine(infile, new_affine))
        return outlist


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

    def close(self):
        self.writer.close()

    def flags(self, infile):
        if self.donotrun:
            return True
        if not os.path.exists(infile):
            print infile + ' does not exist!'
            self.flag('path', infile)
            return True
        if not re.search('B[0-9]{2}-[0-9]{3}', infile):
            print infile + ' not in valid directory'
            self.flag('dir', infile)
            return True
        dir, infilename = os.path.split(infile)
        if '.nii' not in infilename:
            print infile + ' is not a valid nifti infile'
            self.flag('filename', infile)
            return True

    def flag(self, arg, infile):
        d = {'path': [infile, 'na', 'na', 'na', 'na', 'na',
                      '!path does not exist'],
             'dir': [infile, 'na', 'na', 'na', 'na', 'na',
                     '!infile not in a valid directory'],
             'infile': [infile, 'na', 'na', 'na', 'na', 'na',
                      '!invalid infiletype']}
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

    def run_list(self, filelst):
        """
        Reads a file containing a list of paths to .nii files
        and runs run() on each
        """
        for infile in filelst:
            self.run(infile)

def apply_affine(infile, affine):
    """
    Writes auto-named new file with affine applied to infile data
    Return name of new file
    """
    if 'nii.gz' in infile:
        fileext = '.nii.gz'
    else:
        fileext = '.nii'
    img = ni.load(infile)
    outfile = timestamp(os.path.abspath(infile.split(fileext)[0] +\
                               '_centered' + fileext))
    outimg = ni.Nifti1Image(img.get_data(), affine)
    outimg.to_filename(outfile)
    return outfile
