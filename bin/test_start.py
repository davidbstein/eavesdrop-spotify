# try:
#   from pygments.cmdline import main as pretty_print_file
#   pretty_print_file([None, 'test_start.py'])
# except:
#   with open('test_start.py') as f:
#     log(f.read())

# i run often this script with run with
#
# ```
#    while [ true ]; do ipython -i test_start.py; clear; done;
# ```

VERBOSE = True
def log(*s):
  if VERBOSE:
    print ' '.join(map(str, s))

###############
# helper junk #
###############

from unbundler import (
  file_parser,
  file as file_module,
  folder as folder_module,
  build_util,
)
from unbundler.colors import *
import os
from itertools import chain
import json
from collections import (
  deque,
  defaultdict,
)
import os, shutil
import codecs

def headerstr(s, colorize=magenta):
  to_ret = []
  to_ret.append("")
  to_ret.append(colorize("#" * (len(s) + 4)))
  to_ret.append(colorize("# %s #" % s))
  to_ret.append(colorize("#" * (len(s) + 4)))
  to_ret.append("")
  to_ret = '\n'.join(to_ret)
  log(to_ret)
  return to_ret


def organize_nodes(nodes):
  """
  nodes - a node has
    deps: child_id: path
    refs: parent_id: path

  if we can set
    node.is_index = True
    node.is_index = False
  """
  headerstr("setup")
  main_root = folder_module.FolderNode("_trunk_1", trunk_depth=1)
  main_node_root = folder_module.FolderNode("node_modules")
  source_tree = folder_module.FolderTree(main_root, main_node_root)
  entry_node_container = [
    node for node in nodes.itervalues() if node.entry
  ]
  assert len(entry_node_container) == 1
  entry_node = entry_node_container[0]
  entry_node.name = "entry.js"
  entry_node.is_index = False
  source_tree.set_entry(entry_node)

  headerstr("build src/")

  for cur_node_id, cur_node in nodes.iteritems():
    check_args = cur_node_id, cur_node, nodes
    if cur_node.is_index is None:
      build_util.check_for_index_ref(*check_args)
    if cur_node.is_index is None:
      build_util.check_for_node_root(*check_args)
  src_nodes = build_util.get_local_reachable(
    nodes, [entry_node.id]
  )
  index_ids = build_util.solve_for_index_ids(
    src_nodes,
    entry_node.id,
    node_map=nodes
  )
  main_build_result = build_util.build_tree(
    nodes=nodes,
    entry_node_ids=[entry_node.id]
  )
  placed_file_ids = main_build_result['placed_file_ids']
  node_module_file_ids = main_build_result['node_module_file_ids']

  headerstr("building node_modules")
  root_node_module_files = build_util.get_local_reachable(
    nodes, node_module_file_ids
  )
  sub_node_modules = set(nodes) - placed_file_ids - root_node_module_files

  node_modules_root = None
  # node_modules_root = build_util.build_node_modules(
  #   nodes,
  #   node_module_file_ids,
  #   root_node_module_files,
  # )

  log(yellow('nodes'), len(nodes))
  log(yellow('src files'), len(placed_file_ids))
  log(yellow('files in primary node_module env'), len(root_node_module_files))
  log(yellow('files in other node_module envs'), len(sub_node_modules))

  return {
    'source_root': source_tree.get_root(),
    'node_modules_root': node_modules_root,
  }

def _recursive_build(r, path_prefix):
  # os.makedirs(path_prefix + r.get_path())
  for file in r._files.itervalues():
    file_path = path_prefix + file.get_path()
    if not os.path.exists(file_path):
      os.makedirs(file_path)
    target = file_path+"/"+file.name
    with codecs.open(target, 'wb', 'utf-8') as f:
      f.write("// the following file was decompiled from a bundle\n")
      f.write("// with reference id %d\n" % file.id)
      f.write(file.source)
  for sub in r._children.itervalues():
    _recursive_build(sub, path_prefix)

def write_files(source_root, node_modules_root, output_location='/tmp/test_folder'):
  headerstr("writing to the filesystem")
  try:
    shutil.rmtree(output_location)
  except:
    log("can't remove %s" % output_location)
  os.makedirs(output_location)
  _recursive_build(source_root, output_location + "/src/")
  # _recursive_build(node_modules_root, output_location + "/")


def load_nodes(unbundle_location):
  target = unbundle_location
  raw_nodes = file_parser.parse_file(target)
  nodes = {
    k: file_module.MetaFileNode(n)
    for k, n in raw_nodes.iteritems()
  }
  log(yellow("%d nodes" % len(nodes)))
  return nodes

def build_unbundle(nodes):

  organized_nodes = organize_nodes(nodes)
  source_root = organized_nodes['source_root']
  node_modules_root = organized_nodes['node_modules_root']

  write_files(source_root, node_modules_root)

  # for node_id, node in nodes.iteritems():
  #   if node.get_path() == "<UNKNOWN PATH>":
  #     print red("UNKNOWN PATH LEFT")
  #     print node
  #     print node.refs

  return locals()

########################
## Load files and run ##
########################

# there's something wrong. check out album.spa node modules
# rambda/src/pluck should not be an index
# I can add a check for this by following every path
# and raising errors on a non-collision of identical files.

# for target_spa in os.listdir('../unbundled'):
for target_spa in ['artist.spa']:
  headerstr(target_spa, colorize=blue)
  if "unbundled.json" not in os.listdir("../unbundled/%s" % (target_spa, )):
    log(yellow("there is no unbundled.json, skipping"))
    continue
  nodes = load_nodes('../unbundled/%s/unbundled.json' % (target_spa, ))
  build_unbundle(nodes)
