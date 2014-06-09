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
>>> job_id = bsub("test.sleeper", verbose=True, n=2)("sleep 2").job_id
>>> bsub.poll(job_id)
True

# run one job, `then` another when it finishes
>>> res = bsub("test.sleepA", verbose=True)("sleep 2").then("sleep 1",
...            job_name="test.sleepB")
>>> bsub.poll(res.job_id)
True

# again: run one job, `then` another when it finishes with different
# LSF options
>>> res = bsub("test.sleepA", verbose=True)("sleep 2").then("sleep 1",
...             job_name="test.sleepB", R="rusage[mem=1]")
>>> bsub.poll(res.job_id)
True

>>> bsub("test.sleep-kill")("sleep 100000")
bsub('test.sleep-kill')
>>> bsub.bkill('test.sleep-kill')

# wait on multiple jobs
>>> job1 = sub("sleep 3")
>>> job2 = sub("sleep 3")
>>> job3 = bsub("wait_job", w='"done(%i) && done(%i)"' % (job1, job2),
...             verbose=True)("sleep 1")

# cleanup
>>> import os, glob, time
>>> time.sleep(1)
>>> for f in glob.glob('test.sleep*.err') + glob.glob('test.sleep*.out') + \
         glob.glob('some_job.*.out') + glob.glob('some_job.*.err') + \
         glob.glob('wait_job.*.out') + glob.glob('wait_job.*.err'):
...     os.unlink(f)

"""
import subprocess as sp
import sys
import os
import time
import six

TEST_ONLY = 666

class BSubException(Exception):
    pass

class BSubJobNotFound(BSubException):
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
        s = self.__class__.__name__

        return s + " " + self._kwargs_to_flag_string(self.kwargs) \
            + ((" < %s" % self.args[0]) if len(self.args) else "")

    def _get_job_name(self):
        return self._job_name

    @classmethod

    def running_jobs(self, names=False):
        # grab the integer id or the name depending on whether they requested
        # names=True
        return [x.split(None, 7)[-2 if names else 0]
                for x in sp.check_output(["bjobs", "-w"])\
                           .decode().rstrip().split("\n")[1:]
                           if x.strip()
               ]

    @classmethod
    def poll(self, job_ids, names=False):
        if isinstance(job_ids, six.string_types):
            job_ids = [job_ids]

        if len(job_ids) == []:
            return
        job_ids = frozenset(job_ids)
        sleep_time = 1
        while job_ids.intersection(self.running_jobs(names=names)):
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

    @classmethod
    def _kwargs_to_flag_string(cls, kwargs):
        s = ""
        for k, v in kwargs.items():
            # quote if needed.
            if isinstance(v, (float, int)):
                pass
            elif v and (v[0] not in "'\"") and any(tok in v for tok in "[="):
                v = "\"%s\"" % v
            s += " -" + k + ("" if v is None else (" " + str(v)))
        return s

    def __call__(self, input_string=None, job_cap=None):
        # TODO: write entire command to kwargs["e"][:-4] + ".sh"
        if job_cap is not None:
            self._cap(job_cap)
        if input_string is None:
            assert len(self.args) == 1
            command = str(self)
        else:
            command = "echo \"%s\" | %s" % (input_string, str(self))
        if self.verbose:
            sys.stderr.write(command + '\n')
        if self.verbose == TEST_ONLY:
            self.job_id = TEST_ONLY
            return self
        res = _run(command)
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
            try:
                res.kwargs.pop('w')
                return res
            except UnboundLocalError:
                sys.stderr.write('ERROR: %s\n' % input_string)
                return None

    def __str__(self):
        return self.command

    def __repr__(self):
        return "bsub('%s')" % self.job_name

    def kill(self):
        """
        Kill this job. To kill any job, see the bsub.bkill classmethod
        """
        if self.job_id is None: return
        return bsub.kill(int(self.job_id))

    @classmethod
    def bkill(cls, *args, **kwargs):
        """
        args is a list of integer job ids or string names
        """
        kargs = cls._kwargs_to_flag_string(kwargs)
        if all(isinstance(a, six.integer_types) for a in args):
            command = "bkill " + kargs + " " + " ".join(args)
            _run(command, "is being terminated")
        else:
            for a in args:
                command = "bkill " + kargs.strip() + " -J " + a
                _run(command, "is being terminated")

    @classmethod
    def template(cls, commands, inputs, name_getter=os.path.basename,
            date_fmt="%d-%m-%Y", info_dict={}, **bsub_kwargs):
        """
        for date_fmt, see:
            http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
        bsub_kwargs are passed to bsub.__init__
        info_dict: contains any extra variables to be used in the templates.
                   e.g. {'results': 'some/other/path/'}
        see: https://github.com/brentp/bsub/issues/5 for impetus
        """
        if isinstance(commands, six.string_types):
            commands = [commands]
        import datetime
        now = datetime.datetime.now()
        if isinstance(name_getter, six.string_types):
            import re
            reg = re.compile(name_getter)

            def name_getter(afile):
                match = reg.search(afile)

                info = match.groupdict() if match.groupdict() \
                                         else dict(name=match.group(0)[0])
                if not 'name' in info: info['name'] = os.path.basename(file)
                return info

        else:
            _name_getter = name_getter
            def name_getter(afile):
                r = _name_getter(afile)
                return r if isinstance(r, dict) else dict(name=r)

        def job_info(afile):
            info = name_getter(afile)
            info.update(dict(wd=os.getcwd(), dirname=os.path.dirname(afile),
                            basename=os.path.basename(afile), input=afile,
                            date=now.strftime(date_fmt)))
            info.update(info_dict)
            # make {fq1} and {r1} availabe if input is a fastq.
            if afile.endswith(('.fastq', '.fq', '.fastq.gz', '.fq.gz')):
                info['fq1'] = info['r1'] = afile
            # if there is, e.g. r1='some/f_R1_001.fastq, then auto add
            # r2 = 'some/f_R2_001.fastq
            for r1 in set(['fq1', 'r1', 'FQ1', 'R1']).intersection(info):
                fq1 = info[r1]
                fq2 = info[r1].replace("_R1_", "_R2_")

                if fq1 != fq2 and os.path.exists(fq2):
                    info[r1.replace('1', '2')] = fq2
            return info

        if isinstance(inputs, six.string_types):
            import glob
            inputs = glob.glob(inputs)
        job_ids = []
        for afile in inputs:
            info = job_info(afile)
            job = None
            for i, command in enumerate(commands):
                try:
                    cmd = command.format(**info)
                except KeyError:
                    sys.stderr.write("%r\n" % info)
                    raise
                if i == 0:
                    job = bsub(info['name'], **bsub_kwargs)
                    job_ids.append(job(cmd).job_id)
                else:
                    # TODO: adjust name?
                    job = job.then(cmd)
                    job_ids.append(job.job_id)
        return job_ids


def _run(command, check_str="is submitted"):
    p = sp.Popen(command, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    p.wait()
    if p.returncode == 255:
        raise BSubJobNotFound(command)
    elif p.returncode != 0:
        raise BSubException(command + "[" + str(p.returncode) + "]")
    res = p.stdout.read().strip().decode()
    if not (check_str in res and p.returncode == 0):
        raise BSubException(res)
    # could return job-id from here
    return res

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.REPORT_ONLY_FIRST_FAILURE)
