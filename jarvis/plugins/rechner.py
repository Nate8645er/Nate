"""Plugin: sicherer Taschenrechner (ohne eval-Sicherheitsrisiko)."""

import ast
import operator

from jarvis.plugins.base import JarvisPlugin

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node: ast.AST) -> float:
    """Wertet nur Zahlen und Grundrechenarten aus - sonst nichts."""
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("Nur Zahlen und Grundrechenarten (+ - * / ** % //) erlaubt.")


class RechnerPlugin(JarvisPlugin):
    name = "rechner"
    description = "Rechnet mathematische Ausdrücke aus"
    commands = {"rechne": "Ausdruck berechnen, z.B. /rechne 2 * (3 + 4)"}

    def execute(self, command: str, args: str) -> str:
        if not args.strip():
            return "Bitte einen Ausdruck angeben, z.B.: /rechne 2 * (3 + 4)"
        try:
            tree = ast.parse(args.strip(), mode="eval")
            result = _evaluate(tree)
        except ZeroDivisionError:
            return "Division durch Null ist nicht erlaubt."
        except (ValueError, SyntaxError):
            return "Das konnte ich nicht berechnen. Erlaubt sind Zahlen und + - * / ** % //."
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"{args.strip()} = {result}"
