from unbundler import file_parser
import os
import shutil
import codecs
from collections import Counter
import json

def get_nodes_from_file(file_target):
    nodes = file_parser.parse_file(file_target=file_target)
    for n in nodes.values():
        if n._entry:
            id = 0
            name = "_entry_point"
        else:
            id = n.id
            name = Counter(
                [
                    path.replace("../", "").replace("./", "").replace("/", "_")
                     for path in n.refs.values()
                ]
            ).most_common(1)[0][0]
        n.meta.name = "{name}-{id:04d}.js".format(
            id=id,
            name=name
        )
    return nodes


def fix_source(node, nodes):
    source = node.source
    require_str = "require('{path}')"
    for dep_id, dep_path in node.deps.items():
        source = source.replace(
            require_str.format(path=dep_path),
            require_str.format(path="./"+nodes[dep_id].meta.name))
    return source


def unbundle(target):
    file_target = '_unbundled/{}.spa/unbundled.json'.format(target)
    output_folder = 'unbundled_source/{}.spa/src'.format(target)
    nodes = get_nodes_from_file(file_target)
    print("got {} nodes".format(len(nodes)))
    for node in nodes.values():
        file_path = output_folder
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        target = file_path + '/' + node.meta.name
        with codecs.open(target, 'wb', 'utf-8') as f:
          f.write("// the following file was decompiled from a bundle\n")
          f.write("// with reference id %d\n" % node.id)
          f.write(fix_source(node, nodes))
    print("populated {}".format(output_folder))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='take an unbundled.json and fill a folder with files.'
    )
    parser.add_argument('target', help='the target package')
    args = parser.parse_args()
    unbundle(args.target)