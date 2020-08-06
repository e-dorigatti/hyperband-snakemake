import click

from hyperband_snakemake.status import print_status
from hyperband_snakemake.generator import run_generation


@click.group()
def main():
    pass


@main.command()
@click.argument('search-dir', type=click.Path())
def status(search_dir):
    '''
    Prints the status of an ongoing search.
    '''
    print_status(search_dir)


@main.command()
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
@click.option('--bracket', '-b', type=int, multiple=True,
              help='Only perform this bracket (multiple allower).')
def generate(*args, **kwargs):
    '''
    Uses the hyperband algorithm to generate a structured,
    randomized hyper-parameter search.
    '''
    run_generation(*args, **kwargs)


if __name__ == '__main__':
    main()
