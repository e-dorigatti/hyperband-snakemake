Hyperband on Snakemake
===

Do you have a medium-scale hyper-parameter search to run, and need a way to
orchestrate this process? This is the solution. Based on Hyperband [1] and
Snakemake [2], this tool will orchestrate the whole process for you. How is it
different from the other implementations you can easily find elsewhere?

 1. The exact configuration used for each hyper-parameter setting is safely
    stored on disk.
 2. All intermediate results are saved, too.
 3. Thanks to Snakemake, training can be offloaded to a cluster manager such as
    Slurm, enabling effortless and _massive_ parallel training.
 4. Even though this tool is written in Python, you can launch training scripts
    made with _any_ technology: they only need to read a configuration file and
    write a file with a numerical result.

Saving everything on disk proves advantageous when your hyper-parameter search
must run for weeks, as it allows you to check the progress, spot early mistakes,
perform further iterations after the process ends (e.g., shoot for the very best
configuration through Bayesian optimization, using the hyper-band results to
bootstrap that model). Importantly, by decoupling training and search, you do
not risk losing all your work because of some random bug that would crash the
training process.

# Installation
Can be installed via pip:

```
pip install git+https://github.com/e-dorigatti/hyperband-snakemake/
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
> python generator.py 5 3 \
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
brackets, stages, and configurations. Each folder will contain one random
configuration:

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

# Customization
In its present state, the generator script creates by default the logistic
regression example just explained, but adapting it to your needs is easy. This
script uses [Jinja2](https://jinja.palletsprojects.com/en/2.11.x/) to render
three templates:

 1. The [Snakefile](hyperband_snakemake/templates/Snakefile), containing the
    logic to run the script and promote good configurations to the next stage.
 2. The [bash launch script](hyperband_snakemake/templates/run.sh) that is
    invoked by the Snakefile and runs the [sample training
    script](hyperband_snakemake/example/train.py). The training script should
    take as arguments the configuration file and the budget, and write the
    result to a file named `result` in the same directory as the configuration
    file (if you are maximizing a metric, write its negation instead).
 3. The [random configuration](hyperband_snakemake/templates/config) that is
    read by the training script. Thanks to Jinja2, the actual generation of
    random parameters is contained in the template file itself. There can be
    some custom logic, e.g. in the provided example the type of regularization
    (L1 or L2) is chosen based on the solver (SAGA or LBFGS). You are of course
    not restricted to any particular type of configuration, as long as it is
    text-based. For example, you can directly produce a [Python configuration
    file](https://martin-thoma.com/configuration-files-in-python/#python-configuration-file)
    and import it in the training script (if you are using Python, that is).
    This would save you the effort of writing code to read the configuration and
    instantiate the specified model.
 
These templates are rendered and saved in the output directory. This directory
is now entirely portable, you just have to update `config['base_dir']` in the
Snakefile. This variable should contain the path of the output dir, either
absolute or relative to where you will run `snakemake`.

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


# References
[1]: Li, L., Jamieson, K., DeSalvo, G., Rostamizadeh, A. and Talwalkar, A., 2017. _Hyperband: A novel bandit-based approach to hyperparameter optimization._ The Journal of Machine Learning Research, 18(1), pp.6765-6816. http://www.jmlr.org/papers/volume18/16-558/16-558.pdf

[2]: Köster, Johannes and Rahmann, Sven. _Snakemake - A scalable bioinformatics workflow engine_. Bioinformatics 2012. https://academic.oup.com/bioinformatics/article/28/19/2520/290322
