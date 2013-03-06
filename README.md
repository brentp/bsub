bsub
====

python wrapper to submit jobs to bsub (and later qsub)

Authors
------
@brentp, @brwnj

```python

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

```

or use the command-line to poll for running jobs:


python -m bsub 12345 12346 12347

will block until those 3 jobs finish.
