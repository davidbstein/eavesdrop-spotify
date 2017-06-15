import json
import os
import sys
from collections import namedtuple

_VERBOSE_LEVEL = 3
_DEFAULT_FILE_VIEW = "all"
_WRITE=False

def log(message):
  if _VERBOSE_LEVEL >= 3:
    print message

def notify(message):
  if _VERBOSE_LEVEL >= 2:
    print message

def warn(message):
  if _VERBOSE_LEVEL >= 1:
    print message


_count = [0]
def _get_count():
  _count[0] += 1
  return _count[0]


class MultipleLocationError(Exception):
  def __init__(self, source_file, target_file, original_folder, new_folder):
    super(MultipleLocationError, self)
    self.source_file = source_file
    self.target_file = target_file
    self.original_folder = original_folder
    self.new_folder = new_folder

class NameMismatchError(Exception):
  def __init__(self, file, name):
    super(NameMismatchError, self)
    self.file = file
    self.name = name

FilePath = namedtuple("FilePath", ["parts", "target"])

def test_parse_path():
  fp1 = parse_path("module/some/silly/file")
  assert fp1.parts == ["module", "some", "silly"], fp1
  assert fp1.target == "file.js", fp1
  fp2 = parse_path("./file.js")
  assert fp2.parts == ["."] and fp2.target == "file.js", fp2
  fp3 = parse_path("react")
  assert fp3.parts == [] and fp3.target == "react.js", fp3

def parse_path(filepath):
  path = []
  (subpath, element) = os.path.split(filepath)
  # # element = element if '.' in element[1:] else "%s.js" % element
  # removed this becaue json gets turned into js by spotify's
  # bundler, though this may be the right thing to do if I ever
  # go back and tweak the
  element = element if element.endswith(".js") else "%s.js" % element
  fp = FilePath(path, element)
  while subpath != "":
    (subpath, element) = os.path.split(subpath)
    path.append(element)
  path.reverse()
  return fp

class File(object):
  def __init__(self, id, source, deps, name=None, entry=False):
    self.name = name
    self.id = id
    self.source = source
    self.entry = entry
    # id -> path from self to file
    self.deps = {id: path for path, id in deps.iteritems()}
    # id -> path to file from self
    self.refs = {}
    self.index_flag = False
    self.folder = None

  def reset():
    self.refs = {}
    self.folder = None

  def flag_as_index(self):
    self.index = True

  def set_name(self, name):
    if self.name != None and self.name != name:
      raise NameMismatchError(self, name)
    self.name = name

  def get_path(self):
    name = self.name if not self.index_flag else "index.js"
    return "%s%s" % (self.folder.repr_path(), name)

  def get_source(self):
    to_ret = unicode()
    to_ret += "// GENERATED SOURCE FILE FROM BUNDLE\n"
    to_ret += "// %s %s\n" % (self.name, self.folder)
    to_ret += self.source
    return to_ret


class Folder(object):
  def __init__(self, name, module_root=None, is_module_root=False):
    if is_module_root:
      assert not module_root
      module_root = self
    assert module_root
    self._id = _get_count()
    self.module_root = module_root
    self.name = name or ("_%d" % self._id)
    self.children = {".": self}
    self.contents = {}

  def get_root(self):
    src_root = self
    while ".." in src_root.children:
      src_root = src_root.children['..']
    return src_root

  def get_parent(self):
    return self.get_child_folder("..")

  def get_child_folder(self, name, create=True):
    folder = self.children.get(name)
    if not folder and create:
      folder = self._create_folder(name)
    return folder

  def repr_path(self):
    folder = self
    path = ""
    path = "{name}/".format(name=folder.name)
    while ".." in folder.children:
      folder = folder.children['..']
      path = "{name}/{path}".format(name=folder.name, path=path)
    return path

  def _create_folder(self, name):
    log("adding %s to %s (%d)" % (name, self.name, self._id))
    if name == "..":
      folder = Folder(name=None, module_root=self.module_root)
      folder.children[self.name] = self
      self.children['..'] = folder
    else:
      folder = Folder(name=name, module_root=self.module_root)
      folder.children['..'] = self
      self.children[name] = folder
    return folder

  def create_relative_file(self, path, file):
    assert file.name
    filepath = parse_path(path)
    is_module = not filepath.parts
    if is_module:
      filepath = parse_path("./%s/%s" % (path, file.name))
    if is_module or filepath.parts[0] not in ('.', '..'):
      current = self.module_root
    else:
      current = self
    for folder in filepath.parts:
      current = current.get_folder(folder)
    assert current.contents.get(file.name, file) == file, \
      "different files in the same place %s %s" % (path, filepath)
    if is_module:
      current.module_root = current.create_folder("node_modules")
    if file.folder == None:
      current.contents[file.name] = file
      file.folder = current
    if file.folder != current:
      raise MultipleLocationError(
        "tried to write %s to two locations" % file.name,
        file,
        current,
      )

