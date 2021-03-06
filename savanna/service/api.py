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

from savanna import conductor as c
from savanna import context
from savanna.openstack.common import excutils
from savanna.openstack.common import log as logging
from savanna.plugins import base as plugin_base
from savanna.plugins import provisioning
from savanna.service import instances as i
from savanna.utils import general as g
from savanna.utils.openstack import nova


conductor = c.API
LOG = logging.getLogger(__name__)


## Cluster ops

def get_clusters():
    return conductor.cluster_get_all(context.ctx())


def get_cluster(id):
    return conductor.cluster_get(context.ctx(), id)


def scale_cluster(id, data):
    ctx = context.ctx()

    cluster = conductor.cluster_get(ctx, id)
    plugin = plugin_base.PLUGINS.get_plugin(cluster.plugin_name)
    existing_node_groups = data.get('resize_node_groups', [])
    additional_node_groups = data.get('add_node_groups', [])

    #the next map is the main object we will work with
    #to_be_enlarged : {node_group_id: desired_amount_of_instances}
    to_be_enlarged = {}
    for ng in existing_node_groups:
        ng_id = g.find(cluster.node_groups, name=ng['name'])['id']
        to_be_enlarged.update({ng_id: ng['count']})

    additional = construct_ngs_for_scaling(cluster, additional_node_groups)

    try:
        cluster = conductor.cluster_update(ctx, cluster,
                                           {"status": "Validating"})
        LOG.info(g.format_cluster_status(cluster))
        plugin.validate_scaling(cluster, to_be_enlarged, additional)
    except Exception:
        with excutils.save_and_reraise_exception():
            i.clean_cluster_from_empty_ng(cluster)
            cluster = conductor.cluster_update(ctx, cluster,
                                               {"status": "Active"})
            LOG.info(g.format_cluster_status(cluster))

    # If we are here validation is successful.
    # So let's update to_be_enlarged map:
    to_be_enlarged.update(additional)

    context.spawn("cluster-scaling-%s" % id,
                  _provision_nodes, id, to_be_enlarged)
    return conductor.cluster_get(ctx, id)


def create_cluster(values):
    ctx = context.ctx()
    cluster = conductor.cluster_create(ctx, values)
    plugin = plugin_base.PLUGINS.get_plugin(cluster.plugin_name)

    # validating cluster
    try:
        cluster = conductor.cluster_update(ctx, cluster,
                                           {"status": "Validating"})
        LOG.info(g.format_cluster_status(cluster))
        plugin.validate(cluster)
    except Exception as ex:
        with excutils.save_and_reraise_exception():
            cluster = conductor.cluster_update(ctx, cluster,
                                               {"status": "Error",
                                                "status_description": str(ex)})
            LOG.info(g.format_cluster_status(cluster))

    context.spawn("cluster-creating-%s" % cluster.id,
                  _provision_cluster, cluster.id)

    return conductor.cluster_get(ctx, cluster.id)


def _provision_nodes(id, node_group_id_map):
    ctx = context.ctx()
    cluster = conductor.cluster_get(ctx, id)
    plugin = plugin_base.PLUGINS.get_plugin(cluster.plugin_name)

    cluster = conductor.cluster_update(ctx, cluster, {"status": "Scaling"})
    LOG.info(g.format_cluster_status(cluster))
    instances = i.scale_cluster(cluster, node_group_id_map, plugin)

    if instances:
        cluster = conductor.cluster_update(ctx, cluster,
                                           {"status": "Configuring"})
        LOG.info(g.format_cluster_status(cluster))
        plugin.scale_cluster(cluster, i.get_instances(cluster, instances))

    # cluster is now up and ready
    cluster = conductor.cluster_update(ctx, cluster, {"status": "Active"})
    LOG.info(g.format_cluster_status(cluster))


