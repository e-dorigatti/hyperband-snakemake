Hyperband on Snakemake
===


Do you have a medium-to-large-scale hyper-parameter search to run, and need a
way to orchestrate this process? This is the solution. Based on Hyperband [1]
and Snakemake [2], this tool will orchestrate the whole process for you. How is
it different from the other implementations you can easily find elsewhere?

 1. **Easy to debug:** The exact configuration used for each hyper-parameter
    setting is safely stored on disk. All intermediate results are saved, too.
 2. **Distributed:** Thanks to Snakemake, training can be offloaded to a cluster
    manager such as [Slurm][slurm] (see example below), enabling effortless and
    _massive_ parallel training.
 3. **Fail-Safe:** If the training process of a configuration fails, the result
    of previously-run configurations are safely preserved on-disk, and
    currently-running configurations allowed to terminate normally. After the
    bug is fixed, the search can resume from where it was interrupted.
 4. **Language-agnostic:** You can launch training scripts made with _any_
    technology: they only need to read a configuration file and write a file
    with a numerical result.

Note: to use this tool, you must adapt it to your system. See the section named
_Customization_ for instructions.

# Installation
Can be installed via pip:

```
pip install git+https://github.com/e-dorigatti/hyperband-snakemake
```

Or clone the repo, create a conda environment (optional) and install the
required packages:

```
> conda create --file packages.txt -c conda-forge -c bioconda -n hyperband-snakemake
> conda activate hyperband-snakemake
```

# Example
Briefly, Hyperband is a random hyper-parameter search algorithm that smartly
allocates budget to promising configurations. This is done by running all
configurations with a small budget, then obtaining the top half/third/fourth and
running them with two/three/four times larger budget, so that the cost for each
stage remains the same. To know whether it is better to start with many
configurations and small budget, or fewer initial configuration with larger
budget, Hyperband creates several brackets with different trade-offs. A
practical example follows.

First, obtain the plan of the hyper-parameter search. Suppose we want to
evaluate each hyper-parameter configuration by performing ten-folds
cross-validation repeated two times. Further, suppose we want to advance the top
third of configurations to the next stage (the suggested option), and can spare
5**3=243 units of budget for each bracket. We set one budget unit to correspond
to one training epoch, and know that our model requires 10 seconds (0.0028
hours) to perform one epoch on the dataset. These parameters translate to the
following search structure:

```
> hyband generate 3 3 \
    --repetitions 2 --folds 10 \
    --guaranteed-budget 3 \
    --cost-one-epoch-full-dataset 0.0028 \
    --output-dir my-search \
    --random-seed 123456

Hyperband Search - η: 3 S: 3 R: 27 B: 108  (cost: 21.32)
  Bracket 0 (cost: 5.44)
    Stage 0 - 27 configurations each with budget 1.0 (cost: 1.36)
    Stage 1 - 9 configurations each with budget 3.0 (cost: 1.36)
    Stage 2 - 3 configurations each with budget 9.0 (cost: 1.36)
    Stage 3 - 1 configurations each with budget 27.0 (cost: 1.36)
  Bracket 1 (cost: 4.99)
    Stage 0 - 12 configurations each with budget 3.0 (cost: 1.81)
    Stage 1 - 4 configurations each with budget 9.0 (cost: 1.81)
    Stage 2 - 1 configurations each with budget 27.0 (cost: 1.36)
  Bracket 2 (cost: 5.44)
    Stage 0 - 6 configurations each with budget 9.0 (cost: 2.72)
    Stage 1 - 2 configurations each with budget 27.0 (cost: 2.72)
  Bracket 3 (cost: 5.44)
    Stage 0 - 4 configurations each with budget 27.0 (cost: 5.44)
```

Where each stage uses the best configurations in the previous stage of the same
bracket. The indicated cost is in hours (the same unit as the parameter on the
command line), and considers the cross-validation structure (with ten folds, one
epoch requires about 90% of the time needed for the full dataset, i.e. nine
seconds. One budget unit then equals 2x10x9=180 seconds, which translates to
12). The wall-clock time can be of course reduced with parallel training.

This generator will also create a folder hierarchy under `my-search`, splitting
brackets, stages, and configurations.

```
> tree my-search
my-search
├── bracket-0
│   └── stage-0
│       ├── config-0
│       │   └── config
│       ├── config-1
│       │   └── config
│       └── ...
├── bracket-1
│   └── stage-0
│       ├── config-0
│       │   └── config
│       ├── config-1
│       │   └── config
│       └── ...
├── ...
├── run.sh
└── Snakefile
```

Each folder will contain one random configuration:

```
> cat my-search/bracket-2/stage-0/config-16/config
folds: 10
repetitions: 2
cv_seed: 109090
learning_rate: 0.001
C: 0.01
solver: saga
penalty: l1
```

That is generated from a [Jinja2][jinja] template that looks like this:

