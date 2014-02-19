#!/usr/bin/env python
# encoding: utf-8
"""
Passed job ids, hold further execution until those jobs finish.
"""
from bsub import bsub

def main(args):
    bsub.poll(args.jobids)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__,
                    formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("jobids", nargs="+", help="job ids to wait on")
    main(p.parse_args())
