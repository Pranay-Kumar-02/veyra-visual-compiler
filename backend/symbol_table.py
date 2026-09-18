"""
Hierarchical Symbol Table for VCL with nested scope support.
Tracks symbol name, inferred type, current runtime value, scope level, and source location.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Symbol:
    name: str
    type_name: str
    value: Any = None
    scope_name: str = "global"
    scope_level: int = 0
    line: int = 1
    column: int = 1

    def to_dict(self) -> Dict[str, Any]:
        val_display = self.value
        if isinstance(self.value, bool):
            val_display = "true" if self.value else "false"
        elif self.value is None:
            val_display = "uninitialized"
        else:
            val_display = str(self.value)

        return {
            "name": self.name,
            "type": self.type_name,
            "value": val_display,
            "scope": self.scope_name,
            "scope_level": self.scope_level,
            "line": self.line,
            "column": self.column,
        }


class Scope:
    """Represents an individual lexical scope in the symbol table."""

    def __init__(self, name: str, level: int = 0, parent: Optional["Scope"] = None):
        self.name: str = name
        self.level: int = level
        self.parent: Optional["Scope"] = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, symbol: Symbol) -> None:
        symbol.scope_name = self.name
        symbol.scope_level = self.level
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str, current_only: bool = False) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if not current_only and self.parent is not None:
            return self.parent.lookup(name, current_only=False)
        return None

    def update(self, name: str, value: Any, type_name: Optional[str] = None) -> bool:
        if name in self.symbols:
            sym = self.symbols[name]
            sym.value = value
            if type_name:
                sym.type_name = type_name
            return True
        if self.parent is not None:
            return self.parent.update(name, value, type_name)
        return False


class SymbolTable:
    """
    Manages the stack of scopes and provides unified query and export operations.
    """

    def __init__(self):
        self.global_scope = Scope(name="global", level=0, parent=None)
        self.current_scope = self.global_scope
        self.all_scopes: List[Scope] = [self.global_scope]
        self._scope_counter: int = 0

    def enter_scope(self, prefix: str = "block") -> Scope:
        self._scope_counter += 1
        scope_name = f"{prefix}_{self._scope_counter}"
        new_scope = Scope(name=scope_name, level=self.current_scope.level + 1, parent=self.current_scope)
        self.current_scope = new_scope
        self.all_scopes.append(new_scope)
        return new_scope

    def exit_scope(self) -> None:
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent

    def define(self, symbol: Symbol) -> None:
        self.current_scope.define(symbol)

    def lookup(self, name: str, current_only: bool = False) -> Optional[Symbol]:
        return self.current_scope.lookup(name, current_only=current_only)

    def update(self, name: str, value: Any, type_name: Optional[str] = None) -> bool:
        return self.current_scope.update(name, value, type_name)

    def to_list(self) -> List[Dict[str, Any]]:
        """Exports all symbols across all scopes for visualization."""
        records: List[Dict[str, Any]] = []
        for sc in self.all_scopes:
            for sym in sc.symbols.values():
                records.append(sym.to_dict())
        return records

    def reset(self) -> None:
        self.global_scope = Scope(name="global", level=0, parent=None)
        self.current_scope = self.global_scope
        self.all_scopes = [self.global_scope]
        self._scope_counter = 0
