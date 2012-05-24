"""
 create a job with a job name and any extra args to send to lsf
 in the case below. 
    -J some_job -e some_job.%J.err -o some_job.%J.out
 will be automatically added to the command.
>>> sub = bsub("some_job", R="rusage[mem=1]", verbose=True)

# submit a job via call'ing the sub object with the command to run.
# the return value is the numeric job id.
>>> print sub("date").isdigit()
True

# 2nd argument can be a shell script, in which case
# the call() is empty.
#>>> bsub("somejob", "run.sh", verbose=True)()

# dependencies:
>>> job_id = bsub("sleeper", verbose=True)("sleep 2")
>>> bsub.poll(job_id)
True

"""
import subprocess as sp
import sys
import os
import time

class BSubException(Exception):
    pass

class bsub(object):
    def __init__(self, job_name, *args, **kwargs):
        self.verbose = kwargs.pop('verbose', False)
        self.kwargs = kwargs
        self.job_name = job_name
        self.args = args
        assert len(args) in (0, 1)

    @property
    def command(self):
        return self._kwargs_to_flag_string() \
            + ((" < %s" % self.args[0]) if len(self.args) else "")

    def _get_job_name(self):
        return self._job_name

    @classmethod
    def running_jobs(self):
        return [x.split()[0] for x in sp.check_output(["bjobs", "-u", "all"]).rstrip().split("\n")[1:]]

    @classmethod
    def poll(self, job_ids):
        if isinstance(job_ids, basestring):
            job_ids = [job_ids]

        if len(job_ids) == []: 
            return
        job_ids = frozenset(job_ids)
        sleep_time = 1
        while job_ids.intersection(self.running_jobs()):
            time.sleep(sleep_time)
            if sleep_time < 100:
                sleep_time += 0.25
        return True

    def _set_job_name(self, job_name):
        has_log_dir = os.access('logs/', os.W_OK)
        kwargs = self.kwargs
        kwargs["J"] = job_name
        kwargs["e"] = kwargs["J"] + ".%J"
        kwargs["o"] = kwargs["J"] + ".%J"
        if "[" in job_name:
            kwargs["e"] += ".%I"
            kwargs["o"] += ".%I"
        kwargs["e"] += ".err"
        kwargs["o"] += ".out"
        if has_log_dir:
            for i in "oe":
                kwargs[i] = "logs/" + kwargs[i]
        self.kwargs = kwargs
        self._job_name = job_name

    job_name = property(_get_job_name, _set_job_name)

    def _kwargs_to_flag_string(self):
        kwargs = self.kwargs
        s = "%s" % self.__class__.__name__
        for k, v in kwargs.items():
            # quote if needed.
            if v and (v[0] not in "'\"") and any(tok in v for tok in "[="):
                v = "\"%s\"" % v
            dash = " " + ("-" if len(k) == 1 else "--")
            s += dash + k + ("" if v is None else (" " + str(v)))
        return s

    def __call__(self, input_string=None):
        # TODO: submit the job and return the job id.
        # and write entire command to kwargs["e"][:-4] + ".sh"
        if input_string is None:
            assert len(self.args) == 1
            command = str(self)
        else:
            command = "echo \"%s\" | %s" % (input_string, str(self))
        if self.verbose:
            print >>sys.stderr, command
        p = sp.Popen(command, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()
        if p.returncode != 0:
            raise BSubException(command + " | " + str(p.returncode))
        res = p.stdout.read()
        if not ("is submitted" in res and p.returncode == 0):
            raise BSubException(res)
        job = res.split("<", 1)[1].split(">", 1)[0]
        return job

    def __str__(self):
        return self.command

if __name__ == "__main__":
    import doctest
    doctest.testmod()
