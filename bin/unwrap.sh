DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
rm -rf $DIR/../SpotifyEavesdrop.app
cp -r /Applications/Spotify.app $DIR/../SpotifyEavesdrop.app

pushd .
cd $DIR/..
mkdir unbundled
pwd

for rawfn in $DIR/../SpotifyEavesdrop.app/Contents/Resources/Apps/b*;
do
  fn=$(echo $rawfn | tr "/" "\n" | tail -n1)
  cd $DIR/../unbundled
  cp -r $DIR/../unzipped/$fn $fn
  cd $fn
  echo
  echo $fn
  ../../node_modules/browser-unpack/bin/cmd.js < bundle.js > unbundled.json
  python ../../bin/unbundle.py
done

popd