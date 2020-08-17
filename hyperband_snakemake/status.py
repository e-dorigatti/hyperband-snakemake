import os
import math


def bracket_status(idx, path):
    stages_count = 0
    for fname in os.listdir(path):
        if fname.startswith('stage-'):
            stages_count += 1

    current_stage_dir = os.path.join(path, f'stage-{stages_count - 1}')
    config_status = {}
    results = []
    completed = running = pending = failed = 0
    for dir_name in os.listdir(current_stage_dir):
        if dir_name.startswith('config-'):
            conf_dir = os.path.join(current_stage_dir, dir_name)
            conf_nr = int(dir_name.split('-')[1])
            status = 0
            for i, fname in enumerate(os.listdir(conf_dir)):
                if fname == 'result':
                    with open(os.path.join(conf_dir, fname)) as f:
                        res = float(f.read())
                        if math.isfinite(res):
                            results.append((conf_nr, res))
                            status = 2
                            completed += 1
                        else:
                            status = 3
                            failed += 1
                    break

            if i == 0:
                pending += 1
            elif status == 0:
                # running if there is no result file but some file
                # other than the configuration
                running += 1
                status = 1

            config_status[conf_nr] = status

    print(f'Bracket {idx} - Stages completed: {stages_count - 1}')
    print(f'  Stage {stages_count} - {len(config_status)} configurations')
    print(f'    | Completed (C) | Failed (F) | In progress (R) | Pending (.) | Total |')
    print(f'    | {completed:>13d} | {failed:>10d} | {running:>15d} | {pending:>11d} | {len(config_status):>5d} |')
    print()
    for i in range(0, len(config_status), 25):
        print('     ', ' '.join([
            ''.join([
                ['.', 'R', 'C', 'F', '?'][config_status.get(k, -1)]
                for k in range(j, min(j + 5, len(config_status)))
            ]) for j in range(i, i + 25, 5)
        ]))

    results.sort(key=lambda x: x[1])
    count = min(3, len(results))
    if count > 0:
        print('\n  Top completed configuration(s):')
        for i in range(count):
            conf, loss = results[i]
            print(f'    {i + 1}. {loss:.4f} - Conf. {conf}')

    print()


def print_status(search_dir):
    bracket_count = 0
    for fname in os.listdir(search_dir):
        if fname.startswith('bracket-'):
            bracket_count += 1

    for b in range(bracket_count):
        bracket_status(b, os.path.join(search_dir, f'bracket-{b}'))
