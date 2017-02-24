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
  element = element if element.endswith(".js") else "%s.js" % element
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
    if not name:
      assert entry
      self.name = "entry_point.js"
    self.id = id
    self.source = source
    self.entry = entry
    # id -> path from self to file
    self.deps = {id: path for path, id in deps.iteritems()}
    # id -> path to file from self
    self.refs = {}
    self.folder = None

  def get_path(self):
    pass

  def perform_consistency_check(self):
    # check all deps get to this file

    # check all refs go to the correct file


class Folder:
  def __init__(self, name=None):
    self._id = _get_count()
    self.name = name or ("_%d" % self._id)
    self.children = {".": self}
    self.contents = {}

  def get_folder(self, name, create=True):
    folder = self.children.get("name")
    if not folder and create:
      folder = self.create_folder(name)
    return folder

  def create_folder(self, name):
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
    for folder in reversed(filepath.parts):
      current = current.get_folder(folder)
    if current.contents.get(file.name) or file.folder != None:
      assert current.contents[file.name] == file
      assert file.folder == current
    else:
      current.contents[file.name] = file
      file.folder = current


class ReconstructedStructure:
  def __init__(self, file_target="unbundled.js"):
    self.file_target = file_target
    self.module_root = Folder("module_folder")
    self.entry_folder = Folder("entry_folder")
    self.entry = {}
    self.files = {}
    self.parse_files()
    # construct folders
    # find src root

  def parse_files(self):
    with open(self.file_target) as f:
      bundle = json.loads(f.read())
    files = {}
    for raw_file in bundle:
      file = File(**raw_file)
      files[file.id] = file
      if file.entry:
        assert not entry, "too many entry points"
        self.entry = file
    for file in files.itervalues():
      for dep_id, dep_path in file.deps.iteritems():
        files[dep_id].refs[file.id] = dep_path
    assert files['entry'], "no entry point"
    self.files = files


def run_tests():
  print "test parse_path"
  fp1 = parse_path("module/some/silly/file")
  assert fp1.parts == ["module", "some", "silly"] and fp1.target == "file.js", fp1
  fp2 = parse_path("./file.js")
  assert fp2.parts == ["."] and fp2.target == "file.js", fp2
  fp3 = parse_path("react")
  assert fp3.parts == [] and fp3.target == "react.js", fp3

  print "test simple reference"


if __name__ == '__main__':
  if sys.argv[1] == "test":
    run_tests()
  elif sys.argv[1] == "run":
    run()