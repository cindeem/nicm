# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import nicm
import argparse
import sys

def main(input, outputfile, mode, fix, threshold,
         overwrite = True, use_mm = True):
    """outputs center of mass of a file to a csv file

    Usage:
        python nicm.py input output
    """
    cm = CenterMass(input)
    output = cm.run()
    print output 
    if mode != 'q':
        if outputfile == None:
            outputfile = os.path.join(os.path.split(input)[0], 'data.csv')
        m = CMAnalyze(outputfile, mode, use_mm, threshold, overwrite)    
        m.run(input)
        print os.path.abspath(outputfile)
    if fix:
        t = CMTransform(input)
        t.fix()
    return output 

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="""
    This is the description of this command""",
                                     epilog = """nicm_cmd -f /home/user/dir/B12-234/file.nii
                                               nicm_cmd -o data.csv /home/user/dir/B12-234/file.nii""")

    parser.add_argument('input', help = 'nifti file to take as input')
    parser.add_argument('-o', help = 'log file (csv) to output to')
    parser.add_argument('-m', choices = ['w', 'a', 'q'], default = 'q',
                        help = """specify a write mode: w[rite], r[ead], a[ppend], q[uiet]
                        write:
                            creates a new .csv file as log
                        append:
                            creates a new .csv file as log if does not exist
                            else, appends to existing .csv log
                        quiet:
                            do not write a log""") #specify a write mode
    statsoption = parser.add_mutually_exclusive_group(help = 'specify mm/voxel space. defaults to mm space.')
    statsoption.add_argument('-c', action = 'store_true', help = 'use mm space')
    statsoption.add_argument('-C', action = 'store_true', help = 'use voxel space')

    parser.add_argument('-f', action = 'store_true', help = 'fix: create a centered copy of the file')
    parser.add_argument('--no-overwrite', action = 'store_true', 
                        help = 'abort execution if the specified log (.csv) file exists')
    parser.add_argument('-t', default = 20,
                        help = 'specify a threshold for flagging a'\
                        ' file as off center')
    try:
        parser.print_help()
    except:
        args = parser.parse_args()

        if args.C:
            use_mm = False
        else:
            use_mm = True
        main(args.input, args.o, args.m, args.f, args.t, not args.no_overwrite, use_mm)
