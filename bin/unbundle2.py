import json
import os
import sys


_count = [0]
def _get_count():
    _count[0] += 1
    return _count[0]


def parse_path(filepath):
  path = []
  (subpath, element) = os.path.split(filepath)
  element = element if '.' in element[1:] else "%s.js" % element
  fp = FilePath(path, element)
  while subpath != "":
    (subpath, element) = os.path.split(subpath)
    path.append(element)
  path.reverse()
  return fp


class FilePath:
  def __init__(self, parts, target):
    self.parts = parts
    self.target = target

  def __repr__(self):
    return "FilePath(%s, %s)" % (self.parts, self.target)


class File:
  def __init__(self, id, source, deps, name=None, entry=False):
    self.name = name
    self.id = id
    self.source = source
    self.entry = entry
    # id -> path from self to file
    self.deps = {id: path for path, id in deps.iteritems()}
    # id -> path to file from self
    self.refs = {}
    self.folder = None

  def set_name(self, name):
    assert self.name == None or self.name == name, \
      "%s != %s" % (self.name, name)
    self.name = name

  def get_path(self):
    return "%s %s" % (self.folder.repr_path(), self.name)

  def repr_source(self):
    to_ret = unicode()
    to_ret += "// GENERATED SOURCE FILE FROM BUNDLE\n"
    to_ret += "// %s %s\n" % (self.name, self.folder)
    to_ret += self.source
    return to_ret

  def perform_consistency_check(self):
    # check all deps get to this file

    # check all refs go to the correct file
    pass

class Folder:
  def __init__(self, name=None):
    self._id = _get_count()
    self.name = name or ("_%d" % self._id)
    self.children = {".": self}
    self.contents = {}

  def get_folder(self, name, create=True):
    folder = self.children.get(name)
    if not folder and create:
      folder = self.create_folder(name)
    return folder

  def create_folder(self, name):
    print "adding %s to %s" % (name, self.name)
    if name == "..":
      folder = Folder(name=None)
      folder.children[self.name] = self
      self.children['..'] = folder
    else:
      folder = Folder(name=name)
      folder.children['..'] = self
      self.children[name] = folder
    return folder

  def create_relative_file(self, filepath, file):
    current = self
    for folder in filepath.parts:
      current = current.get_folder(folder)
    if current.contents.get(file.name):
      if current.contents[file.name] != file:
        # print file.repr_source()
        # print current.contents[file.name].repr_source()
        raise("different files in the same place")
    if file.folder != None:
      assert file.folder == current, "%s no good: %s != %s" % \
        (file.name, file.folder.name, current.name)
    else:
      current.contents[file.name] = file
      file.folder = current

  def repr_tree(self, depth=0, show_files="count"):
    space = ".  " * depth + ".  "
    to_ret = "%s%s/" % (space, self.name)
    if show_files == "count":
      to_ret += " (%d files) \n" % (len(self.contents))
    else:
      to_ret += "\n"
    for child in sorted(self.children.values()):
      if child == self or child == self.children.get(".."):
        continue
      to_ret += "%s" % (child.repr_tree(depth+1, show_files))
    if show_files == "all":
      for file in self.contents.values():
        to_ret += "%s |-(%d)%s\n" % (space, file.id, file.name)
    return to_ret

  def repr_path(self):
    folder = self
    path = ""
    while ".." in folder.children:
      folder = folder.children['..']
      path = "%s/%s" % (folder.name, path)
    return path

class ReconstructedSource:
  def __init__(self, file_target="unbundled.json"):
    self.module_root = Folder("module_folder")
    # creates self.entry and self.files
    self.entry = None
    self.files = None
    self._parse_files(file_target)
    # construct folders
    self._construct_folders(self.files, self.module_root)
    # find src root
    src_root = self.entry.folder
    while ".." in src_root.children:
      src_root = src_root.children['..']

  def get_src_root(self):
    src_root = self.entry.folder
    while ".." in src_root.children:
      src_root = src_root.children['..']
    return src_root

  def _parse_files(self, file_target):
    with open(file_target) as f:
      bundle = json.loads(f.read())
    files = {}
    for raw_file in bundle:
      file = File(**raw_file)
      files[file.id] = file
      if file.entry:
        assert not self.entry, "too many entry points"
        self.entry = file
        self.entry.set_name("entry_point.js")
        self.entry.folder = Folder("entry_folder")
        self.entry.folder.contents[self.entry.name] = self.entry
    for file in files.itervalues():
      for dep_id, dep_path in file.deps.iteritems():
        files[dep_id].refs[file.id] = dep_path
    self.files = files

  def _construct_folders(self, files, module_root):
    visited = set()
    to_visit = [self.entry]
    while to_visit:
      raw_input()
      current_file = to_visit.pop()
      current_folder = current_file.folder
      visited.add(current_file.id)
      assert len(visited) <= len(files)
      print "\n====\nvisiting", current_file.id, current_file.get_path()
      print "current queue legth: ", len(to_visit)
      print "current structure:"
      print self.get_src_root().repr_tree(depth=2, show_files="all")
      print self.module_root.repr_tree(depth=2, show_files="all")
      print "adding deps:"
      for id, path in current_file.deps.iteritems():
        print "  ", id, path
        target_dep = files[id]
        file_path = parse_path(path)
        if not file_path.parts:
          file_path = parse_path("%s/main.js" % path)
        target_dep.set_name(file_path.target)
        if file_path.parts[0] in (".", ".."):
          current_folder.create_relative_file(file_path, target_dep)
        else:
          module_root.create_relative_file(file_path, target_dep)
        if target_dep.id not in visited:
          to_visit.append(target_dep)

  def validate(self):
    pass


def run_tests():
  print "test parse_path"
  fp1 = parse_path("module/some/silly/file")
  assert fp1.parts == ["module", "some", "silly"], fp1
  assert fp1.target == "file.js", fp1
  fp2 = parse_path("./file.js")
  assert fp2.parts == ["."] and fp2.target == "file.js", fp2
  fp3 = parse_path("react")
  assert fp3.parts == [] and fp3.target == "react.js", fp3

  print "test simple reference"


def run():
  rs = ReconstructedSource()
  print ""
  print rs.get_src_root().repr_tree()
  print rs.module_root.repr_tree()

if __name__ == '__main__':
  if sys.argv[1] == "test":
    run_tests()
  elif sys.argv[1] == "run":
    run()
