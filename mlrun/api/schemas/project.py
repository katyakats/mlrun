import datetime
import typing

import pydantic

from .object import (
    ObjectStatus,
    ObjectKind,
)


class ProjectMetadata(pydantic.BaseModel):
    name: str
    created: typing.Optional[datetime.datetime] = None

    class Config:
        extra = pydantic.Extra.allow


class ProjectSpec(pydantic.BaseModel):
    description: typing.Optional[str] = None
    params: typing.Optional[dict] = None
    functions: typing.Optional[list] = None
    workflows: typing.Optional[list] = None
    artifacts: typing.Optional[list] = None
    artifact_path: typing.Optional[str] = None
    conda: typing.Optional[str] = None
    source: typing.Optional[str] = None
    subpath: typing.Optional[str] = None
    origin_url: typing.Optional[str] = None

    class Config:
        extra = pydantic.Extra.allow


class Project(pydantic.BaseModel):
    kind: ObjectKind = pydantic.Field(ObjectKind.project, const=True)
    metadata: ProjectMetadata
    spec: ProjectSpec = ProjectSpec()
    status: ObjectStatus = ObjectStatus()


class ProjectRecord(Project):
    id: int = None

    class Config:
        orm_mode = True


class ProjectsOutput(pydantic.BaseModel):
    # use the format query param to control whether the full object will be returned or only the names
    projects: typing.List[typing.Union[Project, str]]
