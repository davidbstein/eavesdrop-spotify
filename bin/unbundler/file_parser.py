"""
Creates a series of FileNode objects from an input unbundled pack

see the `browser-unpack` npm module to generate an input file

unbundled.json must contain a list of
{
  id: unique ID of file
  source: raw source code
  deps: a dictionary of relative path to ID
  entry: (optional) a boolean set to true if this was the entry point for the build
}
"""

from unbundler.file_node import FileNode
import json

def parse_file(file_target="unbundled.json"):
  """
  returns acn immutabile dictionary of FileNodes keyed on ID
  """
  with open(file_target) as f:
    content = json.loads(f.read())
  nodes = {
    raw_file_node['id']: FileNode(**raw_file_node)
    for raw_file_node in content
  }
  for ref_id, node in nodes.items():
    if node._dup_id:
      # undo the dedup webpack optimization
      node._source = nodes[node._dup_id].source
    # add dependency paths
    for dep_id, path in node.deps.items():
      nodes[dep_id].set_ref(ref_id, path)
  return nodes