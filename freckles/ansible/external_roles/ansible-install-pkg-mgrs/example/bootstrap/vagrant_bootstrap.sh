#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive

set -x
set -e

sudo apt-get update
sudo apt-get install -y build-essential git python-dev python-virtualenv libssl-dev libffi-dev stow libsqlite3-dev python-pip zile

sudo pip install --upgrade pip
sudo pip install --upgrade setuptools wheel ansible

