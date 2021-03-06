import re
from collections import OrderedDict
from importlib import import_module

from marshmallow import Schema, fields, validate, ValidationError, post_load, pre_dump

from dtran.config_parser import PipelineSchema

wired_pattern = re.compile(r'^\$\.\w+\.\w+$')
keys_pattern = re.compile(r'^\w+$')


class OrderedDictField(fields.Dict):
    mapping_type = OrderedDict


class IOFieldSchema(Schema):
    id = fields.Str(required=True)
    optional = fields.Bool(required=True, truthy={True}, falsy={False})
    val = fields.Raw(required=True, allow_none=True)

    class Meta:
        ordered = True


class NodeSchema(Schema):
    id = fields.Str(required=True, validate=validate.Regexp(keys_pattern))
    adapter = fields.Str(required=True)
    comment = fields.Str()
    inputs = OrderedDictField(required=True, keys=fields.Str(validate=validate.Regexp(keys_pattern)), values=fields.Nested(IOFieldSchema()))
    outputs = OrderedDictField(required=True, keys=fields.Str(validate=validate.Regexp(keys_pattern)), values=fields.Nested(IOFieldSchema()))

    class Meta:
        ordered = True


class EdgeSchema(Schema):
    source = fields.Str(required=True, validate=validate.Regexp(keys_pattern))
    output = fields.Str(required=True, validate=validate.Regexp(keys_pattern))
    target = fields.Str(required=True, validate=validate.Regexp(keys_pattern))
    input = fields.Str(required=True, validate=validate.Regexp(keys_pattern))

    class Meta:
        ordered = True


class DiGraphSchema(Schema):
    version = fields.Str(required=True)
    description = fields.Str()
    nodes = fields.List(fields.Nested(NodeSchema()), required=True, validate=validate.Length(min=1))
    edges = fields.List(fields.Nested(EdgeSchema()), required=True)

    class Meta:
        ordered = True

    @pre_dump
    def create_digraph(self, data, **kwargs):
        PipelineSchema({}).load(data)
        digraph = OrderedDict()
        digraph['version'] = data['version']
        if 'description' in data:
            digraph['description'] = data['description']
        tmp_nodes_dict, tmp_edges_list = {}, []
        digraph['nodes'] = []
        digraph['edges'] = []
        for name, adapter in data['adapters'].items():
            node = OrderedDict()
            node['id'] = name
            node['adapter'] = adapter['adapter']
            if 'comment' in adapter:
                node['comment'] = adapter['comment']
            node['inputs'] = OrderedDict()

            mod, *cls = adapter['adapter'].rsplit('.', 1)
            mod = import_module(mod)
            cls = getattr(mod, cls[0])
            for input, argtype in cls.inputs.items():
                node['inputs'][input] = OrderedDict()
                node['inputs'][input]['id'] = argtype.id
                node['inputs'][input]['optional'] = argtype.optional
                node['inputs'][input]['val'] = argtype.val

            node['outputs'] = OrderedDict()
            for output, argtype in cls.outputs.items():
                node['outputs'][output] = OrderedDict()
                node['outputs'][output]['id'] = argtype.id
                node['outputs'][output]['optional'] = argtype.optional
                node['outputs'][output]['val'] = argtype.val

            if 'inputs' not in adapter:
                continue
            for input, value in adapter['inputs'].items():
                if isinstance(value, str) and wired_pattern.match(value):
                    edge = OrderedDict()
                    adapter_name, output = value.split('.')[1:]
                    edge['source'] = adapter_name
                    edge['output'] = output
                    edge['target'] = name
                    edge['input'] = input
                    digraph['edges'].append(edge)
                    tmp_edges_list.append((edge['source'], edge['target']))
                else:
                    node['inputs'][input]['val'] = value
            # digraph['nodes'].append(node)
            tmp_nodes_dict[name] = node

        # Topological sort nodes and edges in lexical order
        topo_graph_count = {k: 0 for k in tmp_nodes_dict}
        topo_graph_edges = {}
        for ed_src, ed_tgt in tmp_edges_list:
            topo_graph_count[ed_tgt] += 1
            if ed_src not in topo_graph_edges:
                topo_graph_edges[ed_src] = [ed_tgt]
            else:
                topo_graph_edges[ed_src].append(ed_tgt)
        # print(topo_graph_count)
        # print(topo_graph_edges)
        index_count = len(topo_graph_count.keys())
        added_nodes = []
        for index in range(index_count):
            print(f"looping at {index}")
            start_nodes = [n for n, c in topo_graph_count.items() if c == 0 and n not in added_nodes]
            print(f"start nodes are {start_nodes}")
            if not start_nodes:
                raise ValueError("Something is wrong")
            start_node = start_nodes[0]
            node = tmp_nodes_dict[start_node]
            digraph['nodes'].append(node)
            # update topo_graph_count
            if start_node not in topo_graph_edges:
                continue
            for ed_tgt in topo_graph_edges[start_node]:
                if topo_graph_count[ed_tgt] == 0:
                    raise ValueError("Something is WRONG")
                else:
                    topo_graph_count[ed_tgt] -= 1
            print(f"current topo_graph_count is {topo_graph_count}")
            added_nodes.append(start_node)

        # print(digraph)
        return digraph


    @post_load
    def create_config(self, data, **kwargs):
        pipeline_config = OrderedDict()
        pipeline_config['version'] = data['version']
        if 'description' in data:
            pipeline_config['description'] = data['description']
        pipeline_config['adapters'] = OrderedDict()
        for node in data['nodes']:
            adapter_config = OrderedDict()
            adapter_config['adapter'] = node['adapter']
            if 'comment' in node:
                adapter_config['comment'] = node['comment']
            adapter_inputs = OrderedDict()
            for input_name, input_argtype in node['inputs'].items():
                if input_argtype['val'] is not None:
                    adapter_inputs[input_name] = input_argtype['val']
            if adapter_inputs:
                adapter_config['inputs'] = adapter_inputs
            pipeline_config['adapters'][node['id']] = adapter_config

        for edge in data['edges']:
            source, target = (edge['source'], edge['target'])
            if source not in pipeline_config['adapters']:
                raise ValidationError(f"invalid edge source {source}")
            if target not in pipeline_config['adapters']:
                raise ValidationError(f"invalid edge target {target}")
            if 'inputs' not in pipeline_config['adapters'][target]:
                pipeline_config['adapters'][target]['inputs'] = OrderedDict()
            pipeline_config['adapters'][target]['inputs'][edge['input']] = f"$.{source}.{edge['output']}"

        return pipeline_config
