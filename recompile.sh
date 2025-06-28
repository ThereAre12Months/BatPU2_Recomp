# recompile the program
source .venv/bin/activate
python3 recompiler/recomp.py $1 "build/main.ll"
deactivate

cd build/
zig cc "main.ll" "libhelper_funcs.a" "libraylib.a" -O3 -o "../dist/main"
cd ../