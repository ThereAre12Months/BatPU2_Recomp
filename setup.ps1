New-Item -ItemType Directory -Path "build"     -Force | Out-Null
New-Item -ItemType Directory -Path "dist"      -Force | Out-Null
New-Item -ItemType Directory -Path "programs"  -Force | Out-Null


# compile the helper functions + raylib
Set-Location helper_funcs/
zig build -Doptimize=ReleaseFast -Dtarget=native --prefix-lib-dir "../../build/"
Set-Location ../

# setup the virtual environment
python -m venv .venv

# install the python dependencies
.\.venv\Scripts\activate.ps1
python -m pip install -r requirements.txt
deactivate