```
folds: {{ folds }}
repetitions: {{ repetitions }}
cv_seed: {{ range(1000000) | random }}
learning_rate: {{ [1e-5, 1e-4, 1e-3, 1e-2, 1e-1] | random }}
C: {{ [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0] | random }}
{% with solver = ['lbfgs', 'saga'] | random %}
solver: {{ solver }}
{% if solver == 'lbfgs' %}
penalty: l2
{% else %}
penalty: l1
{% endif %}
{% endwith %}
```

The whole process can now be run via Snakemake:

```
snakemake --snakefile my-search/Snakefile
```

The example provided fits a logistic regression model from scikit-learn to the
iris dataset, using one iteration per budget unit. The entire search should require
a few minutes (can be sped up via e.g. `--cores 8`) and result in an accuracy of
98% (averaged across folds and repetitions), visible from one of the last lines
of the log:

```
Job counts:
        count   jobs
        1       find_overall_best
        1
[('my-search/bracket-1/stage-4/config-0/result', -0.9800000000000001), ...
```

The best configuration is also saved in the search root directory (`my-search/config`).

Now, paired to each configuration, you find the negative average accuracy (the
Snakefile is designed to find the configuration with the minimum result):

```
> cat my-search/bracket-2/stage-0/config-16/result
-0.5666666666666667
```

And log file:

```
> cat my-search/bracket-2/stage-0/config-16/log.log
INFO:root:Invoked with configuration file dev/sample-hb/bracket-2/stage-0/config-16/config
INFO:root:Invoked with budget 9
INFO:root:Loaded configuration: {'folds': 10, 'repetitions': 2, 'cv_seed': 109090, 'learning_rate': 0.001, 'C': 0.01, 'solver': 'saga', 'penalty': 'l1'}
INFO:root:Accuracy of repetition 0, fold 0: 0.467
INFO:root:Accuracy of repetition 0, fold 1: 0.533
INFO:root:Accuracy of repetition 0, fold 2: 0.667
...
INFO:root:Accuracy of repetition 1, fold 7: 0.467
INFO:root:Accuracy of repetition 1, fold 8: 0.533
INFO:root:Accuracy of repetition 1, fold 9: 0.667
INFO:root:Mean accuracy: 0.567
```

Note that, since we used random seeds throughout, these results should be fully
reproducible.

# Visualizing search status
Since a Hyperband search can take many days, a simple utility to see the ongoing
progress is provided:

```
> hyband status my-search
Bracket 0 - Stages completed: 0
  Stage 0 - 81 configurations
    | Completed (C) | Failed (F) | In progress (R) | Pending (.) | Total |
    |            12 |          4 |               8 |          57 |    81 |
    |               |            |                 |             |       |

     0  ...F. ...C. .CC.. ..CC. ....R    ..C.. ..C.. ..... CRR.C C...C
    50  ..RR. .F... .R... RF... CF...    ...R. .

  Top completed configuration(s):
    1. 0.1508 - Conf. 68
    2. 0.1590 - Conf. 50
    3. 0.1624 - Conf. 56

Bracket 1 - Stages completed: 0

(output truncated)
```

This will simply scan the directory looking for configuration or result files
indicating progress. A configuration is deemed "in progress" if its folder does not
contain the result file, but contains files or folders other than the configuration
itself, such as log files, TensorBoard's summary folders, etc. A configuration is
deemed "failed" if the result file contains `nan` or `inf`. Note that configurations
that terminated abnormally without writing such a result file, e.g. because of an
unhandled exception, are still counted as "in progress". You should check Snakemake's
logs to determine whether a configuration is still running or has failed.

# Customization
In its present state, the generator script creates by default the logistic
regression example explained above, but adapting it to your needs is easy:

 1. Write a training script, similar to the [provided example][train-tmpl], that
    takes as command line arguments the path to a file with the hyper-parameters
    and the allocated budget. It should write a numeric value to be minimized in
    the search process to a file called `result` in the same directory as the
    configuration.
 2. Customize the [random configuration template][config-tmpl] that is read by
    the training script. Thanks to [Jinja2][jinja], the generation of random
    hyper-parameters is contained in this template file and executed when you
    run the generation command. It can contain some custom logic, e.g. in the
    provided example the type of regularization (L1 or L2) is chosen based on
    the solver (SAGA or LBFGS). You are of course not restricted to any
    particular file type, as long as it is text-based.
 3. Customize the [bash launch script][run-tmpl] that is invoked by the
    Snakefile and launches the training script you wrote in point (1). This can
    be used to provide further options to the training script, collect logs,
    clean temporary outputs, submit the training script to a cluster manager,
    and so on. If you feel this piece is redundant, you can call the training
    script directly from the Snakefile.
 4. (Optional) Customize the [Snakefile][snake-tmpl], which contains the logic
    to run the script you customized in point (3) and promote good
    configurations to the next stage. You do not need to modify this template
    unless you require additional functionality from Snakemake, in which case
    you can modify the rule marked with a comment to suit your needs.

These templates are rendered and saved in the output directory. This directory
is now entirely portable, you just have to update `config['base_dir']` in the
Snakefile. This variable should contain the path of the root directory of the
search configurations, either absolute or relative to where you will run
`snakemake`.

