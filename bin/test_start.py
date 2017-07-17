# try:
#   from pygments.cmdline import main as pretty_print_file
#   pretty_print_file([None, 'test_start.py'])
# except:
#   with open('test_start.py') as f:
#     log(f.read())

# you've probably ran this script with run with
#
# ```
#    while [ true ]; do ipython -i test_start.py; clear; done;
# ```

from colors import *

VERBOSE = True
def log(*s):
  if VERBOSE:
    print ' '.join(map(str, s))

#####################
# The script, woot. #
#####################

from unbundler import (
  file_parser,
  file as file_module,
  folder as folder_module,
  build_util,
)
import os
from itertools import chain
import json
from collections import (
  deque,
  defaultdict,
)

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

####################
# parse file nodes #
####################


def organize_nodes(nodes):
  headerstr("setup")
  main_root = folder_module.FolderNode("_trunk_1", trunk_depth=1)
  main_node_root = folder_module.FolderNode("node_modules")
  folder_tree = folder_module.FolderTree(main_root, main_node_root)
  entry_node_container = [
    node for node in nodes.itervalues() if node.entry
  ]
  assert len(entry_node_container) == 1
  entry_node = entry_node_container[0]
  entry_node.name = "entry.js"
  entry_node.is_index = False
  folder_tree.set_entry(entry_node)

  headerstr("finding which files are index.js")
  for cur_node_id, cur_node in nodes.iteritems():
    if cur_node.is_index is None:
      build_util.check_for_index_ref(cur_node_id, cur_node, nodes)
    if cur_node.is_index is None:
      build_util.check_for_folder_duplication(cur_node_id, cur_node, nodes)
    if cur_node.is_index is None:
      build_util.check_for_sibling_isolation(cur_node_id, cur_node, nodes)

  headerstr("building the tree")
  main_build_result = build_util.build_tree(
    nodes=nodes,
    entry_node_ids=[entry_node.id]
  )
  placed_file_ids = main_build_result['placed_file_ids']
  node_module_file_ids = main_build_result['node_module_file_ids']
  root_node_module_files = build_util.get_local_reachable(
    nodes, node_module_file_ids
  )
  sub_node_modules = set(nodes) - placed_file_ids - root_node_module_files

  log(yellow('nodes'), len(nodes))
  log(yellow('src files'), len(placed_file_ids))
  log(yellow('files in primary node_module env'), len(root_node_module_files))
  log(yellow('files in other node_module envs'), len(sub_node_modules))

########################
## Load files and run ##
########################

# for target_spa in os.listdir('../unbundled'):
for target_spa in ['album.spa']:
  try:
    print headerstr(target_spa, colorize=cyan)
    if "unbundled.json" not in os.listdir("../unbundled/%s" % (target_spa, )):
      print yellow("there is no unbundled.json")
      continue
    target = '../unbundled/%s/unbundled.json' % (target_spa, )
    raw_nodes = file_parser.parse_file(target)
    nodes = {
      k: file_module.MetaFileNode(n)
      for k, n in raw_nodes.iteritems()
    }
    log("%d nodes" % len(nodes))

    organize_nodes(nodes)
  except:
    import traceback
    print red("error")
    traceback.print_exc()

###############
## Test crap ##
###############

def runner(**kw):
  locals().update(kw)
  import os, shutil
  import codecs
  prefix = '/tmp/test_folder/src/'
  try:
    shutil.rmtree(prefix[:-5])
  except:
    log("can't remove")
  os.makedirs(prefix[:-5])
  for node in nodes.itervalues():
    target = prefix[:-4] + '%s.js' % node.id
    with codecs.open(target, 'wb', 'utf-8') as f:
      f.write(node.source)

  def recursive_build(r):
    os.makedirs(prefix + r.get_path())
    for file in r._files.itervalues():
      target = prefix + file.get_path()+"/"+file.name
      with codecs.open(target, 'wb', 'utf-8') as f:
        f.write(file.source)
    for sub in r._children.itervalues():
      recursive_build(sub)

  recursive_build(folder_tree.get_root())

  log(entry_node)
  log(entry_node.deps)

# runner(**locals())
# folder_tree.print_root()

