# new_project

`project.py` scaffolds a template Python project so you can start working straight away.

## Usage

```bash
python3 /path/to/dsutils/src/dsutils/new_project/project.py
```

## Setting up a shortcut

Adding an alias means you can just type `new-project` from anywhere.

### macOS / Linux

Add the following to `~/.zshrc` (zsh) or `~/.bashrc` (bash):

```bash
alias new-project="python3 /Users/julesstremersch/GitHub/dsutils/src/dsutils/new_project/project.py"
```

Then reload your shell:

```bash
source ~/.zshrc   # or ~/.bashrc
```

### Windows (PowerShell)

PowerShell aliases cannot take arguments, so use a function instead. Open your profile:

```powershell
notepad $PROFILE
```

If the file does not exist yet, create it first:

```powershell
New-Item -ItemType File -Path $PROFILE -Force
```

Add the following, adjusting the path to match your machine:

```powershell
function new-project { python "$HOME\GitHub\dsutils\src\dsutils\new_project\project.py" @args }
```

Then reload your profile:

```powershell
. $PROFILE
```

> **Note:** if you see an error about scripts being disabled, run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

### Windows (Command Prompt)

Create a `new-project.bat` file somewhere on your `PATH` containing:

```bat
@echo off
python "%USERPROFILE%\GitHub\dsutils\src\dsutils\new_project\project.py" %*
```

## Running via uv

If you manage `dsutils` with uv, you can point the shortcut at uv instead so the
correct environment is always used:

```bash
alias new-project="uv run --project /path/to/dsutils python -m dsutils.new_project.project"
```