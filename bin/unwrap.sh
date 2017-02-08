DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
rm -rf $DIR/../SpotifyEavesdrop.app
cp -r /Applications/Spotify.app $DIR/../SpotifyEavesdrop.app

pushd .
cd $DIR/..
mkdir unbundled
pwd

for rawfn in $DIR/../SpotifyEavesdrop.app/Contents/Resources/Apps/*;
do
  fn=$(echo $rawfn | tr "/" "\n" | tail -n1)
  cd $DIR/../unbundled
  cp -r $DIR/../unzipped/$fn $fn
  cd $fn
  ../../node_modules/browser-unpack/bin/cmd.js < bundle.js > unbundled.json
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
  name = 'raw/entry_point%s.js' % script['id']
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
done

popd