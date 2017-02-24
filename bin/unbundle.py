import json
import os

count = [0]
def _get_count():
    count[0] += 1
    return count[0]

class Node:
    def __init__(self):
        self.name = None
        self.children = {}
        self.contents = {}
        self.default_name = "_%s" % _get_count()
        self.parent = None

    def add_file(self, script):
        self.contents[script['id']] = script
        script['node'] = self

    def get_parent(self):
        if self is module_node:
            return self
        if not self.parent:
            self.parent = Node()
            self.parent.children[self.name or self.default_name] = self
        return self.parent

    def get_child(self, name):
        if not self.children.get(name):
            new_child = Node()
            new_child.name = name
            new_child.parent = self
            self.children[name] = new_child
            return new_child
        else:
            return self.children[name]

    def _follow_step(self, name):
        if name == '..':
            return self.get_parent()
        if name == '.':
            return self
        assert '.' not in name
        return self.get_child(name)

    def add_relative_file(self, path, script):
        if '/' not in path:
            module_node.add_relative_file("./%s/%s" % (path, path), script)
            return module_node
        path = os.path.dirname(path)
        cur = self
        # print "path: %s" % path
        # print "location: %s" % cur.get_path()
        for item in path.split('/'):
            # print "%s into %s" % (item, cur.name)
            cur = cur._follow_step(item)
            # print "  %s" % cur.get_path()
        cur.add_file(script)
        # print "added to %s /" % (cur.get_path())
        return cur

    def get_path(self):
        cur = self
        path = []
        while cur:
            path.append(cur.name or cur.default_name)
            cur = cur.parent
        return '/'.join(reversed(path))

def visit(id, visited, to_visit):
    script = num_to_script[id]
    node = script['node']
    log = "%s/%s -> " % (node.get_path(), num_to_name[id])
    visited.add(id)
    for path, id_ in script['deps'].iteritems():
        log += "\n\t%s" % path
        to_visit.append(id_)
        dest = node.add_relative_file(path, num_to_script[id_])
        log += "\n\t%s\n" % dest.get_path()
    # print log

if __name__ == '__main__':

    with file('unbundled.json') as f:
        content = json.loads(f.read())

    print 'unbundling %s files' % len(content)

    num_to_script = {}
    num_to_name = {}
    for script in content:
        num_to_script[script['id']] = script
        for name, id in  script['deps'].iteritems():
            num_to_name[id] = os.path.basename(name)

    for script in content:
        if not num_to_name.get(script['id']):
            entry_point = script
            break

    num_to_name[entry_point['id']] = "entry_point.js"
    print "entry point: %s" % entry_point['id']
    entry_node = Node()
    entry_node.add_file(entry_point)
    module_node = Node()
    module_node.default_name = "node_modules"

    to_visit = [entry_point['id']]
    visited = set()

    while to_visit:
        next_id = to_visit.pop()
        if next_id in visited:
            continue
        visit(next_id, visited, to_visit)

    print "visited %d scripts" % len(visited)
    root_node = entry_node
    while root_node.parent:
        root_node = root_node.parent


for script in content:
    if num_to_name.get(script['id']):
        name = "raw/" + script['node'].get_path() + "/" + num_to_name[script['id']]
    if '.' not in os.path.basename(name):
        name += '.js'
    # print 'writing %d: %s' % (script['id'], name)
    dir = os.path.dirname(name)
    if not os.path.exists(dir) or not os.path.isdir(dir):
        os.makedirs(os.path.dirname(name))
    with file(name, 'wb') as f:
        f.write(script['source'].encode('utf-8'))