class ReconstructedSource:
  def __init__(self, file_target="unbundled.json"):
    # creates self.entry and self.files
    self.entry = None
    self.files = None
    self._parse_files(file_target)
    # construct folders
    self._construct_folders(self.files, self.entry.folder.module_root)
    # find src root and attach node_modules
    src_root = self.entry.folder
    while ".." in src_root.children:
      src_root = src_root.children['..']
    self.root = src_root
    assert self.entry.folder.module_root.name not in self.root.children
    module_root = self.entry.folder.module_root
    self.root.children[module_root.name] = module_root
    module_root.children['..'] = self.root

  def get_src_root(self):
    src_root = self.entry.folder.get_root()
    return src_root

  def _parse_files(self, file_target):
    with open(file_target) as f:
      bundle = json.loads(f.read())
    files = {}
    module_root = Folder("node_modules", self_root=True)
    for raw_file in bundle:
      file = File(**raw_file)
      files[file.id] = file
      if file.entry:
        assert not self.entry, "too many entry points"
        self.entry = file
        self.entry.set_name("entry_point.js")
        self.entry.folder = Folder("entry_folder", module_root)
        self.entry.folder.contents[self.entry.name] = self.entry
    for file in files.itervalues():
      for dep_id, dep_path in file.deps.iteritems():
        files[dep_id].refs[file.id] = dep_path
    self.files = files

  def _construct_folders(self, files, module_root):
    visited = set()
    to_visit = [self.entry]
    while to_visit:
      current_file = to_visit.pop()
      current_folder = current_file.folder
      visited.add(current_file.id)
      assert len(visited) <= len(files)
      log(
        "\n====\nvisiting: %s %s" %
        (current_file.id, current_file.get_path())
      )
      log("current queue legth: %d" % len(to_visit))
      log("adding deps to %s:" % current_file.get_path())
      for id, path in current_file.deps.iteritems():
        log("  %2d %s" % (id, path))
        target_dep = files[id]
        self._place_relative_file(current_folder, target_dep, path)
        if target_dep.id not in visited:
          to_visit.append(target_dep)

  def _place_relative_file(self, current_folder, target_dep, path):
    parsed_path = parse_path(path)
    if target_dep.index_flag and not path.endswith("index.js"):
      path += "/index.js"
    if not parsed_path.parts:
      # this is a module entry.
      target_dep.set_name("index.js")
    else:
      try:
        target_dep.set_name(parsed_path.target)
      except NameMismatchError, nme:
        target_is_index = target_dep.name == "index.js"
        if not target_is_index and parsed_path.target == "index.js":
          turn_file_to_index(target_dep)
        else:
          print target_dep.name, parsed_path.target, path
          raise nme
    current_folder.create_relative_file(path, target_dep)

  def validate(self):
    pass


def run_tests():
  log("test parse_path")
  fp1 = parse_path("module/some/silly/file")
  assert fp1.parts == ["module", "some", "silly"], fp1
  assert fp1.target == "file.js", fp1
  fp2 = parse_path("./file.js")
  assert fp2.parts == ["."] and fp2.target == "file.js", fp2
  fp3 = parse_path("react")
  assert fp3.parts == [] and fp3.target == "react.js", fp3
  log("test simple reference")


def run(webpack_template):
  try:
    rs = ReconstructedSource()
  except MultipleLocationError, mle:
    mle.print_details()
    ## TODO: if target_path == current_location.parent then we started
    ## one level too high because our origin is in fact
    ## "orogin/index.js"
    raise mle

def build_tree(webpack_template):
  notify("working...")
  rs = ReconstructedSource()
  notify("Finished rolling up files")
  notify("Writing files:")
  for id in xrange(1,1+len(rs.files)):
    script = rs.files[id]
    path = "raw/%s" % (script.get_path(), )
    notify("writing file {id}: {path}".format(
      id=id,
      path=path,
    ))
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
      os.makedirs(os.path.dirname(path))
    with open(path, 'wb') as f:
      f.write(script.source.encode('utf-8'))
    with open("webpack.config.js", "wb") as f:
      f.write(webpack_template.format(
        entry_path=rs.entry.get_path()
      ))

_WEBPACK_TEMPLATE = """
var path = require('path');

module.exports = {{
  entry: './raw/{entry_path}',
  output: {{
    filename: 'rebundled.js'
  }}
}};
"""

if __name__ == '__main__':
  if sys.argv[1] == "test":
    run_tests()
  elif sys.argv[1] == "run":
    run(_WEBPACK_TEMPLATE)
  elif sys.argv[1] == "build_tree":
    build_tree(_WEBPACK_TEMPLATE)
