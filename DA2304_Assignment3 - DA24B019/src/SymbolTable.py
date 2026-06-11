class SymbolTable:
    STATIC = "static"
    FIELD  = "field"
    ARG    = "argument"
    VAR    = "local"

    def __init__(self):
        self._class_scope      = {}
        self._subroutine_scope = {}
        self._counts = {self.STATIC: 0, self.FIELD: 0,
                        self.ARG: 0,    self.VAR: 0}

    def start_subroutine(self):
        self._subroutine_scope = {}
        self._counts[self.ARG] = 0
        self._counts[self.VAR] = 0

    def define(self, name: str, type_: str, kind: str):
        idx = self._counts[kind]
        self._counts[kind] += 1
        entry = (type_, kind, idx)
        if kind in (self.STATIC, self.FIELD):
            self._class_scope[name] = entry
        else:
            self._subroutine_scope[name] = entry

    def _lookup(self, name: str):
        if name in self._subroutine_scope:
            return self._subroutine_scope[name]
        if name in self._class_scope:
            return self._class_scope[name]
        return None

    def type_of(self, name: str) -> str:
        e = self._lookup(name)
        return e[0] if e else None

    def kind_of(self, name: str) -> str:
        e = self._lookup(name)
        return e[1] if e else None

    def index_of(self, name: str) -> int:
        e = self._lookup(name)
        return e[2] if e else None

    def count(self, kind: str) -> int:
        return self._counts[kind]

    def dump(self) -> str:
        lines = ["=== CLASS SCOPE ==="]
        for name, (t, k, i) in sorted(self._class_scope.items()):
            lines.append(f"  {name:20s}  type={t:12s}  kind={k:8s}  index={i}")
        lines.append("=== SUBROUTINE SCOPE ===")
        for name, (t, k, i) in sorted(self._subroutine_scope.items()):
            lines.append(f"  {name:20s}  type={t:12s}  kind={k:8s}  index={i}")
        return "\n".join(lines)