#!/usr/bin/env bash

# create freckles virtualenv
FRECKLES_DIR="$HOME/.freckles"
FRECKLES_VIRTUALENV="$FRECKLES_DIR/data/venv"
export WORKON_HOME="$FRECKLES_VIRTUALENV"

set -e
set -x

touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress;
PROD=$(softwareupdate -l |
           grep "\*.*Command Line" |
           head -n 1 | awk -F"*" '{print $2}' |
           sed -e 's/^ *//' |
           tr -d '\n')
softwareupdate -i "$PROD" -v;

sudo easy_install pip

sudo pip install virtualenv

mkdir -p "$FRECKLES_DIR"
mkdir -p "$FRECKLES_DIR/data"
mkdir -p "$FRECKLES_VIRTUALENV"
cd "$FRECKLES_VIRTUALENV"

virtualenv freckles

# install freckles & requirements
source freckles/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools wheel

echo 'source "$HOME/.freckles/data/venv/freckles/bin/activate"' >> "$HOME/.bashrc"

source "$HOME/.freckles/data/venv/freckles/bin/activate"
cd /freckles
pip install -r requirements_dev.txt
python setup.py develop
