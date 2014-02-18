"""
 create a job with a job name and any extra args to send to lsf
 in the case below.
    -J some_job -e some_job.%J.err -o some_job.%J.out
 will be automatically added to the command.
>>> sub = bsub("some_job", R="rusage[mem=1]", verbose=True)

# submit a job via call'ing the sub object with the command to run.
# the return value is the numeric job id.
>>> djob = sub("date")
>>> djob.job_id.isdigit() and djob.job_id != '0'
True

# 2nd argument can be a shell script, in which case
# the call() is empty.
#>>> bsub("somejob", "run.sh", verbose=True)()

# dependencies:
>>> job_id = bsub("sleeper", verbose=True, n=2)("sleep 2").job_id
>>> bsub.poll(job_id)
True

# run one job, `then` another when it finishes
>>> res = bsub("sleepA", verbose=True)("sleep 2").then("sleep 1", job_name="sleepB")
>>> bsub.poll(res.job_id)
True

# again: run one job, `then` another when it finishes with different
# LSF options
>>> res = bsub("sleepA", verbose=True)("sleep 2").then("sleep 1", job_name="sleepB", R="rusage[mem=1]")
>>> bsub.poll(res.job_id)
True

# cleanup
>>> import os, glob
>>> os.unlink('sleeper.%s.err' % job_id)
>>> os.unlink('sleeper.%s.out' % job_id)
>>> os.unlink('some_job.%s.err' % djob.job_id)
>>> os.unlink('some_job.%s.out' % djob.job_id)
>>> for f in glob.glob('sleep1.*.err') + glob.glob('sleep2.*.err') + \
         glob.glob('sleep1.*.out') + glob.glob('sleep2.*.out'):
...     os.unlink(f)

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
        self.job_id = None

    def __int__(self):
        return int(self.job_id)

    def __long__(self):
        return long(self.job_id)

    @property
    def command(self):
        return self._kwargs_to_flag_string() \
            + ((" < %s" % self.args[0]) if len(self.args) else "")

    def _get_job_name(self):
        return self._job_name

    @classmethod
    def running_jobs(self):
        return [x.split()[0] for x in sp.check_output(["bjobs"]).rstrip().split("\n")[1:]]

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

    @classmethod
    def _cap(self, max_jobs):
        sleep_time = 1
        while len(self.running_jobs()) >= max_jobs:
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
            if isinstance(v, (float, int)):
                pass
            elif v and (v[0] not in "'\"") and any(tok in v for tok in "[="):
                v = "\"%s\"" % v
            s += " -" + k + ("" if v is None else (" " + str(v)))
        return s


    def __call__(self, input_string=None, job_cap=None):
        # TODO: submit the job and return the job id.
        # and write entire command to kwargs["e"][:-4] + ".sh"
        if job_cap is not None:
            self._cap(job_cap)
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
        self.job_id = job
        return self

    def then(self, input_string, job_name=None, **kwargs):
        """
        >>
        """
        # ability to set/reset kwargs
        self.kwargs.update(kwargs)

        bs = bsub(job_name or self.job_name, *self.args, **self.kwargs)
        bs.verbose = self.verbose
        # NOTE: could use name*, but here force relying on single job
        # cant get exit 0 to work on our cluster.
        bs.kwargs['w'] = '"done(%i)"' % int(self)

        try:
            res = bs(input_string)
        finally:
            res.kwargs.pop('w')
            return res

    def __str__(self):
        return self.command

if __name__ == "__main__":
    import doctest
    doctest.testmod()
