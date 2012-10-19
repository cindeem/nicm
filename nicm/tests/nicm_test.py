# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" test nicm """

import os
from os.path import abspath, join, dirname

import numpy as np

from unittest import TestCase, skipIf, skipUnless

from numpy.testing import (assert_raises, assert_equal,
                           assert_almost_equal)

from ..nicm import (CenterMass, CSVIO,
                     CMTransform, CMAnalyze)


data_path = abspath(join(dirname(__file__), 'data'))

# function to test for installed FSL
def fsl_missing():
    """ looks for FSLDIR in environ"""
    try:
        os.environ['FSLDIR']
        return False
    except:
        return True

class TestCenterMass(TestCase):
    testnii = join(data_path, 'B00-100', 'test.nii')

    def test_class(self):
        assert_raises(TypeError, CenterMass)

    def test_interface(self):
        center_of_mass = CenterMass(self.testnii)
        assert_equal(center_of_mass.filename, self.testnii)
        assert_equal(center_of_mass.thresh, 20)
        assert_equal(center_of_mass._op, '-c')

    @skipIf(fsl_missing(), 'FSL NOT INSTALLED')
    def test_run(self):
        center_of_mass = CenterMass(self.testnii).run()
        assert_almost_equal(center_of_mass[1], 17.1828, decimal=4)
        assert_almost_equal(center_of_mass[0], (10.5, 4., 13.),
                            decimal = 2)
        

class TestCSVIO(TestCase):
    outfile = join(data_path, 'test.csv')
    line = ['kitty', 'hawk', 'princess', 'butterfly']

    def test_class(self):
        assert_raises(TypeError, CSVIO)

    def test_interface(self):
        writer = CSVIO(self.outfile, 'a')
        assert_equal(writer.initialized, True)
        assert_equal(writer.mode, 'a')
        writer = CSVIO(self.outfile)
        assert_equal(writer.mode, 'w')

    def test_functionality(self):
        writer = CSVIO(self.outfile)
        writer.writeline(self.line)
        writer.close()
        writer = CSVIO(self.outfile, 'a')
        writer.writeline(self.line)
        writer.close()
        reader = CSVIO(self.outfile, 'r')  
        assert_equal(reader.readline(), self.line)
        
class TestCMAnalyze(TestCase):
    outfile = join(data_path, 'data.csv')
    infile = join(join(data_path, 'B00-100'), 'test.nii')
    line = [infile, 'B00-100', '10.5', '4.0', '13.0', '17.18284027743958', '']

    def test_class(self):
        assert_raises(TypeError, CMAnalyze)

    def test_interface(self):
        analyze = CMAnalyze(self.outfile)
        assert_equal(analyze.use_mm, True)
        assert_equal(analyze.threshold, 20)
        assert_equal(analyze.overwrite, True)

    def test_errorflags(self):
        analyze = CMAnalyze(self.outfile)
        assert_equal(analyze.flags('nicm_test/notaniftifile.txt'), True)
        assert_equal(analyze.flags('nicm_test/notafile.nii'), True)
        analyze.close()

    def test_run(self):
        analyze = CMAnalyze(self.outfile) 
        analyze.run(self.infile)
        analyze.close()
        reader = CSVIO(self.outfile, 'r')
        assert_equal(reader.readline(), self.line) 

class TestCMTransform(TestCase):
    infile = join(join(data_path, 'B00-100'), 'test.nii')

    def test_class(self):
        assert_raises(TypeError, CMTransform)

    def test_dtransform(self):
        transform = CMTransform(self.infile)
        dtransform = np.array([[1., 0., 0., -10.],
                               [0., 1., 0., -10.],
                               [0., 0., 2., -5.,],
                               [0., 0., 0., 1.,]])
        assert_equal(transform.dtransform(), dtransform)

    def test_cmtransform(self):
        transform = CMTransform(self.infile)
        cmtransform = np.array([[1., 0., 0., -10.5],
                                [0., 1., 0., -4.],
                                [0., 0., 2., -13.,],
                                [0., 0., 0., 1.,]])
        assert_equal(transform.cmtransform(), cmtransform)


    def test_fix(self):
        transform = CMTransform(self.infile)
        test_centered = transform.fix()
        center_mass = CenterMass(test_centered).run()
        npt.assert_almost_equal(center_mass[1], 0.0, decimal=4)
        npt.assert_almost_equal(center_mass[0], (0., 0., 0.), decimal=4)

