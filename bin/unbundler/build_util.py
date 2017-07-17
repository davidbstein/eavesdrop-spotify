from colors import *
from itertools import chain
import json
from collections import (
  deque,
  defaultdict,
)
import file as file_module
import folder as folder_module

VERBOSE = False
def log(*s):
  if VERBOSE:
    print ' '.join(map(str, s))

def _name_parse(r):
  s = r.split('/')[-1]
  if s.endswith('.js'):
    return s
  else:
    return s + ".js"

def check_for_index_ref(cur_node_id, cur_node, nodes):
  names = set([_name_parse(r) for r in cur_node.refs.itervalues()])
  if any(r.endswith(".js") and not r.endswith("index.js") for r in cur_node.refs.itervalues()):
    cur_node.is_index = False
    assert len(names) == 1
    cur_node.name = list(names)[0]

    log(yellow("not index - has a '.js' ref"), cur_node.id)
  if any(r.endswith("/") for r in cur_node.refs.itervalues()):
    for ref_id, ref_path in cur_node.refs.iteritems():
      if ref_path.endswith("/"):
        # fix trailing slash OMG what.
        cur_node.refs[ref_id] = cur_node.refs[ref_id][:-1]
        nodes[ref_id].deps[cur_node_id] = cur_node.refs[ref_id][:-1]
      cur_node.is_index = True
      cur_node.name = "index.js"
  if len(names) == 2:
    assert "index.js" in names or "source.js" in names
    cur_node.is_index = True
    cur_node.name = "index.js"
    if "source.js" in names:
      print red("there is a non-standard index file that need to be configured for this source tree to build correctly: %s" % names)
      cur_node.name = "source.js"
    log(yellow("index"), cur_node.id, cur_node.name)
  elif len(names) == 1:
    cur_node.name = names.pop()
    if cur_node.name == "index.js":
      cur_node.is_index = True
  elif len(names) == 0:
    cur_node.name = "index.js" # % cur_node.id
    log(yellow("unnamed"), cur_node.id, "is entry:", cur_node.entry)
  else:
    log(names)


def check_for_folder_duplication(cur_node_id, cur_node, nodes):
  name = cur_node.name[:-len('.js')]
  for dep_id, dep_path in cur_node.deps.iteritems():
    dep_node = nodes[dep_id]
    if dep_path.startswith("./%s/" % name):
      # this is a module.js that wraps its contents
      # see npm/mout/object.js for an example
      cur_node.is_index = False
      log(cyan("not index - is a module with same-name folder sibling"), cur_node.name, cur_node_id)
      return
    for depref_id, depref_path in dep_node.refs.iteritems():
      if dep_path.startswith("./"):
        subpath = depref_path[:-len(dep_path) + 1]
        if subpath.endswith(name):
          cur_node.is_index = True
          cur_node.name = 'index.js'
          log(cyan("is index - found a local path with matching ancestor"), cur_node.name, cur_node.id)
          return

def check_for_sibling_isolation(cur_node_id, cur_node, nodes):
  # all sibling dependencies are only referred to locallay
  siblings = [
    nodes[dep_id] for
    dep_id, dep_path in cur_node.deps.iteritems()
    if dep_path.startswith('./') and len(dep_path.split('/')) == 2
  ]
  all_sib_refs = set(sum([sib.refs.keys() for sib in siblings],[]))
  outside_refs = all_sib_refs - set(s.id for s in siblings) - set([cur_node_id])
  if len(outside_refs) != 0:
    return # "i'm not the only parent"
  if siblings:
    sib_paths = sum([sib.refs.values() for sib in siblings], [])
    if all(
      sib_path.startswith("./") and len(sib_path.split("/")) == 2
      for sib_path in sib_paths
      ):
      cur_node.is_index = True
      cur_node.name = "index.js"
      log(green("is index - all siblings are unique decendant"), cur_node.id)

def check_for_node_root(cur_node_id, cur_node, nodes):
  for path in cur_node.refs.itervalues():
    if "/" not in path:
      cur_node.is_index = True
      cur_node.name = "index.js"
      return

def _print_depth_error(cur_file_id, depths):
  to_ret = ['file %d has inconsistent depths' % cur_file_id,'depths:']
  cur_depths = depths[cur_file_id]
  for id, d in sorted(cur_depths.iteritems(), key=lambda p: p[1]):
    ref = depths[id]
    path = nodes[id].deps[cur_file_id]
    refs = {nodes[k].name + "%d" % k: v for k, v in nodes[id].refs.iteritems()}
    spc = '\n          '
    name = nodes[id].name
    to_ret.append("id: {id:4} {name} {spc}depth: {d:2} {spc}{refs}{spc}{ref}{spc}{path}".format(**locals()))
  return '\n'.join(to_ret)

def min_max(l):
  return (max(e[0] for e in l), min(e[1] for e in l))

def build_tree(nodes, entry_node_ids):
  placed_file_ids = set()
  node_module_file_ids = set()
  file_ids_to_visit = deque(entry_node_ids)
  while file_ids_to_visit:
    cur_file_id = file_ids_to_visit.popleft()
    cur_file = nodes[cur_file_id]
    log(cyan("visiting %s" % cur_file))
    log("  %d left in file_ids_to_visit" % len(file_ids_to_visit))
    log("  %d/%d placed" % (len(placed_file_ids), len(nodes) - len(node_module_file_ids)))
    for dep_id, path in cur_file.deps.iteritems():
      log(green("  current dep"), dep_id, path)
      cur_dep = nodes[dep_id]
      if cur_dep.id in placed_file_ids:
        log(red("    (seen)"))
        pass
      elif path.startswith("."):
        file_ids_to_visit.append(cur_dep.id)
        folder_module.add_file_by_path(
          cur_file.folder, path, cur_dep
        )
        placed_file_ids.add(cur_dep.id)
        log(green("  cur dep placement:"), cur_dep)
      else:
        node_module_file_ids.add(cur_dep.id)
        log(red("  skipping %s" % path))
  return {
    "placed_file_ids": placed_file_ids,
    "node_module_file_ids": node_module_file_ids,
  }

def build_node_modules(nodes, referenced_node_ids, reachable_node_ids):
  """
    referenced nodes: nodes that are referenced from outside of scope and are therefore in the root node_modules folder

    reachable nodes: all of these should be placed relative to the root, others should be placed in local environments.

  """
  # reachable node ids are ones that are imported by src and are not local to a specific node. this isn't actually right, many node_modules may import from a shared node module, but it'll have to do until I can figure out detecting versions. This will at least not break, though it may unneccessarily duplicate file.
  node_root = folder_module.FolderNode("node_modules")
  root_node_module_members = defaultdict(set)
  for node_id in referenced_node_ids:
    node = nodes[node_id]
    paths = set(path for path in node.refs.itervalues() if not path.startswith("."))
    assert len(paths) == 1
    path = paths.pop()
    folder_module.add_file_by_path(node_root, path, node)
    module = path.split("/")[0]
    root_node_module_members[module].add(node_id)
  # pleace the reachable nodes
  build_tree(nodes, referenced_node_ids)
  # place the sub-node-modules
  return node_root


def get_local_reachable(nodes, start_ids):
  reachable = set()
  to_visit = deque(start_ids)
  visited = set([])
  while to_visit:
    cur = nodes[to_visit.popleft()]
    visited.add(cur.id)
    reachable.add(cur)
    for dep_id, dep_path in cur.deps.iteritems():
      if dep_path.startswith('.'):
        if dep_id not in visited:
          to_visit.append(dep_id)
  return visited