def _provision_cluster(cluster_id):
    ctx = context.ctx()
    cluster = conductor.cluster_get(ctx, cluster_id)
    plugin = plugin_base.PLUGINS.get_plugin(cluster.plugin_name)

    # updating cluster infra
    cluster = conductor.cluster_update(ctx, cluster,
                                       {"status": "InfraUpdating"})
    LOG.info(g.format_cluster_status(cluster))
    plugin.update_infra(cluster)

    # creating instances and configuring them
    cluster = conductor.cluster_get(ctx, cluster_id)
    i.create_cluster(cluster)

    # configure cluster
    cluster = conductor.cluster_update(ctx, cluster, {"status": "Configuring"})
    LOG.info(g.format_cluster_status(cluster))
    plugin.configure_cluster(cluster)

    # starting prepared and configured cluster
    cluster = conductor.cluster_update(ctx, cluster, {"status": "Starting"})
    LOG.info(g.format_cluster_status(cluster))
    plugin.start_cluster(cluster)

    # cluster is now up and ready
    cluster = conductor.cluster_update(ctx, cluster, {"status": "Active"})
    LOG.info(g.format_cluster_status(cluster))


def terminate_cluster(id):
    ctx = context.ctx()
    cluster = conductor.cluster_get(ctx, id)

    cluster = conductor.cluster_update(ctx, cluster, {"status": "Deleting"})
    LOG.info(g.format_cluster_status(cluster))

    plugin = plugin_base.PLUGINS.get_plugin(cluster.plugin_name)
    plugin.on_terminate_cluster(cluster)

    i.shutdown_cluster(cluster)
    conductor.cluster_destroy(ctx, cluster)


## ClusterTemplate ops

def get_cluster_templates():
    return conductor.cluster_template_get_all(context.ctx())


def get_cluster_template(id):
    return conductor.cluster_template_get(context.ctx(), id)


def create_cluster_template(values):
    return conductor.cluster_template_create(context.ctx(), values)


def terminate_cluster_template(id):
    return conductor.cluster_template_destroy(context.ctx(), id)


## NodeGroupTemplate ops

def get_node_group_templates():
    return conductor.node_group_template_get_all(context.ctx())


def get_node_group_template(id):
    return conductor.node_group_template_get(context.ctx(), id)


def create_node_group_template(values):
    return conductor.node_group_template_create(context.ctx(), values)


def terminate_node_group_template(id):
    return conductor.node_group_template_destroy(context.ctx(), id)


## Plugins ops

def get_plugins():
    return plugin_base.PLUGINS.get_plugins(
        base=provisioning.ProvisioningPluginBase)


def get_plugin(plugin_name, version=None):
    plugin = plugin_base.PLUGINS.get_plugin(plugin_name)
    if plugin:
        res = plugin.as_resource()
        if version:
            if version in plugin.get_versions():
                configs = plugin.get_configs(version)
                res._info['configs'] = [c.dict for c in configs]
                processes = plugin.get_node_processes(version)
                res._info['node_processes'] = processes
                required_image_tags = plugin.get_required_image_tags(version)
                res._info['required_image_tags'] = required_image_tags
            else:
                return None
        return res


def convert_to_cluster_template(plugin_name, version, config_file):
    plugin = plugin_base.PLUGINS.get_plugin(plugin_name)
    return plugin.convert(config_file, plugin_name, version,
                          conductor.cluster_template_create)


def construct_ngs_for_scaling(cluster, additional_node_groups):
    ctx = context.ctx()
    additional = {}
    for ng in additional_node_groups:
        count = ng['count']
        ng['count'] = 0
        ng_id = conductor.node_group_add(ctx, cluster, ng)
        additional.update({ng_id: count})
    return additional

## Image Registry


def get_images(tags):
    return nova.client().images.list_registered(tags)


def get_image(**kwargs):
    if len(kwargs) == 1 and 'id' in kwargs:
        return nova.client().images.get(kwargs['id'])
    else:
        return nova.client().images.find(**kwargs)


def register_image(image_id, username, description=None):
    client = nova.client()
    client.images.set_description(image_id, username, description)
    return client.images.get(image_id)


def unregister_image(image_id):
    client = nova.client()
    client.images.unset_description(image_id)
    return client.images.get(image_id)


def add_image_tags(image_id, tags):
    client = nova.client()
    client.images.tag(image_id, tags)
    return client.images.get(image_id)


def remove_image_tags(image_id, tags):
    client = nova.client()
    client.images.untag(image_id, tags)
    return client.images.get(image_id)
