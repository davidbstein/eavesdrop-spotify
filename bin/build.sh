DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

for a in $DIR/../SpotifyEavesdrop.app/Contents/Resources/Apps/*;
do
  rm $a
  cd $DIR/../unzipped/${a:64}
  zip -r $a . *;
  cd -
done;
