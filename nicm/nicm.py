#!/usr/local/epd/bin/python

from math import sqrt
import sys
import csv
import os
import re
import nibabel as ni
import nipype.interfaces.fsl as fsl
import numpy as np

ANATOMY_PATH='fs_ss_anatomy'
WRITE_PATH='/home/jagust/cwang/cm'
ANATOMY_FILE='rad_nu_mri.nii'
R_THRESHOLD = 20
V_THRESHOLD = 20
NA = 'n/a'


class CMFinder:

    def vfindcm(self, filename):
        """returns the center of mass of a brain from a .nii file in the current directory as a list of integers corresponding to the x, y, and z coordinates."""

        com = fsl.ImageStats()
        print os.getcwd()
        if ANATOMY_FILE not in os.listdir('.'):
            #print 'File not found!'
            raise IOError('File not found!')
        com.inputs.in_file=filename
        com.inputs.op_string='-c'
        output = com.run()
        assert output.runtime.returncode == 0, 'return code non-zero'
        cm = output.outputs.out_stat 
        dist = sqrt(float(sum([x**2 for x in cm])))
        if dist > V_THRESHOLD:
            cm = cm + [dist, '!off center']
        else:
            cm = cm + [dist,'']       
        return cm 
    
    def rfindcm(self, filename):
        """returns the center of mass of a brain from a .nii file in the current directory as a list of floating point numbers corresponding to the x, y, and z coordinates."""

        com = fsl.ImageStats()
        if ANATOMY_FILE not in os.listdir('.'):
            print 'File not found!'
            raise IOError('File not found!')
        com.inputs.in_file=filename
        com.inputs.op_string='-C'
        output = com.run()
        assert output.runtime.returncode == 0, 'return code non-zero'
        cm = output.outputs.out_stat
        dist = sqrt(float(sum([x**2 for x in cm]))) 
        if dist > R_THRESHOLD:
            cm = cm + [dist, '!off center']
        else:
            cm = cm + [dist, '']
        return cm

class CSVOut:
    
    def init(self, filename):
        """Creates a new csv file, if it does not already exist, and writes the header line. Overwrites existing file."""
        prevdir = os.getcwd()
        os.chdir(WRITE_PATH)
        
        if not re.search('.csv', filename):
           filename = filename + '.csv'     
        writer = csv.writer(open(filename, 'w'), delimiter=',')
        writer.writerow(['id', 'x CM', 'y CM','z CM', 'distance', 'flags?'])
        os.chdir(prevdir)   

    def add(self, filename, data):
        """Appends a line of data to a csv file, or creates the file and then writes data to it if the file does not exist"""     
        prevdir = os.getcwd()
        os.chdir(WRITE_PATH)

        if not re.search('.csv', filename):
           filename = filename + '.csv'
        if filename not in os.listdir('.'):
            self.write(filename, data)
        else:
            writer = csv.writer(open(filename, 'a'), delimiter=',')
            writer.writerow(data)
        os.chdir(prevdir)

    def write(self, filename, data):
        """creates filename.csv if it does not exist, and writes a header and a line of data to it. Overwrites existing file."""
        prevdir = os.getcwd()
        os.chdir(WRITE_PATH)

        if '.csv' not in filename:
            filename = filename + '.csv'
        self.init(filename)
        self.add(filename, data)
        os.chdir(prevdir)

def main(input, output, outputtype='v', writemode='a'):
    """Finds the center of mass of a brain from a .nii file and writes it to a .csv file
    output is the csv file to output to. Output directory can be changed in constant variables at top of this file.
    input accepts either the path to the .nii file to analyze, or if in a directory with B* subdirectories, will accept an ID. (the second method is preferred)
    outputtype: v gets data in voxel coordinates, R gets data in real space coordinates
    writemode: a adds data to the output file, w will overwrite the file from the beginning.

    
    If running as a standalone script
    ---------------------------------
    Expects the path for the output file as first argument
    Expects the path to a .nii file as second argument. 
    
    -w will overwrite previous .csv data

    -R will return real-world spatial data, -v will return voxel data.
    Defaults to -v.

    Do not run inside patient (B*) directory

    Syntax:
    python cm.py NII_FILE OUTPUT_FILE [mode [overwrite]]"""

    prevdir = os.getcwd()
    if re.match('B[0-9]{2}-[0-9]{3}', input) and input in os.listdir('.'):
        try:
            os.chdir(os.path.join(input, ANATOMY_PATH))
            finder = CMFinder()
            writer = CSVOut()
            try:
                data = [input] + finder.vfindcm(ANATOMY_FILE)
            except IOError:
                print ANATOMY_FILE + " not found for " + input + "!"
                writer.add(output, [input, NA, NA, NA, NA, '!' + ANATOMY_FILE + ' not found'])
                os.chdir(prevdir)
                return
            if writemode == 'w':
                writer.write(output, data)
            else:
                writer.add(output, data)
            os.chdir(prevdir)
            return
        except OSError, e:
            print "Path does not exist!"          
            writer.add(output, [input, NA, NA, NA, NA, '!' + ANATOMY_PATH + ' does not exist!']) 
    else: #this has not been tested thoroughly, use IDs as input if possible.
        print input
        id = '' 
        pathlst = re.split('/', input)
        try:
            for dir in pathlst[:-1]:
                os.chdir(dir)
                if re.match('B[0-9]{2}-[0-9]{3}', dir):
                    id = dir
            if id == '':
                print 'No patient ID found!'
                return
        except OSError:
            print "Invalid path: " + input + "!"
            return
        filename = pathlst[-1]
        arg = ''
        finder = CMFinder()
        writer = CSVOut()
        try:
            if outputtype == 'R':
                data = [id] + finder.rfindcm(filename)
                if writemode == 'w':
                    writer.write(output, data)
                else:
                    writer.add(output, data)
            else:
                data = [id] + finder.vfindcm(filename) 
                if writemode == 'w':
                    writer.write(output, data)
                else:
                    writer.add(output, data)
        except IOError:
            os.chdir(prevdir)
            writer.add(output, '!' + input + ' not found!') 
            print filename + " not found for " + id + "!"
            return


if len(sys.argv) >= 3:
    if '-R' in sys.argv:
        outputtype = 'R'
    else:
        outputtype = 'v'

    if '-w' in sys.argv:
        writemode = 'w'
    else:
        writemode = 'a'

    main(sys.argv[1], sys.argv[2], outputtype, writemode)
