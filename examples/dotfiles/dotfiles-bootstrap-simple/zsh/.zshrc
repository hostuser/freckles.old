ZSHDIR=$HOME/.zsh

if [ -f ~/.zplug/init.zsh ]; then
    source ~/.zplug/init.zsh
fi


# history stuff
HISTFILE="$HOME/.zsh_history"
HISTSIZE=10000000
SAVEHIST=10000000
setopt BANG_HIST                 # Treat the '!' character specially during expansion.
setopt EXTENDED_HISTORY          # Write the history file in the ":start:elapsed;command" format.
setopt INC_APPEND_HISTORY        # Write to the history file immediately, not when the shell exits.
setopt SHARE_HISTORY             # Share history between all sessions.
setopt HIST_EXPIRE_DUPS_FIRST    # Expire duplicate entries first when trimming history.
setopt HIST_IGNORE_DUPS          # Don't record an entry that was just recorded again.
setopt HIST_IGNORE_ALL_DUPS      # Delete old recorded entry if new entry is a duplicate.
setopt HIST_FIND_NO_DUPS         # Do not display a line previously found.
setopt HIST_IGNORE_SPACE         # Don't record an entry starting with a space.
setopt HIST_SAVE_NO_DUPS         # Don't write duplicate entries in the history file.
setopt HIST_REDUCE_BLANKS        # Remove superfluous blanks before recording entry.
setopt HIST_VERIFY               # Don't execute immediately upon history expansion.
setopt HIST_BEEP                 # Beep when accessing nonexistent history.

zplug "zsh-users/zsh-history-substring-search"
zplug "zsh-users/zsh-syntax-highlighting"

#zplug "zplug/zplug"
if [ -f /usr/local/bin/activate.sh ]; then
   source /usr/local/bin/activate.sh
fi

zplug "plugins/autoenv", from:oh-my-zsh
zplug "plugins/git", from:oh-my-zsh, defer:2
zplug "plugins/pip", from:oh-my-zsh
zplug "plugins/lein", from:oh-my-zsh, defer:2
zplug "plugins/mvn", from:oh-my-zsh
zplug "plugins/gradle", from:oh-my-zsh, defer:2
zplug "plugins/python", from:oh-my-zsh
zplug "plugins/fabric", from:oh-my-zsh
zplug "plugins/debian", from:oh-my-zsh, defer:2
zplug "plugins/command-not-found", from:oh-my-zsh
zplug "plugins/extract", from:oh-my-zsh
zplug "plugins/docker", from:oh-my-zsh
zplug "plugins/sudo", from:oh-my-zsh
zplug "plugins/rsync", from:oh-my-zsh
zplug "plugins/pass", from:oh-my-zsh

#zplug "robbyrussell/oh-my-zsh", use:"lib/*.zsh", nice:14
zplug "themes/ys", from:oh-my-zsh, as:theme
#zplug 'dracula/zsh', as:theme
# zplug "tylerreckart/odin"

# Then, source plugins and add commands to $PATH
#zplug load --verbose
zplug load

# Install plugins if there are plugins that have not been installed
if ! zplug check --verbose; then
    printf "Install? [y/N]: "
    if read -q; then
        echo; zplug install
    fi
fi

#zplug install

setopt HIST_FIND_NO_DUPS
setopt IGNORE_EOF

# functions
mcd() {
    mkdir -p "$1"; cd "$1";
}

cls() {
    cd "$1"; ll;
}

backup() {
    mv "$1" "$1.bak"; mkdir "$1"
}

calibre_update_function() {
    sudo -v && wget -nv -O- https://raw.githubusercontent.com/kovidgoyal/calibre/master/setup/linux-installer.py | sudo python -c "import sys; main=lambda:sys.stderr.write('Download failed\n'); exec(sys.stdin.read()); main()"
}

git_checkout_interactive() {
    git_select_hash | xargs git checkout
}

git_select_hash() {
    git hist | percol | awk '{print $2}'
}

