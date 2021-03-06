# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Defines interface for DB access.

Functions in this module are imported into the savanna.db namespace. Call these
functions from savanna.db namespace, not the savanna.db.api namespace.

All functions in this module return objects that implement a dictionary-like
interface.

**Related Flags**

:db_backend:  string to lookup in the list of LazyPluggable backends.
              `sqlalchemy` is the only supported backend right now.

:sql_connection:  string specifying the sqlalchemy connection to use, like:
                  `sqlite:///var/lib/savanna/savanna.sqlite`.

"""

from oslo.config import cfg

from savanna.openstack.common.db import api as db_api
from savanna.openstack.common import log as logging


CONF = cfg.CONF

_BACKEND_MAPPING = {
    'sqlalchemy': 'savanna.db.sqlalchemy.api',
}

IMPL = db_api.DBAPI(backend_mapping=_BACKEND_MAPPING)
LOG = logging.getLogger(__name__)


def setup_db():
    """Set up database, create tables, etc.

    Return True on success, False otherwise
    """
    return IMPL.setup_db()


def drop_db():
    """Drop database.

    Return True on success, False otherwise
    """
    return IMPL.drop_db()


## Helpers for building constraints / equality checks


def constraint(**conditions):
    """Return a constraint object suitable for use with some updates."""
    return IMPL.constraint(**conditions)


def equal_any(*values):
    """Return an equality condition object suitable for use in a constraint.

    Equal_any conditions require that a model object's attribute equal any
    one of the given values.
    """
    return IMPL.equal_any(*values)


def not_equal(*values):
    """Return an inequality condition object suitable for use in a constraint.

    Not_equal conditions require that a model object's attribute differs from
    all of the given values.
    """
    return IMPL.not_equal(*values)


def to_dict(func):
    def decorator(*args, **kwargs):
        res = func(*args, **kwargs)

        if isinstance(res, list):
            return [item.to_dict() for item in res]

        if res:
            return res.to_dict()
        else:
            return None

    return decorator


## Cluster ops

@to_dict
def cluster_get(context, cluster):
    """Return the cluster or None if it does not exist."""
    return IMPL.cluster_get(context, cluster)


@to_dict
def cluster_get_all(context):
    """Get all clusters."""
    return IMPL.cluster_get_all(context)


@to_dict
def cluster_create(context, values):
    """Create a cluster from the values dictionary."""
    return IMPL.cluster_create(context, values)


@to_dict
def cluster_update(context, cluster, values):
    """Set the given properties on cluster and update it."""
    return IMPL.cluster_update(context, cluster, values)


def cluster_destroy(context, cluster):
    """Destroy the cluster or raise if it does not exist."""
    IMPL.cluster_destroy(context, cluster)


## Node Group ops

def node_group_add(context, cluster, values):
    """Create a Node Group from the values dictionary."""
    return IMPL.node_group_add(context, cluster, values)


def node_group_update(context, node_group, values):
    """Set the given properties on node_group and update it."""
    IMPL.node_group_update(context, node_group, values)


def node_group_remove(context, node_group):
    """Destroy the node_group or raise if it does not exist."""
    IMPL.node_group_remove(context, node_group)


## Instance ops

def instance_add(context, node_group, values):
    """Create an Instance from the values dictionary."""
    return IMPL.instance_add(context, node_group, values)


def instance_update(context, instance, values):
    """Set the given properties on Instance and update it."""
    IMPL.instance_update(context, instance, values)


def instance_remove(context, instance):
    """Destroy the Instance or raise if it does not exist."""
    IMPL.instance_remove(context, instance)


## Cluster Template ops

@to_dict
def cluster_template_get(context, cluster_template):
    """Return the cluster_template or None if it does not exist."""
    return IMPL.cluster_template_get(context, cluster_template)


@to_dict
def cluster_template_get_all(context):
    """Get all cluster_templates."""
    return IMPL.cluster_template_get_all(context)


@to_dict
def cluster_template_create(context, values):
    """Create a cluster_template from the values dictionary."""
    return IMPL.cluster_template_create(context, values)


def cluster_template_destroy(context, cluster_template):
    """Destroy the cluster_template or raise if it does not exist."""
    IMPL.cluster_template_destroy(context, cluster_template)


## Node Group Template ops

@to_dict
def node_group_template_get(context, node_group_template):
    """Return the Node Group Template or None if it does not exist."""
    return IMPL.node_group_template_get(context, node_group_template)


@to_dict
def node_group_template_get_all(context):
    """Get all Node Group Templates."""
    return IMPL.node_group_template_get_all(context)


@to_dict
def node_group_template_create(context, values):
    """Create a Node Group Template from the values dictionary."""
    return IMPL.node_group_template_create(context, values)


def node_group_template_destroy(context, node_group_template):
    """Destroy the Node Group Template or raise if it does not exist."""
    IMPL.node_group_template_destroy(context, node_group_template)


## Data Source ops

@to_dict
def data_source_get(context, data_source):
    """Return the Data Source or None if it does not exist."""
    return IMPL.data_source_get(context, data_source)


@to_dict
def data_source_get_all(context):
    """Get all Data Sources."""
    return IMPL.data_source_get_all(context)


@to_dict
def data_source_create(context, values):
    """Create a Data Source from the values dictionary."""
    return IMPL.data_source_create(context, values)


def data_source_destroy(context, data_source):
    """Destroy the Data Source or raise if it does not exist."""
    IMPL.data_source_destroy(context, data_source)


## Jobs ops

@to_dict
def job_get(context, job):
    """Return the Job or None if it does not exist."""
    return IMPL.job_get(context, job)


@to_dict
def job_get_all(context):
    """Get all Jobs."""
    return IMPL.job_get_all(context)


@to_dict
def job_create(context, values):
    """Create a Job from the values dictionary."""
    return IMPL.job_create(context, values)


def job_destroy(context, job):
    """Destroy the Job or raise if it does not exist."""
    IMPL.job_destroy(context, job)


## JobExecutions ops

@to_dict
def job_execution_get(context, job_execution):
    """Return the JobExecution or None if it does not exist."""
    return IMPL.job_execution_get(context, job_execution)


@to_dict
def job_execution_get_all(context):
    """Get all JobExecutions."""
    return IMPL.job_execution_get_all(context)


@to_dict
def job_execution_create(context, values):
    """Create a JobExecution from the values dictionary."""
    return IMPL.job_execution_create(context, values)


def job_execution_update(context, job_execution, values):
    """Create a JobExecution from the values dictionary."""
    return IMPL.job_execution_update(context, job_execution, values)


def job_execution_destroy(context, job_execution):
    """Destroy the JobExecution or raise if it does not exist."""
    IMPL.job_execution_destroy(context, job_execution)


## JobOrigin ops

@to_dict
def job_origin_get(context, job_origin):
    """Return the JobOrigin or None if it does not exist."""
    return IMPL.job_origin_get(context, job_origin)


@to_dict
def job_origin_get_all(context):
    """Get all JobOrigins."""
    return IMPL.job_origin_get_all(context)


@to_dict
def job_origin_create(context, values):
    """Create a JobOrigin from the values dictionary."""
    return IMPL.job_origin_create(context, values)


def job_origin_update(context, job_origin, values):
    """Update a JobOrigin from the values dictionary."""
    IMPL.job_origin_update(context, job_origin, values)


def job_origin_destroy(context, job_origin):
    """Destroy the JobOrigin or raise if it does not exist."""
    IMPL.job_origin_destroy(context, job_origin)
