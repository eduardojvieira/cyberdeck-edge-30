# Loaded from conf.d before config.fish restores ~/.local/bin precedence.
status is-interactive; or return
if test -x /home/linuxbrew/.linuxbrew/bin/brew
    /home/linuxbrew/.linuxbrew/bin/brew shellenv fish | source
end
