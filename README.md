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
> python -m hyperband_snakemake generate 5 3 \
    --repetitions 2 --folds 10 \
    --guaranteed-budget 3 \
    --cost-one-epoch-full-dataset 0.0028 \
    --output-dir my-search \
    --random-seed 123456

Hyperband Search (cost: 426.23)
  Bracket 0 (cost: 73.48)
    Stage 0 - 243 configurations each with budget 1.0 (cost: 12.25)
    Stage 1 - 81 configurations each with budget 3.0 (cost: 12.25)
    Stage 2 - 27 configurations each with budget 9.0 (cost: 12.25)
    Stage 3 - 9 configurations each with budget 27.0 (cost: 12.25)
    Stage 4 - 3 configurations each with budget 81.0 (cost: 12.25)
    Stage 5 - 1 configurations each with budget 243.0 (cost: 12.25)
  Bracket 1 (cost: 67.44)
    Stage 0 - 98 configurations each with budget 3.0 (cost: 14.82)
    Stage 1 - 32 configurations each with budget 9.0 (cost: 14.52)
    Stage 2 - 10 configurations each with budget 27.0 (cost: 13.61)
    Stage 3 - 3 configurations each with budget 81.0 (cost: 12.25)
    Stage 4 - 1 configurations each with budget 243.0 (cost: 12.25)
  Bracket 2 (cost: 64.86)
    Stage 0 - 41 configurations each with budget 9.0 (cost: 18.60)
    Stage 1 - 13 configurations each with budget 27.0 (cost: 17.69)
    Stage 2 - 4 configurations each with budget 81.0 (cost: 16.33)
    Stage 3 - 1 configurations each with budget 243.0 (cost: 12.25)
  Bracket 3 (cost: 73.48)
    Stage 0 - 18 configurations each with budget 27.0 (cost: 24.49)
    Stage 1 - 6 configurations each with budget 81.0 (cost: 24.49)
    Stage 2 - 2 configurations each with budget 243.0 (cost: 24.49)
  Bracket 4 (cost: 73.48)
    Stage 0 - 9 configurations each with budget 81.0 (cost: 36.74)
    Stage 1 - 3 configurations each with budget 243.0 (cost: 36.74)
  Bracket 5 (cost: 73.48)
    Stage 0 - 6 configurations each with budget 243.0 (cost: 73.48)
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
> python -m hyperband_snakemake status my-search
Bracket 0 - Stages completed: 0
  Stage 0 - 81 configurations
    | Completed (C) | Failed (F) | In progress (R) | Pending (.) | Total |
    |            12 |        4   |               8 |          57 |    81 |

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
