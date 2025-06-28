# BatPU2_Recomp
A simple static recompiler for the BatPU-2  

> [!NOTE]  
> The only program currently working is the [dvd program](https://github.com/mattbatwings/BatPU-2/blob/main/programs/dvd.mc).

# Structure
The project consists out of 2 parts.  
- The actual recompiler (`recompiler/`)  
- A collection of helper functions  (`helper_funcs/`)

The recompiler itself is made using Python and llvmlite (an llvm wrapper for Python).

The helper functions are made in Zig and raylib.

# Requirements
I don't know the _actual_ versions needed to run this program, but the following are the versions I used and _should_ work.  

- Python 3.12.3  
- llvmlite 0.44.0  
- Zig 0.14.0  
- raylib_zig 5.6.0 

# How to recompile a program

(do only once)  
1. Run the setup file for your operating system (`setup.ps1` for windows, `setup.sh` for GNU/Linux)  
What this does:
    - compiles the zig helper functions
    - creates a Python virtual environment
    - installs all Python dependencies

(for every program you want to recompile)  
1. place the .mc file you want to recompile into the `programs/` directory
2. run the recompile script for your operating system with the path to the program you want to recompile (eg. `./recompile.ps1 programs/dvd.mc`) 

If the recompilation succeeded, there will now be a `main.exe` or `main` file in the `dist/` directory.