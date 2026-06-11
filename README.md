# DA2304 Assignment 3: Jack Compiler & 2D Convolution

This is my submission for Assignment 3. It contains a two-part project: a 2D Convolution program written in Jack, and a custom Jack-to-VM compiler built from scratch in Python to translate it. 

## Folder Setup

I've organized the directory exactly as requested:
* **`jack/`**: Contains my raw source code (`Conv.jack` and `Main.jack`).
* **`src/`**: Contains all the Python compiler modules.
* **`out/`**: Where the generated XML and VM artefacts live after running the code.

## How to Run the Compiler

You just need Python 3 to run this.

1. Open your terminal and navigate into the `src` folder:

   cd src/

2. Run the master compiler script and point it at the `jack` folder:

   python3 JackCompiler.py ../jack/

Note: This automatically generates the token streams, parse trees, and VM code right next to the original source files. I just drag them into the out/ folder afterward


## The Convolution Details (`Main.jack`)

My Jack program runs a standard MAC convolution using a Laplacian edge-detector kernel .

If you run my generated `.vm` files through our Assignment 2 VM Translator and load the resulting `.asm` into the Hack CPU Emulator, it will run two distinct tests:
1. A 5x5 input matrix processed into a 3x3 output (Stride = 1).
2.  A 9x9 input matrix processed into a 4x4 output (Stride = 2).
