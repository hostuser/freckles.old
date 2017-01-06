#!/usr/bin/env bash

# install pip
apt-get update
apt-get install -y python-setuptools python-dev libffi-dev libssl-dev git curl gcc

pip install --upgrade setuptools

easy_install pip
pip2 install ansible

# ansible
#TODO check if dir/file exists
#sudo mkdir /etc/ansible
#echo -e "[local]\n127.0.0.1   ansible_connection=local\n" | sudo tee /etc/ansible/hosts

#ansible-galaxy install -r requirements.yml

ln -s /vagrant/examples/example1/dotfiles /home/vagrant/dotfiles
cd /vagrant
python setup.py develop
