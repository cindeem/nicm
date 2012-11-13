# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import ..nicm

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

    parser = argparse.ArgumentParser(description="""
    This is the description of this command""",
                                     epilog = "Examples HERE")
    parser.add_argument('input', help = '')
    parser.add_argument('-o', help = '')
    parser.add_argument('-m', choices = ['w', 'a'], default = 'w') #specify a write mode
    statsoption = parser.add_mutually_exclusive_group()
    statsoption.add_argument('-c', action = 'store_true')
    statsoption.add_argument('-C', action = 'store_true')

    parser.add_argument('-f', action = 'store_true', help = 'fix')
    parser.add_argument('--no-overwrite', action = 'store_true')
    parser.add_argument('-t', default = 20,
                        help = 'specify a threshold for flagging a'\
                        ' file as off center')
    if not sys.argv[1]:
        parser.print_help()
    else:
        args = parser.parse_args()

        if args.C:
            use_mm = False
        else:
            use_mm = True
        main(args.input, args.o, args.m, args.f, args.t, not args.no_overwrite, use_mm)
