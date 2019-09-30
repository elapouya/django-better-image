#!/usr/bin/env bash

# To be run *in* "scripts" dir
# uses yui-compressor, closure compiler and sass :
# download compiler .jar here : https://github.com/google/closure-compiler
# sudo apt install yui-compressor
# sudo apt-get install ruby-full build-essential rubygems
# sudo gem install sass
# if needed :
# sudo gem install rb-inotify

BETTERIMAGEDIR=$(dirname $0)/../django_better_image
CSSDIR=$BETTERIMAGEDIR/static/django_better_image/css
JSDIR=$BETTERIMAGEDIR/static/django_better_image/js

BETTERIMAGE_SCSS=$CSSDIR/better_image.scss
BETTERIMAGE_CSS=$CSSDIR/better_image.css
BETTERIMAGE_MIN_CSS=$CSSDIR/better_image.min.css
BETTERIMAGE_JS=$JSDIR/better_image.js
BETTERIMAGE_MIN_JS=$JSDIR/better_image.min.js

JS_COMPRESS="java -jar $HOME/bin/closure-compiler.jar --language_out=ECMASCRIPT_2015"
YUI_COMPRESS=yui-compressor
SAAS=/usr/local/bin/sass

if [[ -d $CSSDIR ]]
then
    set -x
    $SAAS $BETTERIMAGE_SCSS $BETTERIMAGE_CSS
    $YUI_COMPRESS $BETTERIMAGE_CSS -o $BETTERIMAGE_MIN_CSS
    $YUI_COMPRESS $CSSDIR/better_image_fonticons.css -o $CSSDIR/better_image_fonticons.min.css
    set +x
fi

if [[ -d $JSDIR ]]
then
    set -x
    rm -f $JSDIR/better_image.min.js
    $JS_COMPRESS $JSDIR/better_image.js > $JSDIR/better_image.min.js

    rm $JSDIR/better_image_utils.js
    cat $JSDIR/util.js >> $JSDIR/better_image_utils.js
    cat $JSDIR/popover.js >> $JSDIR/better_image_utils.js
    cat $JSDIR/tooltip.js >> $JSDIR/better_image_utils.js
    $JS_COMPRESS $JSDIR/better_image_utils.js > $JSDIR/better_image_utils.min.js

    set +x
fi