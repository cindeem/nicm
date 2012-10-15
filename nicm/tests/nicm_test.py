# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" test nicm """

import os
from os.path import abspath, join, pjoin, dirname

import numpy as np

from unittest import TestCase

from numpy.testing import (assert_raises, assert_equal,
                           assert_almost_equal)

from ../nicm import (CenterMass, CSVIO,
                     CMTransform, CMAnalyze)


data_path = abspath(pjoin(dirname(__file__), data))

class TestCenterMass(TestCase):
    