kill_process() {
    get_process_id | xargs kill
}

killkill_process() {
    get_process_id | xargs kill -9
}

get_process_id() {
    ps axu | percol --query="$USER " | awk '{print $2}'
}

get_process_parents() {
    get_process_id | xargs pstree --show-parents
}

current_firefox_tab_number() {
    python2 <<< $'import json\nf = open("/home/markus/.mozilla/firefox/febeprof.restore/sessionstore-backups/recovery.js", "r")\njdata = json.loads(f.read())\nf.close()\nprint str(jdata["windows"][0]["selected"])'
}

current_firefox_url() {
    sed -n "$(current_firefox_tab_number)p" <(python2 <<< $'import json\nf = open("/home/markus/.mozilla/firefox/febeprof.restore/sessionstore-backups/recovery.js", "r")\njdata = json.loads(f.read())\nf.close()\nfor win in jdata.get("windows"):\n\tfor tab in win.get("tabs"):\n\t\ti = tab.get("index") - 1\n\t\tprint tab.get("entries")[i].get("url")')
}

connect() {
    docker exec -i -t "$1" /bin/bash
}

debian_desktop() {
    docker run -it --rm -p 5901:5901 -v $1:/data -e USER=root debian-desktop bash
}

password_entries() {
      local IFS=$'\n'
      local prefix="${PASSWORD_STORE_DIR:-$HOME/.password-store}"
      find -L "$prefix" \( -name .git -o -name .gpg-id \) -prune -o $@ -print 2>/dev/null | sed -e "s#${prefix}/\{0,1\}##" -e 's#\.gpg##' | sort
}

function exists { which $1 &> /dev/null }


# aliases
# ls
alias lr='ls -larth'
alias sudo='sudo env "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH" '

# verbose copy using rsync
alias cpv="rsync -poghb --backup-dir=/tmp/rsync -e /dev/null --progress --"

# misc
alias dc='docker-compose'
alias fuck='eval $(thefuck $(fc -ln -1))'
alias FUCK='fuck'
alias f='fuck'
alias t='tree -L 2'
alias t1='tree -L 1'
alias t2='tree -L 2'
alias t3='tree -L 3'

alias lR='ls -R'

## git
alias gs='git status '
alias ga='git add '
alias gb='git branch '
alias gc='git commit '
alias gd='git diff '
alias go='git checkout '
alias gl='git hist '
alias gh='git_select_hash'
alias gt='git tag '
alias goc='git_checkout_interactive'

## systemctl
alias sc='systemctl'
alias scs='systemctl start'
alias scu='systemctl status'
alias scr='systemctl restart'
alias sct='systemctl stop'
alias sce='systemctl enable'
alias scd='systemctl disable'

alias scu='systemctl --user'
alias scus='systemctl --user start'
alias scuu='systemctl --user status'
alias scur='systemctl --user restart'
alias scut='systemctl --user stop'
alias scue='systemctl --user enable'
alias scud='systemctl --user disable'

## nix
alias n='nix-env -qaP|grep'
alias ni='nix-env -i'
alias nun='nix-env --uninstall'
alias nup='nix-channel --update && nix-env --upgrade'

# misc
alias my_ip='curl  http://echoip.com'
alias get_pass="password_entries | grep -i / | percol | sed 's/.*/\"&\"/' | xargs pass "

# temporary aliases
alias old_pass='export PASSWORD_STORE_DIR=~/.password-store-old pass'
alias op='PASSWORD_STORE_DIR=~/.password-store-old pass'
alias old_get_pass="PASSWORD_STORE_DIR=~/.password-store-old password_entries | grep -i / | percol | sed 's/.*/\"&\"/'| PASSWORD_STORE_DIR=~/.password-store-old xargs pass "

## apps
if exists htop; then
    alias top='htop'
fi
if exists di; then
    alias df='di'
fi

export ALTERNATE_EDITOR=""
export EDITOR="et"
export VISUAL="ec"

