import unittest
import numpy as np
import numpy.testing as npt
import nicm 


if __name__ == '__main__':
        
    """ Example Usecases

        get image center of mass

        infile = 'something'
        center_mass = get_center_ofmass(infile)
        center_of_mass = CenterMass(infile).run()
    """

    # test center of mass
    infile = 'nicm_test/B00-100/test.nii'
    npt.assert_raises(TypeError, nicm.CenterMass)
    center_of_mass = nicm.CenterMass(infile)
    npt.assert_equal(center_of_mass.filename, infile)
    npt.assert_equal(center_of_mass.thresh, 20)
    npt.assert_equal(center_of_mass._op , '-c')
    center_of_mass = nicm.CenterMass(infile).run()
    npt.assert_almost_equal(center_of_mass[1], 17.1828, decimal=4)
    npt.assert_almost_equal(center_of_mass[0], (10.5, 4., 13.), decimal=4)

    outfile = 'nicm_test/test.csv'
    writer = nicm.CSVIO(outfile, 'a')
    npt.assert_equal(writer.initialized, True)
    line = ['kitty', 'hawk', 'princess', 'butterfly']
    writer = nicm.CSVIO(outfile, 'w')
    writer.writeline(line)
    writer.writeline(line)
    reader = nicm.CSVIO(outfile, 'r')
    #npt.assert_equal(reader.readline(), line)
     
    analyze = nicm.CMAnalyze('nicm_test/data.csv') 
    npt.assert_equal(analyze.use_mm, True)
    npt.assert_equal(analyze.threshold, 20)
    npt.assert_equal(analyze.overwrite, True)

    npt.assert_equal(analyze.flags('nicm_test/notaniftifile.txt'), True)
    npt.assert_equal(analyze.flags('nicm_test/notafile.nii'), True)
    analyze.run(infile)

    transform = nicm.CMTransform(infile)
    dtransform = np.array([[1., 0., 0., -10.],
                          [0., 1., 0., -10.],
                          [0., 0., 2., -5.,],
                          [0., 0., 0., 1.,]])
    cmtransform = np.array([[1., 0., 0., -10.5],
                            [0., 1., 0., -4.],
                            [0., 0., 2., -13.,],
                            [0., 0., 0., 1.,]])
    npt.assert_equal(transform.dtransform(), dtransform)
    npt.assert_equal(transform.cmtransform(), cmtransform)

    test_centered = transform.fix()
    center_mass = nicm.CenterMass(test_centered).run()
    npt.assert_almost_equal(center_mass[1], 0.0, decimal=4)
    npt.assert_almost_equal(center_mass[0], (0., 0., 0.), decimal=4)


