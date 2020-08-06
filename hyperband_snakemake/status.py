import os


def bracket_status(idx, path):
    stages_completed = stages_count = 0
    for fname in os.listdir(path):
        if fname.startswith('stage-'):
            stages_count += 1
            if os.path.exists(os.path.join(path, fname, 'config')):
                stages_completed += 1

    current_stage_dir = os.path.join(path, f'stage-{stages_completed}')
    config_status = []

    results = []
    completed = running = pending = 0
    for dir_name in os.listdir(current_stage_dir):
        if dir_name.startswith('config-'):
            conf_dir = os.path.join(current_stage_dir, dir_name)
            conf_nr = int(dir_name.split('-')[1])
            status = 0
            for i, fname in enumerate(os.listdir(conf_dir)):
                if fname == 'result':
                    status = 2
                    completed += 1
                    with open(os.path.join(conf_dir, fname)) as f:
                        results.append((conf_nr, float(f.read())))
                    break

            if i == 0:
                pending += 1
            elif status == 0:
                # running if there is no result file but some file
                # other than the configuration
                running += 1
                status = 1

            config_status.append(status)

    print(f'Bracket {idx} - Stages completed: {stages_completed}')
    print(f'  Stage {stages_completed} - {len(config_status)} configurations')
    print(f'    | Completed (x) | In progress (~) | Pending (.) | Total |')
    print(f'    | {completed:>13d} | {running:>15d} | {pending:>11d} | {len(config_status):>5d} |')
    print()
    for i in range(0, len(config_status), 25):
        print('     ', ' '.join(''.join((
            ['.', '~', 'x'][c] for c in config_status[j:j+5])
        ) for j in range(i, i + 25, 5)))

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
