class FileNode(object):
  def __init__(self, id, source, deps, entry=False):
    self._id = id
    self._source = source
    self._deps = {id: path for path, id in deps.iteritems()}
    self._entry = entry
    self._refs = {}
    self.meta = MetaFileNode(self)

  def __getattr__(self, name):
    # cheap and dirty way to keep myself honest about not mutating this class
    assert name in ('source', 'id', 'deps', 'entry', 'refs')
    return self.__dict__['_'+name]

  def set_ref(self, ref_id, path):
    assert ref_id not in self.refs
    self.refs[ref_id] = path



class MetaFileNode(object):
  def __init__(self, node):
    self.node = node
    self.siblings = []
    self.known_path = []
    self.is_index = None
    self.folder = None
