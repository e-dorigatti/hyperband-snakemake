import os

from jinja2 import Environment, FileSystemLoader, PackageLoader


class HbWriter:
    def __init__(self, config_template, run_template, snakefile_template, template_dir=None):
        self._overwrite_warning = False
        self._config_template = config_template
        self._run_template = run_template
        self._snakefile_template = snakefile_template

        if template_dir is not None:
            loader = FileSystemLoader(template_dir)
        else:
            loader = PackageLoader('hyperband_snakemake', 'templates')

        self._env = Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)

    def render_stage_config(self, index, search, stage):
        tmpl = self._env.get_template(self._config_template)
        rendered = tmpl.render(
            folds=stage.search.folds,
            repetitions=stage.search.repetitions,
            search=search,
            index=index,
        )
        return rendered

    def render_snakefile(self, output_dir, search):
        brackets = [{
            'id': i,
            'max_stage': len(b.stages),
            'num_best': b.stages[-1].n,
            'stages': [{
                'id': j,
                'configs': s.n,
                'budget': int(search.guaranteed_budget + s.r),
                'promote_count': b.stages[j + 1].n if j < len(b.stages) - 1 else 0,
                'promote_epochs': (
                    search.guaranteed_budget + b.stages[j + 1].r
                    if j < len(b.stages) - 1 else None
                ),
            } for j, s in enumerate(b.stages)]
        } for i, b in enumerate(search.brackets)]

        tmpl = self._env.get_template(self._snakefile_template)
        rendered = tmpl.render(
            brackets=brackets, base_dir=output_dir, search=search)
        return rendered

    def render_run(self, search):
        tmpl = self._env.get_template(self._run_template)
        rendered = tmpl.render(search=search)
        return rendered

    @staticmethod
    def _ensure_exists(*parts):
        dd = None
        for p in parts:
            dd = os.path.join(dd, p) if dd is not None else p
            if not os.path.exists(dd):
                os.mkdir(dd)
        return dd

    def _write_to_file(self, string, path, overwrite):
        if isinstance(path, (list, tuple)):
            path = os.path.join(self._ensure_exists(*path[:-1]), path[-1])

        exists = os.path.exists(path)
        if exists and not overwrite:
            if not self._overwrite_warning:
                print('WARNING: not overwriting existing configuration files(s)!')
                print('WARNING: only warning once.')
                self._overwrite_warning = True
        else:
            with open(path, 'w') as f:
                f.write(string)

    def write_search(self, search, output_dir, overwrite=False):
        self._ensure_exists(output_dir)

        self._write_to_file(
            self.render_run(search),
            os.path.join(output_dir, 'run.sh'),
            overwrite
        )

        self._write_to_file(
            self.render_snakefile(output_dir, search),
            os.path.join(output_dir, 'Snakefile'),
            overwrite
        )

        for i, bracket in enumerate(search.brackets):
            for j in range(bracket.stages[0].n):
                self._write_to_file(
                    self.render_stage_config(j, search, bracket.stages[0]),
                    [output_dir, f'bracket-{i}',
                        'stage-0', f'config-{j}', 'config'],
                    overwrite
                )
