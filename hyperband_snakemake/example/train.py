import logging
import os

import click
import yaml
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold


@click.command()
@click.argument('config-file', type=click.Path())
@click.option('--budget', '-b', type=int)
def main(config_file: str, budget: int) -> None:
    config_dir, _ = os.path.split(config_file)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(config_dir, 'log.log'))
        ]
    )
    logger = logging.getLogger()

    logger.info('Invoked with configuration file %s', config_file)
    logger.info('Invoked with budget %d', budget)

    # Read the provided YAML configuration
    with open(config_file) as f:
        config = yaml.safe_load(f)
    logger.info('Loaded configuration: %s', config)

    # Run repeated, stratified cross-validation
    data = load_iris()
    accuracies = []
    for i in range(config['repetitions']):
        kfold = StratifiedKFold(config['folds'], shuffle=True,
                                random_state=config['cv_seed'] + i)
        splits = kfold.split(data['data'], data['target'])
        for j, (train_idx, test_idx) in enumerate(splits):
            # Train the model with the provided hyper-parameters
            model = LogisticRegression(
                max_iter=budget,
                solver=config['solver'],
                penalty=config['penalty'],
                C=config['C'],
            )
            model.fit(data['data'][train_idx], data['target'][train_idx])
            accuracy = model.score(data['data'][test_idx], data['target'][test_idx])
            accuracies.append(accuracy)
            logger.info('Accuracy of repetition %d, fold %d: %.3f', i, j, accuracy)

    mean_acc = sum(accuracies) / len(accuracies)
    logger.info('Mean accuracy: %.3f', mean_acc)

    # Write average accuracy to the output file
    with open(os.path.join(config_dir, 'result'), 'w') as f:
        f.write(f'{-mean_acc}\n')


if __name__ == '__main__':
    main()
