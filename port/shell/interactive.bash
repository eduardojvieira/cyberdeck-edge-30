# BEGIN EQS FISH: interactive terminals only; account/login shell remains Bash.
if [[ $- == *i* && -z ${BASH_EXECUTION_STRING-} && -t 0 && -t 1 ]] &&
   [[ -x /usr/bin/fish && "$(ps -p "$PPID" -o comm=)" != fish ]]; then
    if shopt -q login_shell; then
        exec /usr/bin/fish --login
    else
        exec /usr/bin/fish
    fi
fi
# END EQS FISH
