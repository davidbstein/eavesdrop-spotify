try:
  from pygments.cmdline import main as pretty_print_file
  pretty_print_file([None, 'test_start.py'])
except:
  with open('test_start.py') as f:
    print f.read()

# you've probably ran this script with run with
#
# ```
#    while [ true ]; do ipython -i test_start.py; clear; done;
# ```

from colors import *

############
## Test crap
############
def runner(**kw):
  locals().update(kw)
  import os, shutil
  import codecs
  prefix = '/tmp/test_folder/src/'
  try:
    shutil.rmtree(prefix[:-5])
  except:
    print "can't remove"
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

  print entry_node
  print entry_node.deps

  for file_id in [896, 899]:
    if file_id in placed_file_ids:
      node = nodes[file_id]
      print ""
      print node
      print node.refs
      print node.deps

  folder_tree.print_root()

#####################
# The script, woot. #
#####################

from unbundler import (
  file_parser,
  file as file_module,
  folder as folder_module,
)
from itertools import chain
import json
from collections import (
  deque,
  defaultdict,
)



def headerstr(s):
  print ""
  print magenta("#" * (len(s) + 4))
  print magenta("# %s #" % s)
  print magenta("#" * (len(s) + 4))
  print ""

####################
# parse file nodes #
####################

headerstr("setup")

#   create metadata object for each file node
#    - end of path
#    - filenode
#    - filename guess?
#    - is_index False no, True yes, None unknown
#    - parent folder node
raw_nodes = file_parser.parse_file('../unbundled/artist.spa/unbundled.json')
nodes = {
  k: file_module.MetaFileNode(n)
  for k, n in raw_nodes.iteritems()
}
print "%d nodes" % len(nodes)

# create "root" folder and "node_modules" folder
main_root = folder_module.FolderNode("_trunk_1", trunk_depth=1)
main_node_root = folder_module.FolderNode("node_modules")
folder_tree = folder_module.FolderTree(main_root, main_node_root)

# as we go forward to look at paths, some things:
#   exposed root - this is a node module
#   single dot - this is a sibling
#   double got - relative path
placed_file_ids = set()

# build the tree with the unnamed trunk
#   entry is the only path with unnamed folders, build special nodes that can have unnamed parents and start building tree.
entry_node_container = [
  node for node in nodes.itervalues() if node.entry
]
assert len(entry_node_container) == 1
entry_node = entry_node_container[0]
entry_node.name = "entry.js"
entry_node.is_index = False

folder_tree.set_entry(entry_node)


#####################
# Analysis of files #
#####################

headerstr("finding which files are index.js")

def _name_parse(r):
  s = r.split('/')[-1]
  if s.endswith('.js'):
    return s
  else:
    return s + ".js"

def check_for_index_ref(cur_node_id, cur_node, nodes=nodes):
  names = set([_name_parse(r) for r in cur_node.refs.itervalues()])
  if any(r.endswith(".js") and not r.endswith("index.js") for r in cur_node.refs.itervalues()):
    cur_node.is_index = False
    assert len(names) == 1
    cur_node.name = list(names)[0]

    print yellow("not index - has a '.js' ref"), cur_node.id
  if len(names) == 2:
    assert "index.js" in names, names
    cur_node.is_index = True
    cur_node.name = "index.js"
    print yellow("index"), cur_node.id, cur_node.name
  elif len(names) == 1:
    cur_node.name = names.pop()
    if cur_node.name == "index.js":
      cur_node.is_index = True
  elif len(names) == 0:
    cur_node.name = "index.js" # % cur_node.id
    print yellow("unnamed"), cur_node.id, "is entry:", cur_node.entry
  else:
    print names


