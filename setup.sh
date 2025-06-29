mkdir -p build/
mkdir -p dist/
mkdir -p programs/

# compile the helper functions + raylib
cd helper_funcs/
zig build -Doptimize=ReleaseFast -Dtarget=native --prefix-lib-dir "../../build/"
cd ../

# setup the virtual environment
python3 -m venv .venv

# install the python dependencies
source .venv/bin/activate
python3 -m pip install -r requirements.txt
deactivate