alias p='get_process_id'
alias pp='get_process_parents'
alias k='kill_process'
alias kk='killkill_process'

alias calibre_update='calibre_update_function'

alias dc='docker-compose'
alias de='docker exec -i -t'

alias psg="ps aux|grep"
alias port="netstat -tulanp"
alias listen="lsof -P -i -n"

# unalias
alias di=x
unalias di
alias ag=x
unalias ag

# bindkeys
bindkey -e
bindkey '^L' backward-kill-word  # helm-like delete last part of path


# autoloads
export WORDCHARS="_-"
autoload select-word-style
select-word-style normal

if exists percol; then
    function percol_select_history() {
        local tac
        exists gtac && tac="gtac" || { exists tac && tac="tac" || { tac="tail -r" } }
        BUFFER=$(fc -l -n 1 | eval $tac | percol --query "$LBUFFER")
        CURSOR=$#BUFFER         # move cursor
        zle -R -c               # refresh
    }

    zle -N percol_select_history
    bindkey '^S' percol_select_history
fi

if exists fasd; then
    eval "$(fasd --init auto)"
    bindkey '^X^A' fasd-complete    # C-x C-a to do fasd-complete (files and directories)
    bindkey '^X^F' fasd-complete-f  # C-x C-f to do fasd-complete-f (only files)
    bindkey '^X^D' fasd-complete-d  # C-x C-d to do fasd-complete-d (only directories)
fi

#if [ -e /usr/share/virtualenvwrapper/virtualenvwrapper.sh ]; then . /usr/share/virtualenvwrapper/virtualenvwrapper.sh; fi
#if [ -e /usr/local/bin/virtualenvwrapper.sh ]; then . /usr/local/bin/virtualenvwrapper.sh; fi
#export WORKON_HOME=$HOME/.virtualenvs

if [ -d $HOME/.pyenv ]; then
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi

if [[ $TERMINIX_ID ]]; then
    source /etc/profile.d/vte.sh
fi

export NIXPKGS=$HOME/src/system/nixpkgs

# less stuff (from: https://www.topbug.net/blog/2016/09/27/make-gnu-less-more-powerful/ )
export LESS='--quit-if-one-screen --ignore-case --status-column --LONG-PROMPT --RAW-CONTROL-CHARS --HILITE-UNREAD --tabs=4 --no-init --window=-4'
# Set colors for less. Borrowed from https://wiki.archlinux.org/index.php/Color_output_in_console#less
export LESS_TERMCAP_mb=$'\E[1;31m'     # begin bold
export LESS_TERMCAP_md=$'\E[1;36m'     # begin blink
export LESS_TERMCAP_me=$'\E[0m'        # reset bold/blink
export LESS_TERMCAP_so=$'\E[01;44;33m' # begin reverse video
export LESS_TERMCAP_se=$'\E[0m'        # reset reverse video
export LESS_TERMCAP_us=$'\E[1;32m'     # begin underline
export LESS_TERMCAP_ue=$'\E[0m'        # reset underline
# Set the Less input preprocessor.
if type lesspipe >/dev/null 2>&1; then
  export LESSOPEN='|lesspipe %s'
fi
# if type pygmentize >/dev/null 2>&1; then
  # export LESSCOLORIZER='pygmentize'
#fi


# don't use cached auto-complete
zstyle ":completion:*:commands" rehash 1
zstyle ':completion:*:sudo::' environ  PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH" HOME="/root"

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
export FZF_COMPLETION_OPTS='+c'
export FZF_COMPLETION_TRIGGER=';;'
export FZF_DEFAULT_COMMAND="find -L $HOME \( -path '*/.*' -o -fstype 'dev' -o -fstype 'proc' \) -prune -o -type f -print -o -type d -print -o -type l -print 2> /dev/null | sed 1d"
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND="find -L $HOME \( -path '*/\.*' -o -fstype 'dev' -o -fstype 'proc' \) -prune -o -type d -print 2> /dev/null | sed 1d"


