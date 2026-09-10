# PC Fish/Gentleman profile adapted for native Droidian, not Termux/Omarchy.
# Keep scripts, SSH commands and file transfers free of interactive side effects.
status is-interactive; or return

set -g fish_greeting ''
fish_add_path --path "$HOME/.local/bin" "$HOME/bin"
if command -q nvim
    set -gx EDITOR nvim
    set -gx VISUAL nvim
end

# Same vi navigation with Emacs shortcuts in insert mode as the PC.
function fish_user_key_bindings
    fish_default_key_bindings -M insert
    fish_vi_key_bindings --no-erase insert
end
fish_vi_key_bindings

if command -q starship
    starship init fish | source
end
if command -q zoxide
    zoxide init fish | source
end
if command -q fzf
    fzf --fish | source
end

alias ls 'ls --color=auto'
if command -q batcat
    alias bat batcat
end
if command -q fdfind
    alias fd fdfind
end

function fzfbat --description 'Find files with a syntax-highlighted preview'
    set -l viewer bat
    command -q batcat; and set viewer batcat
    command fzf --preview="$viewer --theme=gruvbox-dark --color=always -- {}" $argv
end

function fzfnvim --description 'Open a selected file in Neovim'
    # Preserve spaces/newlines; cancelling must not open an empty editor.
    set -l file (fzfbat --print0 | string split0)
    if test (count $file) -eq 1
        command nvim -- "$file"
    end
end

# Gentleman palette from the PC, independent of desktop/compositor settings.
set -g fish_color_normal F3F6F9
set -g fish_color_command 7AA89F
set -g fish_color_keyword FF8DD7
set -g fish_color_quote FFE066
set -g fish_color_redirection F3F6F9
set -g fish_color_end DEBA87
set -g fish_color_error CB7C94
set -g fish_color_param A3B5D6
set -g fish_color_comment 8394A3
set -g fish_color_selection --background=263356
set -g fish_color_search_match --background=263356
set -g fish_color_operator B7CC85
set -g fish_color_escape FF8DD7
set -g fish_color_autosuggestion 8394A3
set -g fish_pager_color_progress 8394A3
set -g fish_pager_color_prefix 7AA89F
set -g fish_pager_color_completion F3F6F9
set -g fish_pager_color_description 8394A3
