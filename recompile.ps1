# recompile the program
./.venv/Scripts/activate.ps1
python recompiler/recomp.py $args[0] "build/main.ll"
deactivate

# link the program with the helper functions and raylib
Set-Location build/
zig cc "main.ll" "helper_funcs.lib" "raylib.lib" -lopengl32 -lwinmm -lgdi32 -luser32 -lkernel32 -O3 -o "../dist/main.exe"
Set-Location ../