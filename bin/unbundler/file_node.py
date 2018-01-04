class FileNode(object):
  def __init__(self, id, source, deps, entry=False):
    self._id = id
    self._source = source
    self._deps = {id: path for path, id in deps.items() if path != "dup"}
    self._dup_id = deps.get("dup", None)
    self._entry = entry
    self._refs = {}
    self.meta = MetaFileNode(self)

  def __getattr__(self, attr_name):
    # cheap and dirty way to keep myself honest about not mutating this class
    assert attr_name in ('source', 'id', 'deps', 'entry', 'refs')
    return self.__dict__['_'+attr_name]

  def __str__(self):
    if self._entry:
      return "<FileNode ENTRY {_id}>".format(**self.__dict__)
    return "<FileNode {_id}>".format(**self.__dict__)

  def set_ref(self, ref_id, path):
    assert ref_id not in self.refs
    self.refs[ref_id] = path



class MetaFileNode(object):
  # mutable container
  def __init__(self, node):
    self._node = node
    self.siblings = []
    self.is_index = None
    self.folder = None
    self.name = None

  def get_path(self):
    if self.folder is None:
      return "<UNKNOWN PATH>"
    return self.folder.get_path()

  def __getattr__(self, attr_name):
    # cheap and dirty way to keep myself honest about not mutating this class
    assert attr_name in ('source', 'id', 'deps', 'entry', 'refs', 'path')
    return self._node.__dict__['_'+attr_name]

  def __repr__(self):
    return "<MetaFileNode {path} / {name} - {_node}>".format(
      path=self.get_path(),
      **self.__dict__
    )