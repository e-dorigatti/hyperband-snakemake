import random

import click

from hyperband_snakemake.search import HbSearch
from hyperband_snakemake.writer import HbWriter


@click.command()
@click.argument('smax', type=int)
@click.argument('eta', type=int)
@click.option('--cost-one-epoch-full-dataset', '-t', type=float,
              help='Cost to train for one epoch on the full dataset')
@click.option('--repetitions', '-r', type=int, default=1,
              help='Number of repetitions for cross-validation')
@click.option('--folds', '-k', type=int, default=5,
              help='Number of folds for cross-validation')
@click.option('--random-seed', type=int, help='Seed for the random generator')
@click.option('--guaranteed-budget', type=int, default=0,
              help='Minimum budget added to each configuration')
@click.option('--output-dir', '-o', type=click.Path(),
              help='Base directory to store the generated configurations')
@click.option('--overwrite', is_flag=True,
              help='Overwrite existing configurations')
@click.option('--template-dir', type=str,
              help='Path to the folder containing the templates')
@click.option('--config-template', default='config',
              help='Path to the configuration template (relative to the template dir.)')
@click.option('--run-template', default='run.sh',
              help='Path to the launch template (relative to the template dir.)')
@click.option('--snakefile-template', default='Snakefile',
              help='Path to the snakefile template (relative to the template dir.)')
def main(output_dir, smax, eta, cost_one_epoch_full_dataset, repetitions, folds,
         random_seed, guaranteed_budget, overwrite, template_dir, config_template,
         run_template, snakefile_template):
    '''
    Uses the hyperband algorithm to generate a structured randomized hyper-parameter search.
    '''
    random.seed(random_seed)

    unit_time = 1.0
    if cost_one_epoch_full_dataset is not None and repetitions is not None and folds is not None:
        epoch_cost = cost_one_epoch_full_dataset * \
            ((1 - 1 / folds) if folds > 1 else 1)
        unit_time = repetitions * folds * epoch_cost

    search = HbSearch(
        smax, eta, unit_time=unit_time, folds=folds,
        repetitions=repetitions, guaranteed_budget=guaranteed_budget
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


if __name__ == '__main__':
    main()

