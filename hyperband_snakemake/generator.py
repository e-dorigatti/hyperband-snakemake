import random

import click

from hyperband_snakemake.search import HbSearch
from hyperband_snakemake.writer import HbWriter


def run_generation(output_dir, smax, eta, cost_one_epoch_full_dataset, repetitions, folds,
                   random_seed, guaranteed_budget, overwrite, template_dir, config_template,
                   run_template, snakefile_template, bracket):
    random.seed(random_seed)

    unit_time = 1.0
    if cost_one_epoch_full_dataset is not None and repetitions is not None and folds is not None:
        epoch_cost = cost_one_epoch_full_dataset * \
            ((1 - 1 / folds) if folds > 1 else 1)
        unit_time = repetitions * folds * epoch_cost

    search = HbSearch(
        smax, eta, unit_time=unit_time, folds=folds,
        repetitions=repetitions, guaranteed_budget=guaranteed_budget,
        allowed_brackets=bracket
    )

    search.pprint()

    print()
    if output_dir is not None:
        print('Saving random configurations to', output_dir)
        writer = HbWriter(config_template, run_template,
                          snakefile_template, template_dir)
        writer.write_search(search, output_dir, overwrite)
    else:
        print('Not saving configurations (specify target directory with --output-dir)')

