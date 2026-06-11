import os

class VMWriter:
    ADD  = "add"
    SUB  = "sub"
    NEG  = "neg"
    EQ   = "eq"
    GT   = "gt"
    LT   = "lt"
    AND  = "and"
    OR   = "or"
    NOT  = "not"

    def __init__(self, output_path: str):
        self._out = open(output_path, "w")
        self._label_count = 0

    def write_push(self, segment: str, index: int):
        self._out.write(f"push {segment} {index}\n")

    def write_pop(self, segment: str, index: int):
        self._out.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command: str):
        self._out.write(f"{command}\n")

    def new_label(self, prefix: str = "L") -> str:
        lbl = f"{prefix}_{self._label_count}"
        self._label_count += 1
        return lbl

    def write_label(self, label: str):
        self._out.write(f"label {label}\n")

    def write_goto(self, label: str):
        self._out.write(f"goto {label}\n")

    def write_if_goto(self, label: str):
        self._out.write(f"if-goto {label}\n")

    def write_function(self, name: str, n_locals: int):
        self._out.write(f"function {name} {n_locals}\n")

    def write_call(self, name: str, n_args: int):
        self._out.write(f"call {name} {n_args}\n")

    def write_return(self):
        self._out.write("return\n")

    def close(self):
        self._out.close()