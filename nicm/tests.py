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
    infile = 'testdata/B12-253_PIB00000.nii.gz'
    npt.assert_raises(TypeError, nicm.CenterMass)
    center_of_mass = nicm.CenterMass(infile)
    npt.assert_equal(center_of_mass.filename, infile)
    npt.assert_equal(center_of_mass.thresh, 20)
    npt.assert_equal(center_of_mass._op , '-c')
    center_of_mass = nicm.CenterMass(infile).run()
    npt.assert_almost_equal(center_of_mass[1], 450.95794588, decimal=4)

    outfile = 'test.csv'
    writer = CSVIO(outfile, 'a')
    npt.assert_equal(writer.filename, outfile)
    npt.assert_equal(writer.initialized, True)
    line = ['kitty', 'hawk', 'princess', 'butterfly']
    writer = CSVIO(outfile, 'w')
    writer.writeline(line)
    reader = CSVIO(outfile, 'r')
    npt.assert_equal(reader.readline(), line)
     
    analyze = CMAnalyze(infile) 
    npt.assert_equal(analyze.use_mm, True)
    npt.assert_equal(analyze.threshold, 20)
    npt.assert_equal(analyze.overwrite, True)
    npt.assert_equal(analyze.outputfile, infile)

    npt.assert_equal(analyze.flags('test/notaniftifile.txt'), True)
    npt.assert_equal(analyze.flags('test/notafile.nii'), True)

    transform = CMTransform(infile)
    npt.assert_equal(analyze.filepath, infile)
    dtransform = 0
    cmtransform = 0
    npt.assert_equal(transform.dtransform(), dtransform)
    npt.assert_equal(transform.cmtransform(), cmtransform)

