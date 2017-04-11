#!/usr/bin/env bash

set -e
set -x

curl --insecure -L https://raw.githubusercontent.com/makkus/freckles-dev/master/prepare.sh | bash -s --
