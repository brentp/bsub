#!/usr/bin/env python
# encoding: utf-8
"""
Passed job ids, hold further execution until those jobs finish.
"""
from bsub import bsub
import sys
import tempfile
import os
import atexit

def bsez(args):
    """
    automatically add -e and -o with reasonable paths
    given the job name
    """
    if not sys.stdin.isatty():
        _, f = tempfile.mkstemp(suffix=".sh")
        with open(f, 'w') as fh:
            fh.write(sys.stdin.read())
        atexit.register(os.unlink, f)
    else:
        sys.stderr.write("empty job\n")
        sys.exit(1)
    args = sys.argv[1:]
    assert "-J" in args
    ji = args.index("-J")
    _ = args.pop(ji) # remove -J
    job_name = args.pop(ji)


    args2 = []
    for i, a in enumerate(args):
        if not a.startswith('-'):
            args2.append(a)
        # so a is a flag. if the next is also a flag, insert True
        elif i < len(args) - 1 and args[i + 1][0] == "-":
            args2.extend((a[1:], True))
        elif i == len(args) - 1:
            assert a[0] == "-", a
            args2.extend((a[1:], True))
        else:
            args2.append(a[1:])
    kwargs = dict(zip(args2[::2], args2[1::2]))
    print bsub(job_name, f, **kwargs)()





if __name__ == "__main__":
    bsez(sys.argv[1:])


