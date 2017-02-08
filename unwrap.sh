# TODO: figure out where the overlap of shared libs is and automate this part
pushd .
mkdir unbundled
cd unbundled
# cp -r something.spa
# cd something.spa
# ../../node_modules/browser-unpack/bin/cmd.js < bundle.js > unbundled.json
# rm -rf raw
# mkdir raw
# cd raw
python -c "
import json
import os

with file('unbundled.json') as f:
  content = json.loads(f.read())

print 'unbundling %s files' % len(content)

num_to_name = {}
max_depth = 1
for c in content:
    for name, id in  c['deps'].iteritems():
        num_to_name[id] = name
        max_depth = max(len(name.split('..')), max_depth)

pwd = 'raw/_' + '_'.join('/' for _ in xrange(max_depth))
if not os.path.exists(pwd):
    os.makedirs(pwd)

for script in content:
  print script['id']
  name = 'raw/unknown/%s.js' % script['id']
  if num_to_name.get(script['id']):
    name = pwd + num_to_name[script['id']]
  if '.' not in os.path.basename(name):
    name += '.js'
  print 'writing: %s' % name
  dir = os.path.dirname(name)
  if not os.path.exists(dir) or not os.path.isdir(dir):
    print 'creating dir %s' % dir
    os.makedirs(os.path.dirname(name))
  with file(name, 'wb') as f:
    f.write(script['source'].encode('utf-8'))
"

popd