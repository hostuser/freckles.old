#!/usr/bin/env bash

BASE_DIR="$HOME/.freckles"
PROOT_DIR="$BASE_DIR/opt/proot"
NIX_DIR="$BASE_DIR/opt/nix"
NIX_VERSION="1.11.5-x86_64-linux"
NIX_ROOT="$NIX_DIR/root"
NIX_BINARY_URL="https://nixos.org/releases/nix/latest/nix-$NIX_VERSION.tar.bz2"

mkdir -p "$PROOT_DIR"
cd "$PROOT_DIR"

wget http://static.proot.me/proot-x86_64
chmod u+x proot-x86_64

mkdir -p "$NIX_DIR"
cd "$NIX_DIR"
wget "$NIX_BINARY_URL"
tar xvjf nix-*bz2
rm nix-*bz2

mv "$NIX_DIR/nix-$NIX_VERSION" "$NIX_ROOT"

$PROOT_DIR/proot-x86_64 -b $NIX_DIR/root:/nix bash -c "cd /nix; ./install"

echo "Add:"
echo
echo "    $PROOT_DIR/proot-x86_64 -b $NIX_ROOT/:/nix bash"
echo "    source $HOME/.nix-profile/etc/profile.d/nix.sh"
echo
echo "to your .bashrc to be able to use this nix environment."
