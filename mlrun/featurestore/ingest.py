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

import os
import pathlib
import v3io_frames as v3f
from tempfile import mktemp

from mlrun.datastore import store_manager

from .model import TargetTypes
from ..platforms.iguazio import split_path
from ..config import config as mlconf


def write_to_target_store(client, kind, source, target_path, featureset, **kw):
    """write/ingest data to a target store"""
    if kind == TargetTypes.parquet:
        return upload_file(source, target_path, **kw)
    if kind == TargetTypes.nosql:
        index = list(featureset.spec.entities.keys())
        return upload_nosql(source, target_path, index)
    raise NotImplementedError(
        "currently only parquet/file and nosql targets are supported"
    )


def upload_nosql(source, target_path, index):
    if isinstance(source, str):
        # if source is a path/url convert to DataFrame
        source = store_manager.object(url=source).as_df()

    container, subpath = split_path(target_path)
    client = v3f.Client(mlconf.frames_url, container=container)
    if len(index) != 1:
        raise ValueError("currently only support single column NoSQL index")
    client.write(
        "kv", subpath, index_cols=index, save_mode="overwriteTable", dfs=source
    )


def upload_file(source, target_path, format="parquet", **kw):
    suffix = pathlib.Path(target_path).suffix
    if not suffix:
        target_path = target_path + "." + format
    if isinstance(source, str):
        if source and os.path.isfile(source):
            store_manager.object(url=target_path).upload(source)
        return target_path

    df = source
    if df is None:
        return None

    if format in ["csv", "parquet"]:
        writer_string = "to_{}".format(format)
        saving_func = getattr(df, writer_string, None)
        target = target_path
        to_upload = False
        if "://" in target:
            target = mktemp()
            to_upload = True
        else:
            dir = os.path.dirname(target)
            if dir:
                os.makedirs(dir, exist_ok=True)

        saving_func(target, **kw)
        if to_upload:
            store_manager.object(url=target_path).upload(target)
            os.remove(target)
        return target_path

    raise ValueError(f"format {format} not implemented yes")