def check_for_folder_duplication(cur_node_id, cur_node, nodes=nodes):
  name = cur_node.name[:-len('.js')]
  for dep_id, dep_path in cur_node.deps.iteritems():
    dep_node = nodes[dep_id]
    if dep_path.startswith("./%s/" % name):
      # this is a module.js that wraps its contents
      # see npm/mout/object.js for an example
      cur_node.is_index = False
      print cyan("not index - is a module with same-name folder sibling"), cur_node.name, cur_node_id
      return
    for depref_id, depref_path in dep_node.refs.iteritems():
      if dep_path.startswith("./"):
        subpath = depref_path[:-len(dep_path) + 1]
        if subpath.endswith(name):
          cur_node.is_index = True
          cur_node.name = 'index.js'
          print cyan("is index - found a local path with matching ancestor"), cur_node.name, cur_node.id
          return

for cur_node_id, cur_node in nodes.iteritems():
  check_for_index_ref(cur_node_id, cur_node)
  check_for_folder_duplication(cur_node_id, cur_node)

headerstr("doing a depth check")

def print_depth_error(cur_file_id, depths):
  to_ret = ['file %d has inconsistent depths' % cur_file_id,'depths:']
  cur_depths = depths[cur_file_id]
  for id, d in sorted(cur_depths.iteritems(), key=lambda p: p[1]):
    ref = depths[id]
    path = nodes[id].deps[cur_file_id]
    spc = '\n          '
    name = nodes[id].name
    to_ret.append("id: {id:4} {name} {spc}depth: {d:2} {spc}{ref}{spc}{path}".format(**locals()))
  return '\n'.join(to_ret)

def depth_check(nodes=nodes, entry_id=entry_node.id):
  file_ids_to_visit = deque([entry_id])
  depths = defaultdict(dict)
  depths[entry_id]["initial condition"] = 0
  while file_ids_to_visit:
    cur_file_id = file_ids_to_visit.popleft()
    cur_file = nodes[cur_file_id]
    print cur_file_id, depths[cur_file_id]
    assert len(set(depths[cur_file_id].values())) <= 1, print_depth_error(cur_file_id, depths)
    cur_depth = depths[cur_file_id].itervalues().next()
    for dep_id, path in cur_file.deps.iteritems():
      if not path.startswith("."):
        continue
      dep = nodes[dep_id]
      depth = (
        cur_depth
        + folder_module.depth_diff(path)
        + (1 if dep.is_index else 0)
        + (1 if cur_file.is_index else 0)
      )
      if depths[dep_id].get(cur_file_id) is None:
        depths[dep_id][cur_file_id] = depth
        file_ids_to_visit.append(dep_id)
  # for k, v in sorted(depths.iteritems()):
  #   if len(v) > 1:
  #     print k, v.values()


depth_check()

####################
# Building of Tree #
####################

headerstr("building the tree")
# build the tree of things in the root
#   - keep a list of node modules, but don't start on them quite yet.

# node_module_file_ids = set()
# file_ids_to_visit = deque([entry_node.id])
# while file_ids_to_visit:
#   cur_file_id = file_ids_to_visit.popleft()
#   cur_file = nodes[cur_file_id]
#   print cyan("visiting %s" % cur_file)
#   print "  %d left in file_ids_to_visit" % len(file_ids_to_visit)
#   print "  %d/%d placed" % (len(placed_file_ids), len(nodes))
#   for dep_id, path in cur_file.deps.iteritems():
#     print green("  current dep"), dep_id, path
#     cur_dep = nodes[dep_id]
#     if cur_dep.id in placed_file_ids:
#       print red("    (seen)")
#       pass
#     elif path.startswith("."):
#       file_ids_to_visit.append(cur_dep.id)
#       folder_module.add_file_by_path(
#         cur_file.folder, path, cur_dep
#       )
#       placed_file_ids.add(cur_dep.id)
#       print green("  cur dep placement:"), cur_dep
#     else:
#       print red("  skipping %s" % path)

# build anything in "node_modules"
# we can't do this first because things that /are/ node modules reference their own environments

#   if a file already has a parent, confirm that your walk matches.
#   if it doesn't
#     - one too shallow: starting point is an index
#     - one too deep: referring parent is in index

# checkreps

# construct the folder heiarchy




runner(**locals())


