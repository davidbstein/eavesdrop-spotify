DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
rm -rf $DIR/../SpotifyEavesdrop.app
cp -r /Applications/Spotify.app $DIR/../SpotifyEavesdrop.app

pushd .
cd $DIR/..
mkdir unbundled
pwd

for rawfolder_name in $DIR/../SpotifyEavesdrop.app/Contents/Resources/Apps/a*;
do
  folder_name=$(echo $rawfolder_name | tr "/" "\n" | tail -n1)
  cd $DIR/../unbundled
  cp -r $DIR/../unzipped/$folder_name $folder_name
  cd $folder_name
  echo
  echo "unwrapping $folder_name"
  ../../node_modules/browser-unpack/bin/cmd.js < bundle.js > unbundled.json
  python ../../bin/unpack_bundle.py run
done

popd