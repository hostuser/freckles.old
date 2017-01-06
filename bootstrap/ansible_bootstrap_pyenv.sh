#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive
set -e

export PATH="~/.pyenv/bin:$PATH"
DEFAULT_PYTHON_VERSION=2.7.8
function update_repos {
    if hash apt-get 2>/dev/null; then
        echo "Updating deb repos."
        sudo apt-get update
    fi
}

function install {
    if [ $1 == "deb" ] && hash apt-get 2>/dev/null; then
        echo "Installing $2 using apt-get..."
        sudo apt-get install -y $2
    elif [ $1 == "rpm" ] && hash yum 2>/dev/null; then
        echo "Installing $2 using yum..."
        sudo yum install $2
    elif [ $1 = "rpm_group" ] && hash yum 2>/dev/null; then
        echo "Installing $2 using yum groupinstall..."
        sudo yum groupinstall $2
    else:
        echo "$1 not found, and can't figure out how to install it."
        exit 1
    fi
}

if ! hash pyenv 2>/dev/null; then

    update_repos

    install deb build-essential
    install deb git
    install deb zlib1g-dev
    install deb libbz2-dev
    install deb libssl-dev
    install deb libffi-dev
    install rpm git
    install rpm_group "Development tools"
    install rpm zlib-devel
    install rpm bzip2
    install rpm bzip2-devel
    install rpm readline-devel
    install rpm sqlite
    install rpm sqlite-devel
    install rpm openssl-devel
    install rpm libffi-devel

    curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash

    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

    pyenv update
    pyenv install "$DEFAULT_PYTHON_VERSION"

    pyenv virtualenv "$DEFAULT_PYTHON_VERSION" freckles

else

    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

fi

pyenv activate freckles

pip install --upgrade setuptools

easy_install pip
