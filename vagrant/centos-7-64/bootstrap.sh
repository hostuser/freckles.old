#!/usr/bin/env bash

set -e

# bootstrap environment
/freckles/bootstrap/bootstrap_rpm.sh

echo 'source "$HOME/.freckles/virtualenv/freckles/bin/activate"' >> "$HOME/.bashrc"
ln -s /freckles/examples/example_only_zsh/dotfiles /home/vagrant/dotfiles

# install freckles
source "$HOME/.freckles/virtualenv/freckles/bin/activate"
cd /freckles
python setup.py develop
