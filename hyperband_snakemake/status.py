import math
import os
from enum import Enum
from typing import Optional, Tuple


class Status(Enum):
    PENDING = '.'
    RUNNING = 'R'
    COMPLETED = 'C'
    FAILED = 'F'
    UNKNOWN = '?'


def get_config_status(conf_dir: str) -> Tuple[Status, Optional[float]]:
    status = Status.PENDING
    res = None
    for fname in os.listdir(conf_dir):
        if fname == 'result':
            with open(os.path.join(conf_dir, fname)) as f:
                res = float(f.read())
                if math.isfinite(res):
                    status = Status.COMPLETED
                else:
                    status = Status.FAILED
            break
        if fname != 'config':
            # running if there is no result file
            # but some file other than the configuration
            status = Status.RUNNING

    return status, res


def bracket_status(idx: int, path: str) -> None:
    stages_count = 0
    for fname in os.listdir(path):
        if fname.startswith('stage-'):
            stages_count += 1

    current_stage_dir = os.path.join(path, f'stage-{stages_count - 1}')
    config_status = {}
    results = []
    status_counts = {s: 0 for s in Status}
    for dir_name in os.listdir(current_stage_dir):
        if dir_name.startswith('config-'):
            status, result = get_config_status(os.path.join(current_stage_dir, dir_name))

            conf_nr = int(dir_name.split('-')[1])
            config_status[conf_nr] = status
            status_counts[status] += 1
            if status == Status.COMPLETED:
                assert result is not None
                results.append((conf_nr, result))

    print('Bracket {} - Stages completed: {}\n'
          '  Stage {} - {} configurations\n'
          '    | Completed (C) | Failed (F) | In progress (R) | Pending (.) | Total |\n'
          '    | {:>13d} | {:>10d} | {:>15d} | {:>11d} | {:>5d} |'.format(
              idx, stages_count - 1, stages_count, len(config_status),
              status_counts[Status.COMPLETED], status_counts[Status.FAILED],
              status_counts[Status.RUNNING], status_counts[Status.PENDING],
              len(config_status)
          ))

    for i in range(0, len(config_status), 50):
        print(f' {i:>5d} ', '   '.join([
            ' '.join([''.join([
                config_status.get(k, Status.UNKNOWN).value
                for k in range(j, min(j + 5, len(config_status)))
            ]) for j in range(ll, ll + 25, 5)])
            for ll in range(i, i + 50, 25)
        ]))

    results.sort(key=lambda x: x[1])
    count = min(3, len(results))
    if count > 0:
        print('\n  Top completed configuration(s):')
        for i in range(count):
            conf, loss = results[i]
            print(f'    {i + 1}. {loss:.4f} - Conf. {conf}')

    print()


def print_status(search_dir: str) -> None:
    bracket_count = 0
    for fname in os.listdir(search_dir):
        if fname.startswith('bracket-'):
            bracket_count += 1

    for b in range(bracket_count):
        bracket_status(b, os.path.join(search_dir, f'bracket-{b}'))
