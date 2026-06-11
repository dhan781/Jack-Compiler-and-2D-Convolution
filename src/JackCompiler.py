#!/usr/bin/env python3

import sys
import os
from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine

def compile_file(jack_path: str):
    print(f"  Compiling {jack_path} …")
    tokenizer = JackTokenizer(jack_path)
    tokens    = tokenizer.tokenize()
    engine    = CompilationEngine(tokens, jack_path)
    engine.compile_class()
    print(f"    → {os.path.splitext(jack_path)[0]}T.xml")
    print(f"    → {os.path.splitext(jack_path)[0]}.xml")
    print(f"    → {os.path.splitext(jack_path)[0]}.vm")

def main():
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <file.jack | directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    if os.path.isdir(target):
        jack_files = [
            os.path.join(target, f)
            for f in os.listdir(target)
            if f.endswith(".jack")
        ]
        if not jack_files:
            print(f"No .jack files found in {target}")
            sys.exit(1)
        for jf in sorted(jack_files):
            compile_file(jf)
    elif os.path.isfile(target) and target.endswith(".jack"):
        compile_file(target)
    else:
        print(f"Invalid input: {target}")
        sys.exit(1)
        
    print("Done.")

if __name__ == "__main__":
    main()