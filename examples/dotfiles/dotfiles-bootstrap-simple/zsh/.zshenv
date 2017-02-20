export PATH=$HOME/local/bin:$PATH
if [ -f $HOME/.nix-profile/etc/profile.d/nix.sh ];
then
	source $HOME/.nix-profile/etc/profile.d/nix.sh
fi

if [ -d $HOME/.pyenv ]; then
    export PATH="$HOME/.pyenv/bin:$PATH"
fi

export XDG_DATA_DIRS=$HOME/.nix-profile/share:/usr/local/share/:/usr/share

GPG_TTY=$(tty)
export GPG_TTY

export GTAGSLABEL=pygments
