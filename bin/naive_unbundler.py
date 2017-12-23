from unbundler import file_parser
import os
import shutil
import codecs
from collections import Counter


def get_nodes_from_file(file_target):
    nodes = file_parser.parse_file(file_target=file_target)
    for n in nodes.itervalues():
        if n._entry:
            id = 0
            name = "_entry_point"
        else:
            id = n.id
            name = Counter(
                [
                    path.replace("../", "").replace("./", "").replace("/", "_")
                     for path in n.refs.itervalues()
                ]
            ).most_common(1)[0][0]
        n.meta.name = "{name} -{id:04d}.js".format(
            id=id,
            name=name
        )
    return nodes


def fix_source(node):
    source = node.source
    require_str = "require('{path}')"
    for dep_id, dep_path in node.deps.iteritems():
        source = source.replace(
            require_str.format(path=dep_path),
            require_str.format(path="./"+nodes[dep_id].meta.name))
    return source


def unbundle(file_target, output_folder):
    nodes = get_nodes_from_file(file_target)
    for node in nodes.itervalues():
        file_path = output_folder
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        target = file_path + '/' + node.meta.name
        with codecs.open(target, 'wb', 'utf-8') as f:
          f.write("// the following file was decompiled from a bundle\n")
          f.write("// with reference id %d\n" % node.id)
          f.write(fix_source(node))
