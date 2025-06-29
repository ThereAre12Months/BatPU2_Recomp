./.venv/Scripts/activate.ps1
python recompiler/recomp.py "benchmark/fibonacci.mc" "build/main.ll" --headless
deactivate

Set-Location build/
zig cc "main.ll" "helper_funcs.lib" "raylib.lib" -lopengl32 -lwinmm -lgdi32 -luser32 -lkernel32 -Ofast -march=native -o "../dist/main.exe"
Set-Location ../

echo "Benchmarking Fibonacci..."
Measure-Command {./dist/main.exe}

./.venv/Scripts/activate.ps1
python recompiler/recomp.py "benchmark/fractal.mc" "build/main.ll"
deactivate

Set-Location build/
zig cc "main.ll" "helper_funcs.lib" "raylib.lib" -lopengl32 -lwinmm -lgdi32 -luser32 -lkernel32 -Ofast -march=native -o "../dist/main.exe"
Set-Location ../

echo "Benchmarking Sierpinski..."
Measure-Command {./dist/main.exe}