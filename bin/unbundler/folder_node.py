class FolderNode(object):
  def __init__(self, trunk_id=None, parent=None):
    """
      trunk_id - number of steps down from the entry point
    """
    self._is_trunk = trunk_id is not None
    self._parent = parent

  def get_parent(self):
    pass

  def get_folder(self, name, create=False):
    pass

  def get_file(self, name):
    pass

  def add_file(self, name):
    pass

  def get_path(self):
    pass

  def print_contents(self, indent=0, files=True):
    pass

