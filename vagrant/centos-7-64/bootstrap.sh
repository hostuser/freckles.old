#!/usr/bin/env bash

# create freckles virtualenv
FRECKLES_DIR="$HOME/.freckles"
FRECKLES_VIRTUALENV="$FRECKLES_DIR/data/venv"
export WORKON_HOME="$FRECKLES_VIRTUALENV"

set -e
set -x

sudo yum -y install epel-release
sudo yum -y update
sudo yum -y install wget git python-virtualenv stow openssl-devel sqlite-devel

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
#ln -s /freckles/examples/example_only_zsh/dotfiles /home/vagrant/dotfiles

# install freckles
source "$HOME/.freckles/data/venv/freckles/bin/activate"
cd /freckles
pip install -r requirements_dev.txt
python setup.py develop


#echo 'source "$HOME/.freckles/virtualenv/freckles/bin/activate"' >> "$HOME/.bashrc"
#ln -s /freckles/examples/example_only_zsh/dotfiles /home/vagrant/dotfiles

# install freckles
#source "$HOME/.freckles/virtualenv/freckles/bin/activate"
#cd /freckles
#python setup.py develop
