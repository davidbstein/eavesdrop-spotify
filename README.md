# eavesdrop-spotify

This is going to be a way to replace the "buddy list" in spotify with a stack-ranked list of your friends, where the top-ranked friend currently listening to music will be your personal DJ.

```
# todo: once this is written make a one-liner that uses curl to do all the magic
```

## How it works

This only works on OSX. You must have installed Spotify in your `/Applications` folder. It will create a new `SpotifyEavesdropper.app` in the folder you check out this repo. You can run that app when Spotify isn't running to get the modified verion.

### Can I use this to make arbitrary changes to the Spotify client?

I've included some scripts to make this pretty easy for your own projects.

First, run `./bin/setup.sh`, which will create the `unzipped` directory and the `SpotifyEavesdropper.app` application.

Next, run `./bin/unwrap.sh`, which will create a folder called `unbundled` that contains the source code and folder structure that was originally used to build the client.

__TODO__: at the moment, `entry_point.js` will be in the wrong location in the folder structure.

__TODO__: templates are kinda messy

Finally, make the changes that you want, bundle them into `bundle.js` using your favorite bundler, replace the appropriate `bundle.js` in the `unzipped` folder and run `./bin/build.sh`. You can also muck around with the CSS and `index.html`

After running `./bin/build.sh` your `SpotifyEavesdropper.app` will be running the new code.

## Warnings

This is a proof of concept, if you break your Spotify client it's not my fault :P

Running `./bin/setup.sh` will overwrite `unzipped/` and `SpotifyEavesdropper.app` with the current state of `/Applications/Spotify.app`
