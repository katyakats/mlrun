# Copyright 2018 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os import path
import click
from ast import literal_eval
import getpass
import yaml

from .runtimes import run_start
from .utils import run_keys

@click.group()
def main():
    pass

@main.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("url", type=str)
@click.option('--param', '-p', default='', multiple=True,
              help="parameter name and value tuples, e.g. -p x=37 -p y='text'")
@click.option('--in-artifact', '-i', multiple=True, help='input artifact')
@click.option('--out-artifact', '-o', multiple=True, help='output artifact')
@click.option('--in-path', help='default input path/url (prefix) for artifact')
@click.option('--out-path', help='default output path/url (prefix) for artifact')
@click.option('--secrets', '-s', multiple=True, help='secrets file=<filename> or env=ENV_KEY1,..')
@click.option('--uid', help='unique run ID')
@click.option('--name', help='run name')
@click.option('--workflow', help='workflow name/id')
@click.option('--project', help='project name/id')
@click.option('--rundb', default='', help='save run results to path or DB url')
@click.option('--runtime', '-r', default='local', help='runtime environment e.g. local, remote, nuclio, mpi')
@click.option('--kfp', is_flag=True, help='running inside Kubeflow Piplines')
@click.argument('run_args', nargs=-1, type=click.UNPROCESSED)
#@click.option('--secrets', '-s', type=click.File(), help='secrets file')
def run(url, param, in_artifact, out_artifact, in_path, out_path, secrets, uid, name,
        workflow, project, rundb, runtime, kfp, run_args):
    """Execute a task and inject parameters."""

    meta = {}
    set_item(meta, uid, 'uid')
    set_item(meta, name, 'name')
    set_item(meta, project, 'project')
    set_item(meta, workflow, 'workflow')

    labels = {'owner': getpass.getuser()}
    set_item(labels, workflow, 'workflow')
    meta['labels'] = labels

    spec = {'runtime': {'kind': runtime, 'command': url}}
    set_item(spec['runtime'], run_args, 'args', list(run_args))

    if param:
        params_dict = {}
        for param in param:
            i = param.find('=')
            if i == -1:
                continue
            key, value = param[:i].strip(), param[i + 1:].strip()
            if key is None:
                raise ValueError(f'cannot find param key in line ({param})')
            try:
                params_dict[key] = literal_eval(value)
            except SyntaxError:
                params_dict[key] = value
        spec['parameters'] = params_dict

    set_item(spec, in_artifact, run_keys.input_objects, line2keylist(in_artifact))
    set_item(spec, in_path, run_keys.input_path)
    set_item(spec, out_path, run_keys.output_path)
    set_item(spec, out_artifact, run_keys.output_artifacts, line2keylist(out_artifact))
    set_item(spec, secrets, run_keys.secrets, line2keylist(secrets, 'kind', 'source'))

    struct = {'metadata': meta, 'spec': spec}
    resp = run_start(struct, rundb=rundb, kfp=kfp)
    if resp:
        print(yaml.dump(resp, default_flow_style=False, sort_keys=False))


def set_item(struct, item, key, value=None):
    if item:
        if value:
            struct[key] = value
        else:
            struct[key] = item


def line2keylist(lines: list, keyname='key', valname='path'):
    out = []
    for line in lines:
        i = line.find('=')
        if i == -1:
            raise ValueError('cannot find "=" in line ({}={})'.format(keyname, valname))
        key, value = line[:i].strip(), line[i + 1:].strip()
        if key is None:
            raise ValueError('cannot find key in line ({}={})'.format(keyname, valname))
        value = path.expandvars(value)
        out += [{keyname: key, valname: value}]
    return out


if __name__ == "__main__":
    main()

