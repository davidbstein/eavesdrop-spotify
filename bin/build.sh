DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

for a in $DIR/../SpotifyEavesdrop.app/Contents/Resources/Apps/*;
do
  rm $a
  fn=$(echo $a | tr "/" "\n" | tail -n1)
  echo "building: ${fn}"
  cd $DIR/../unzipped/${fn}
  zip -r $a . * > /dev/null;
  cd -
done;
