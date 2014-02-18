bsub
====

python wrapper to submit jobs to bsub (and later qsub)

Authors
------
@brentp, @brwnj


Example
-------

```python
>>> from bsub import bsub
>>> sub = bsub("some_job", R="rusage[mem=1]", verbose=True)

# submit a job via call'ing the sub object with the command to run.
# the return value is the numeric job id.
>>> print sub("date").job_id.isdigit()
True

# 2nd argument can be a shell script, in which case
# the call() is empty.
#>>> bsub("somejob", "run.sh", verbose=True)()

# dependencies:
>>> job_id = bsub("sleeper", verbose=True)("sleep 2").job_id
>>> bsub.poll(job_id)
True

```


Chaining
--------

It's possible to specify dependencies to LSF using a flag like:

   bsub -w 'done("other-name")' < myjob

We make this more pythonic with:

```Python

>>> j = sub('sleep 1').then('sleep 2')

```
which will wait for the first job `sleep 1` to complete
before running the second job `sleep 2`. These can be chained as:

```Python

j = sub('myjob')
j2 = j('sleep 1')
j3 = j2.then('echo "hello"')
j4 = j3.then('echo "world"')
j5 = j4.then('my scripts.p')

# or:

j('sleep 1').then('echo "hello"').then('echo "world"')

```
Where each job in `.then()` is not run until the preceding job
is `done()` according to LSF.

Bioinformatics example of chaining:

This would submit jobs for positive and negative strand coverage in parallel.
Each strand submitting jobs that run serially.

```Python

from bsub import bsub

submit = bsub("bam2bg", verbose=verbose)

# convert bam to stranded bg then bw
sample = "subject_1"
chrom_sizes = "chrom_sizes.txt"

#  submit jobs by strand for parallel processing
for symbol, strand in izip(["+", "-"], ["pos", "neg"]):

    bigwig = sample + "_" + strand + ".bw"
    bedgraph = sample + "_" + strand + ".bedgraph"

    bam_to_bg = ("bedtools genomecov -strand %s -bg "
                    "-ibam %s | bedtools sort -i - > %s") % (symbol, bam, bedgraph)
    bg_to_bw = "bedGraphToBigWig %s %s %s" % (bedgraph, chrom_sizes, bigwig)
    gzip_bg = "gzip -f %s" % bedgraph

    # process strand-based steps serially
    # submit first 2 jobs to default queue; final job to 'gzip' queue
    submit(bam_to_bg).then(bg_to_bw, job_name="bg2bw").then(gzip_bg, "gzipbg", q='gzip')

```


Command-Line
------------

use the command-line to poll for running jobs:


```Shell
python -m bsub 12345 12346 12347
```

will block until those 3 jobs finish.
