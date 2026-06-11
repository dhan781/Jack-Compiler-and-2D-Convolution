import os
from typing import List, Tuple, Optional
from SymbolTable import SymbolTable
from VMWriter import VMWriter

XML_ESCAPE = {"<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;"}

OP_MAP = {
    "+": VMWriter.ADD,
    "-": VMWriter.SUB,
    "&": VMWriter.AND,
    "|": VMWriter.OR,
    "<": VMWriter.LT,
    ">": VMWriter.GT,
    "=": VMWriter.EQ,
}

def _esc(v: str) -> str:
    for ch, e in XML_ESCAPE.items():
        v = v.replace(ch, e)
    return v

class CompilationEngine:
    def __init__(self, tokens: List[Tuple[str, str]], source_path: str):
        self._tokens = tokens
        self._pos    = 0
        self._indent = 0
        base = os.path.splitext(source_path)[0]
        self._xml_file = open(base + ".xml", "w")
        self._vm        = VMWriter(base + ".vm")
        self._symbols   = SymbolTable()
        self._class_name: str = ""

    def _peek(self) -> Optional[Tuple[str, str]]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self) -> Tuple[str, str]:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, type_or_val) -> Tuple[str, str]:
        tok = self._advance()
        if isinstance(type_or_val, str):
            if tok[0] != type_or_val and tok[1] != type_or_val:
                raise SyntaxError(
                    f"Expected '{type_or_val}', got {tok} at position {self._pos}"
                )
        return tok

    def _eat(self, value: str) -> Tuple[str, str]:
        tok = self._advance()
        if tok[1] != value:
            raise SyntaxError(
                f"Expected '{value}', got '{tok[1]}' at position {self._pos}"
            )
        return tok

    def _peek_val(self) -> Optional[str]:
        t = self._peek()
        return t[1] if t else None

    def _peek_type(self) -> Optional[str]:
        t = self._peek()
        return t[0] if t else None

    def _xml(self, tag: str, val: str):
        pad = "  " * self._indent
        self._xml_file.write(f"{pad}<{tag}> {_esc(val)} </{tag}>\n")

    def _open(self, tag: str):
        pad = "  " * self._indent
        self._xml_file.write(f"{pad}<{tag}>\n")
        self._indent += 1

    def _close(self, tag: str):
        self._indent -= 1
        pad = "  " * self._indent
        self._xml_file.write(f"{pad}</{tag}>\n")

    def _write_token(self):
        ttype, tval = self._advance()
        self._xml(ttype, tval)
        return ttype, tval

    def _write_keyword(self, kw: str):
        self._eat(kw)
        self._xml("keyword", kw)

    def _write_symbol(self, sym: str):
        self._eat(sym)
        self._xml("symbol", sym)

    def compile_class(self):
        self._open("class")
        self._write_keyword("class")
        _, cname = self._advance()
        self._class_name = cname
        self._xml("identifier", cname)
        self._write_symbol("{")
        while self._peek_val() in ("static", "field"):
            self._compile_class_var_dec()
        while self._peek_val() in ("constructor", "function", "method"):
            self._compile_subroutine_dec()
        self._write_symbol("}")
        self._close("class")
        self._xml_file.close()
        self._vm.close()

    def _compile_class_var_dec(self):
        self._open("classVarDec")
        _, kind_kw = self._advance()
        self._xml("keyword", kind_kw)
        kind = SymbolTable.STATIC if kind_kw == "static" else SymbolTable.FIELD
        var_type = self._compile_type()
        _, name = self._advance()
        self._xml("identifier", name)
        self._symbols.define(name, var_type, kind)
        while self._peek_val() == ",":
            self._write_symbol(",")
            _, name = self._advance()
            self._xml("identifier", name)
            self._symbols.define(name, var_type, kind)
        self._write_symbol(";")
        self._close("classVarDec")

    def _compile_type(self) -> str:
        ttype, tval = self._advance()
        if ttype == "keyword":
            self._xml("keyword", tval)
        else:
            self._xml("identifier", tval)
        return tval

    def _compile_subroutine_dec(self):
        self._open("subroutineDec")
        self._symbols.start_subroutine()
        _, sub_kind = self._advance()
        self._xml("keyword", sub_kind)
        ret_type = self._compile_type()
        _, sub_name = self._advance()
        self._xml("identifier", sub_name)
        full_name = f"{self._class_name}.{sub_name}"
        self._write_symbol("(")
        if sub_kind == "method":
            self._symbols.define("this", self._class_name, SymbolTable.ARG)
        self._compile_parameter_list()
        self._write_symbol(")")
        self._open("subroutineBody")
        self._write_symbol("{")
        while self._peek_val() == "var":
            self._compile_var_dec()
        n_locals = self._symbols.count(SymbolTable.VAR)
        self._vm.write_function(full_name, n_locals)
        if sub_kind == "constructor":
            n_fields = self._symbols.count(SymbolTable.FIELD)
            self._vm.write_push("constant", n_fields)
            self._vm.write_call("Memory.alloc", 1)
            self._vm.write_pop("pointer", 0)
        elif sub_kind == "method":
            self._vm.write_push("argument", 0)
            self._vm.write_pop("pointer", 0)
        self._compile_statements()
        self._write_symbol("}")
        self._close("subroutineBody")
        self._close("subroutineDec")

    def _compile_parameter_list(self):
        self._open("parameterList")
        if self._peek_val() != ")":
            var_type = self._compile_type()
            _, name = self._advance()
            self._xml("identifier", name)
            self._symbols.define(name, var_type, SymbolTable.ARG)
            while self._peek_val() == ",":
                self._write_symbol(",")
                var_type = self._compile_type()
                _, name = self._advance()
                self._xml("identifier", name)
                self._symbols.define(name, var_type, SymbolTable.ARG)
        self._close("parameterList")

    def _compile_var_dec(self):
        self._open("varDec")
        self._write_keyword("var")
        var_type = self._compile_type()
        _, name = self._advance()
        self._xml("identifier", name)
        self._symbols.define(name, var_type, SymbolTable.VAR)
        while self._peek_val() == ",":
            self._write_symbol(",")
            _, name = self._advance()
            self._xml("identifier", name)
            self._symbols.define(name, var_type, SymbolTable.VAR)
        self._write_symbol(";")
        self._close("varDec")

    def _compile_statements(self):
        self._open("statements")
        stmt_kws = {"let", "if", "while", "do", "return"}
        while self._peek_val() in stmt_kws:
            kw = self._peek_val()
            if kw == "let":
                self._compile_let()
            elif kw == "if":
                self._compile_if()
            elif kw == "while":
                self._compile_while()
            elif kw == "do":
                self._compile_do()
            elif kw == "return":
                self._compile_return()
        self._close("statements")

    def _compile_let(self):
        self._open("letStatement")
        self._write_keyword("let")
        _, var_name = self._advance()
        self._xml("identifier", var_name)
        is_array = self._peek_val() == "["
        if is_array:
            self._push_variable(var_name)
            self._write_symbol("[")
            self._compile_expression()
            self._write_symbol("]")
            self._vm.write_arithmetic(VMWriter.ADD)
        self._write_symbol("=")
        self._compile_expression()
        self._write_symbol(";")
        if is_array:
            self._vm.write_pop("temp", 0)
            self._vm.write_pop("pointer", 1)
            self._vm.write_push("temp", 0)
            self._vm.write_pop("that", 0)
        else:
            self._pop_variable(var_name)
        self._close("letStatement")

    def _compile_if(self):
        self._open("ifStatement")
        self._write_keyword("if")
        self._write_symbol("(")
        self._compile_expression()
        self._write_symbol(")")
        label_false = self._vm.new_label("IF_FALSE")
        label_end   = self._vm.new_label("IF_END")
        self._vm.write_arithmetic(VMWriter.NOT)
        self._vm.write_if_goto(label_false)
        self._write_symbol("{")
        self._compile_statements()
        self._write_symbol("}")
        if self._peek_val() == "else":
            self._vm.write_goto(label_end)
            self._vm.write_label(label_false)
            self._write_keyword("else")
            self._write_symbol("{")
            self._compile_statements()
            self._write_symbol("}")
            self._vm.write_label(label_end)
        else:
            self._vm.write_label(label_false)
        self._close("ifStatement")

    def _compile_while(self):
        self._open("whileStatement")
        label_start = self._vm.new_label("WHILE_START")
        label_end   = self._vm.new_label("WHILE_END")
        self._vm.write_label(label_start)
        self._write_keyword("while")
        self._write_symbol("(")
        self._compile_expression()
        self._write_symbol(")")
        self._vm.write_arithmetic(VMWriter.NOT)
        self._vm.write_if_goto(label_end)
        self._write_symbol("{")
        self._compile_statements()
        self._write_symbol("}")
        self._vm.write_goto(label_start)
        self._vm.write_label(label_end)
        self._close("whileStatement")

    def _compile_do(self):
        self._open("doStatement")
        self._write_keyword("do")
        _, name = self._advance()
        self._xml("identifier", name)
        self._compile_subroutine_call(name)
        self._write_symbol(";")
        self._vm.write_pop("temp", 0)
        self._close("doStatement")

    def _compile_return(self):
        self._open("returnStatement")
        self._write_keyword("return")
        if self._peek_val() != ";":
            self._compile_expression()
        else:
            self._vm.write_push("constant", 0)
        self._write_symbol(";")
        self._vm.write_return()
        self._close("returnStatement")

    BINARY_OPS = set("+-*/&|<>=")

    def _compile_expression(self):
        self._open("expression")
        self._compile_term()
        while self._peek_val() in self.BINARY_OPS:
            _, op = self._advance()
            self._xml("symbol", op)
            self._compile_term()
            if op == "*":
                self._vm.write_call("Math.multiply", 2)
            elif op == "/":
                self._vm.write_call("Math.divide", 2)
            else:
                self._vm.write_arithmetic(OP_MAP[op])
        self._close("expression")

    def _compile_term(self):
        self._open("term")
        ttype, tval = self._peek()
        if ttype == "integerConstant":
            self._advance()
            self._xml("integerConstant", tval)
            self._vm.write_push("constant", int(tval))
        elif ttype == "stringConstant":
            self._advance()
            self._xml("stringConstant", tval)
            self._vm.write_push("constant", len(tval))
            self._vm.write_call("String.new", 1)
            for ch in tval:
                self._vm.write_push("constant", ord(ch))
                self._vm.write_call("String.appendChar", 2)
        elif ttype == "keyword" and tval in ("true", "false", "null", "this"):
            self._advance()
            self._xml("keyword", tval)
            if tval == "true":
                self._vm.write_push("constant", 0)
                self._vm.write_arithmetic(VMWriter.NOT)
            elif tval in ("false", "null"):
                self._vm.write_push("constant", 0)
            else:
                self._vm.write_push("pointer", 0)
        elif tval == "(":
            self._write_symbol("(")
            self._compile_expression()
            self._write_symbol(")")
        elif tval in ("-", "~"):
            self._advance()
            self._xml("symbol", tval)
            self._compile_term()
            if tval == "-":
                self._vm.write_arithmetic(VMWriter.NEG)
            else:
                self._vm.write_arithmetic(VMWriter.NOT)
        elif ttype == "identifier":
            self._advance()
            self._xml("identifier", tval)
            next_val = self._peek_val()
            if next_val == "[":
                self._push_variable(tval)
                self._write_symbol("[")
                self._compile_expression()
                self._write_symbol("]")
                self._vm.write_arithmetic(VMWriter.ADD)
                self._vm.write_pop("pointer", 1)
                self._vm.write_push("that", 0)
            elif next_val in (".", "("):
                self._compile_subroutine_call(tval)
            else:
                self._push_variable(tval)
        self._close("term")

    def _compile_subroutine_call(self, name: str):
        n_args = 0
        if self._peek_val() == ".":
            self._write_symbol(".")
            _, method_name = self._advance()
            self._xml("identifier", method_name)
            kind = self._symbols.kind_of(name)
            if kind is not None:
                self._push_variable(name)
                n_args += 1
                class_type = self._symbols.type_of(name)
                full_name  = f"{class_type}.{method_name}"
            else:
                full_name = f"{name}.{method_name}"
        else:
            self._vm.write_push("pointer", 0)
            n_args += 1
            full_name = f"{self._class_name}.{name}"
        self._write_symbol("(")
        n_args += self._compile_expression_list()
        self._write_symbol(")")
        self._vm.write_call(full_name, n_args)

    def _compile_expression_list(self) -> int:
        self._open("expressionList")
        count = 0
        if self._peek_val() != ")":
            self._compile_expression()
            count += 1
            while self._peek_val() == ",":
                self._write_symbol(",")
                self._compile_expression()
                count += 1
        self._close("expressionList")
        return count

    def _push_variable(self, name: str):
        kind  = self._symbols.kind_of(name)
        index = self._symbols.index_of(name)
        if kind == SymbolTable.FIELD:
            self._vm.write_push("this", index)
        elif kind is not None:
            self._vm.write_push(kind, index)
        else:
            raise NameError(f"Undefined variable: {name}")

    def _pop_variable(self, name: str):
        kind  = self._symbols.kind_of(name)
        index = self._symbols.index_of(name)
        if kind == SymbolTable.FIELD:
            self._vm.write_pop("this", index)
        elif kind is not None:
            self._vm.write_pop(kind, index)
        else:
            raise NameError(f"Undefined variable: {name}")