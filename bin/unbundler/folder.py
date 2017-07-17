import colors


VERBOSE = False
def log(*s):
  if VERBOSE:
    print ' '.join(map(str, s))


class FolderNode(object):
  def __init__(self, name, trunk_depth=None, parent=None):
    """
      trunk_id - number of steps down from the entry point
    """
    self._trunk_depth = trunk_depth
    # it's a concious choice to not just have a child named
    # '..', as it helps me not make obvious mistakes in some
    # of my scripts /shrug
    self._parent = parent
    self._children = {}
    self._files = {}
    self._name = name

  def get_parent(self):
    if self._parent:
      return self._parent
    elif not self._parent and self._trunk_depth:
      new_parent = FolderNode(
        "_trunk_%s" % (self._trunk_depth+1),
        trunk_depth=self._trunk_depth+1
      )
      new_parent._add_folder(self)
      return new_parent
    raise Error("no parent found")

  def get_folder(self, name, create=False):
    to_ret = self._children.get(name)
    if to_ret:
      return to_ret
    elif create:
      new_folder = self._add_folder(FolderNode(name))
      log(" `--> created ", new_folder)
      return new_folder
    else:
      return None

  def get_file(self, name):
    pass

  def get_name(self):
    return self._name

  def add_file(self, file_node):
    assert file_node.name
    assert (
      file_node.name not in self._files or
      file_node == self._files[file_node.name]
      ), \
      "\n --".join(map(str, [
        self._files.keys(), file_node, self._files[file_node.name]
      ]))
    file_node.folder = self
    self._files[file_node.name] = file_node

  def check_file(self, file_name):
    assert file_name in files

  def _add_folder(self, folder_node):
    assert folder_node._name, folder_node
    assert folder_node._name not in self._children
    assert folder_node._parent == None
    folder_node._parent = self
    self._children[folder_node._name] = folder_node
    return folder_node

  def get_path(self):
    cur = self
    folders = [cur]
    while cur._parent:
      cur = cur._parent
      folders.append(cur)
    return '/'.join(cur._name for cur in reversed(folders))

  def print_contents(self, indent=0, files=True):
    pass

  def print_subtree(self):
    spacer = colors.green("  |")
    filetag = colors.green("--- ")
    def recursive_print(folder, depth=0):
      gap = spacer * depth
      print "{gap}\033[00m\033[32;1m{fname}/\033[00m".format(
        gap=gap[:-6], fname=folder._name
      )
      for subfolder in sorted(folder._children.itervalues(), key=lambda x: x._name):
        recursive_print(subfolder, depth+1)
      for file in sorted(folder._files.itervalues(), key=lambda x: x.name):
        print "{gap}{filetag}({id}) {name}".format(
          gap=gap, filetag=filetag, id=file.id, name=file.name
        )
    recursive_print(self)

  def __repr__(self):
    return "<FolderNode %s>" % self.get_path()


class FolderTree(object):
  def __init__(self, root, node_module_root):
    self._root = root
    self.node_module_root = node_module_root

  def set_entry(self, entry_node):
    self._root.add_file(entry_node)

  def get_root(self):
    root = self._root
    while root._parent:
      root = root._parent
    return root

  def print_root(self):
    self.get_root().print_subtree()



def depth_diff(path):
  path_parts = path.split('/')[:-1]
  diff = 0
  for part in path_parts:
    if part == '..':
      diff -= 1
    elif part != '.':
      diff += 1
  return diff

def add_file_by_path(start, path, file):
  path_parts = path.split('/')
  cur = start
  if not file.is_index:
    file.name = path_parts[-1]
    path_parts = path_parts[:-1]
  else:
    file.name = 'index'
  if not file.name.endswith(".js"):
    file.name += ".js"
  for part in path_parts:
    log("--> cur, part:", cur, part)
    if part == ".":
      cur = cur
    elif part == "..":
      cur = cur.get_parent()
    else:
      cur = cur.get_folder(part, create=True)
  cur.add_file(file)
