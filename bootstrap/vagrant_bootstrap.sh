#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive
set -e

cd /vagrant/bootstrap
./ansible_bootstrap_pyenv.sh

export PATH="~/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

#pip install -r requirements_dev.txt

cd /vagrant

pyenv activate freckles
python setup.py develop

ln -s /vagrant/examples/example_only_zsh/dotfiles /home/vagrant/dotfiles

cd /home/vagrant
echo 'export PATH="~/.pyenv/bin:$PATH"' >> .bashrc
echo 'eval "$(pyenv init -)"' >> .bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> .bashrc
