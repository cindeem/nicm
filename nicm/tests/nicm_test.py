# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" test nicm """

import os
from os.path import abspath, join, dirname

import numpy as np

from unittest import TestCase

from numpy.testing import (assert_raises, assert_equal,
                           assert_almost_equal)

from ..nicm import (CenterMass, CSVIO,
                     CMTransform, CMAnalyze)


data_path = abspath(join(dirname(__file__), 'data'))

class TestCenterMass(TestCase):
    testnii = join(data_path, 'B00-100', 'test.nii')

    def test_class(self):
        assert_raises(TypeError, CenterMass)

    def test_interface(self):
        center_of_mass = CenterMass(self.testnii)
        assert_equal(center_of_mass.filename, self.testnii)
        assert_equal(center_of_mass.thresh, 20)
        assert_equal(center_of_mass._op, '-c')

    def test_run(self):
        center_of_mass = CenterMass(self.testnii).run()
        assert_almost_equal(center_of_mass[1], 17.1828, decimal=4)
        assert_almost_equal(center_of_mass[0], (10.5, 4., 13.),
                            decimal = 2)
        
