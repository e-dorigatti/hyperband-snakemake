import os
import shutil
from typing import List, Optional, Tuple, Union, Set

from jinja2 import (BaseLoader, ChoiceLoader, Environment, FileSystemLoader,
                    PackageLoader)

from hyperband_snakemake.search import HbSearch, HbStage


class HbWriter:
    def __init__(self, config_template: str, run_template: str, snakefile_template: str,
                 template_dir: Optional[str] = None):
        self._overwrite_warning = False
        self._config_template = config_template
        self._run_template = run_template
        self._snakefile_template = snakefile_template
        self._template_dir = template_dir

        loader: BaseLoader
        if self._template_dir is not None:
            loader = ChoiceLoader([
                FileSystemLoader(self._template_dir),
                PackageLoader('hyperband_snakemake', 'templates'),
            ])
        else:
            loader = PackageLoader('hyperband_snakemake', 'templates')

        self._env = Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)

    def render_stage_config(self, bracket_index: int, config_index: int,
                            search: HbSearch, stage: HbStage) -> str:
        tmpl = self._env.get_template(self._config_template)
        rendered = tmpl.render(
            folds=stage.search.folds,
            repetitions=stage.search.repetitions,
            search=search,
            bracket_index=bracket_index,
            config_index=config_index,
        )
        return rendered

    def render_snakefile(self, output_dir: str, search: HbSearch) -> str:
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

    def render_run(self, search: HbSearch) -> str:
        tmpl = self._env.get_template(self._run_template)
        rendered = tmpl.render(search=search)
        return rendered

    @staticmethod
    def _ensure_exists(*parts: str) -> str:
        dd = None
        for p in parts:
            if dd is not None:
                dd = os.path.join(dd, p)
            else:
                dd = p

            if not os.path.exists(dd):
                os.mkdir(dd)

        assert dd is not None
        return dd

    def _write_to_file(self, string: str, path: Union[str, tuple, list],
                       overwrite: bool) -> None:
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

    def _ignore_templates(self, path: str, files: List[str]) -> List[str]:
        if path == self._template_dir:
            templates = ['config', 'run.sh', 'Snakefile']
            return [t for t in templates if t in files]
        else:
            return []

    def _generate_all_configs(self, search: HbSearch) -> List[Tuple[List[str], str]]:
        path_and_config: List[Tuple[List[str], str]] = []
        generated_configs: Set[str] = set()

        for i, bracket in enumerate(search.brackets):
            for j in range(bracket.stages[0].n):
                # generate unique configuration
                tried, cfg = 0, ''
                while tried == 0 or cfg in generated_configs:
                    cfg = self.render_stage_config(i, j, search, bracket.stages[0])
                    tried += 1
                    if tried >= 27:
                        # number of failures generating a unique random config is
                        # distributed as a Geometric random variable. there is a
                        # ~50% chance of observing more than 27 failures when we
                        # generated 97.5% of all possible configs
                        raise RuntimeError('too many attempts generating unique random '
                                           f'configuration ({len(generated_configs)} so '
                                           'far)! - either use fewer random '
                                           'hyperparameters or increase the size of the '
                                           'search')
                generated_configs.add(cfg)
                path_and_config.append(([f'bracket-{i}', 'stage-0', f'config-{j}', 'config'], cfg))
        return path_and_config

    def write_search(self, search: HbSearch, output_dir: str,
                     overwrite: bool = False) -> None:

        path_and_config = self._generate_all_configs(search)
        for path, config in path_and_config:
            self._write_to_file(config, [output_dir] + path, overwrite)

        if self._template_dir is not None:
            shutil.copytree(self._template_dir, output_dir, ignore=self._ignore_templates,
                            dirs_exist_ok=True)

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
