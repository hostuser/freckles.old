#!/usr/bin/env bash

if [ -e "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then source "$HOME/.nix-profile/etc/profile.d/nix.sh"; fi

cd {{cookiecutter.freckles_playbook_dir}}

export PATH="../bin:$PATH"


ansible-playbook {{cookiecutter.freckles_ask_sudo}} {{cookiecutter.freckles_playbook}}
