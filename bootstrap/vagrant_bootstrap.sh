#!/usr/bin/env bash

set -e

# bootstrap environment
/vagrant/bootstrap/bootstrap_deb.sh

echo 'source "$HOME/.freckles/virtualenv/freckles/bin/activate"' >> "$HOME/.bashrc"
ln -s /vagrant/examples/example_only_zsh/dotfiles /home/vagrant/dotfiles

# install freckles
source "$HOME/.freckles/virtualenv/freckles/bin/activate"
cd /vagrant
python setup.py develop
