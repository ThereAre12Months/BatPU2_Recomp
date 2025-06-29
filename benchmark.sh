# recompile the program
source .venv/bin/activate
python3 recompiler/recomp.py "benchmark/fibonacci.mc" "build/main.ll" --headless
deactivate

cd build/
zig cc "main.ll" "libhelper_funcs.a" "libraylib.a" -Ofast -march=native -o "../dist/main"
cd ../

echo "Benchmarking Fibonacci..."
time ./dist/main