You can pass `--template-dir` to the generator to make it use your custom
templates. Simply create a copy of the provided directory, modify to your needs,
and run the search:

```
> cp -r hyperband_snakemake/templates my-templates
> vim my-templates/config
> vim my-templates/run.sh
> vim my-templates/Snakefile
> python generator.py --template-dir my-templates ...
> snakemake ...
```

# Running with Slurm
Once you have customized the configuration template, it is quite easy to run a
hyperband search on a cluster managed by [slurm][slurm], you just need to modify
the [launch script template][run-tmpl] to invoke `srun`, like so:

```
srun --time 24:00:00 --gpus-per-task 1 --cpus-per-task 6 --mem 92G \
    --output "$1/slurm-%j.out" --error "$1/slurm-%j.err" \
    <path-to-python> train.py "$1/config" --output-dir "$1" --max-epochs "$2"
```

Where `<path-to-python>` points to the python interpreter in a suitable virtual
environment (but note that you are not restricted to use Python!).

Another option is to use `sbatch` combined with `--wait`, which has the
advantage that you can use a heredoc:

```
sbatch --wait << EOF
#!/bin/bash

#SBATCH <other options>

conda activate <env>
python train.py "$1/config" --output-dir "$1" --max-epochs "$2"
EOF
```

Then, use `nohup` (or tmux, or screen) to fire-and-forget Snakemake from the
login node:

```
> nohup snakemake --snakefile my-search/Snakefile --latency-wait 60 -j 100 > my-search/log.out &
```

Which will schedule up to 100 jobs at the same time. `latency-wait` tells
Snakemake to wait for the result files for up to 60 seconds before failing the
job. It may be necessary to account for possible latencies when the results
saved in a networked file-system.

# Random Search
This tool can also be used to run a simple random search without the full
Hyperband machinery simply by restricting the search to the first stage of the
first bracket:

```
$ hyband generate 4 3 --bracket 0 --last-stage 0
Hyperband Search - η: 3 S: 4 R: 81 B: 405  (cost: 81.00)
  Bracket 0 (cost: 81.00)
    Stage 0 - 81 configurations each with budget 1.0 (cost: 81.00)
```

Note that the launch script `run.sh` will still get a budget of 1 which you
should obviously ignore. As above, the root of the output folder will contain
the best configuration at the end of the search.

# Cross-validation
It is possible to modify the launch script template to use cross-validation or bootstrap resampling to evaluate a single hyperparameter configuration.
In this case, the launch script would run multiple trainings with the same config and aggregate the results into an overall average score that will be used to rank the hyperparameters.
The advantage of doing this in the launch script rather than in the training script is that these training runs can be run in parallel.

In the specific case of SLURM, one can leverage job arrays to run cross-validation (for example), using the environment variable `SLURM_ARRAY_TASK_ID` to find which fold the script is supposed to use for validation:

```
#!/bin/bash
set -x

echo "Called with base directory $1 and budget $2"

# separate log files for each job in the array
sbatch ... -o "$1/log%a.out" -e "$1/log%a.err" --wait --array 0-4 << EOF
#!/bin/bash
source ~/.bashrc
conda activate env

# run a single fold of 5-fold cross-validation
# the validation score of fold k will be saved in the file result-k
python train.py $1/config --epochs $2 \
    --this-cv-fold $LURM_ARRAY_TASK_ID --total-cv-folds 5 \
    --output-file $1/result-$LURM_ARRAY_TASK_ID
EOF

# sbatch will wait until all jobs in the array finished running

if [[ $? -ne 0 ]]; then
  # there was an error in at least one of the jobs, abort with same error code
  exit $?
fi

# read all the result files, compute the average, and save in the result file
find $1 -name "result-*" | xargs awk \
  '/nan/{found_nan=1} {n=n+$0; c=c+1} END {if(found_nan) { print "nan" } else {print n/c}}' \
  > $1/result
```





# References
[1]: Li, L., Jamieson, K., DeSalvo, G., Rostamizadeh, A. and Talwalkar, A., 2017. _Hyperband: A novel bandit-based approach to hyperparameter optimization._ The Journal of Machine Learning Research, 18(1), pp.6765-6816. http://www.jmlr.org/papers/volume18/16-558/16-558.pdf

[2]: Köster, Johannes and Rahmann, Sven. _Snakemake - A scalable bioinformatics workflow engine_. Bioinformatics 2012. https://academic.oup.com/bioinformatics/article/28/19/2520/290322

 [jinja]: https://jinja.palletsprojects.com/en/2.11.x/
 [run-tmpl]: hyperband_snakemake/templates/run.sh
 [snake-tmpl]: hyperband_snakemake/templates/Snakefile
 [train-tmpl]: hyperband_snakemake/example/train.py
 [config-tmpl]: hyperband_snakemake/templates/config
 [python-cfg]: https://martin-thoma.com/configuration-files-in-python/#python-configuration-file
 [slurm]: https://slurm.schedmd.com/overview.html
