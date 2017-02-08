DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
rm -rf $DIR/../SpotifyEavesdrop.app
cp -r /Applications/Spotify.app $DIR/../SpotifyEavesdrop.app

pushd .
cd $DIR/..
mkdir unzipped
cd unzipped
pwd

for rawfn in $DIR/../SpotifyEavesdrop.app/Contents/Resources/Apps/*;
do
  fn=$(echo $rawfn | tr "/" "\n" | tail -n1)
  mkdir ${fn}
  cd ${fn}
  yes | unzip -a $rawfn
  cd $DIR/../unzipped
done

popd