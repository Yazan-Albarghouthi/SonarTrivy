import ast
import hashlib
import operator
import os
import secrets
import string

_OPERATORS = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def generate_reset_token(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def is_admin(username: str, password: str) -> bool:
    expected_username = os.environ.get("ADMIN_USERNAME", "")
    expected_password = os.environ.get("ADMIN_PASSWORD", "")
    if not expected_username or not expected_password:
        return False
    username_match = secrets.compare_digest(username, expected_username)
    password_match = secrets.compare_digest(
        hash_password(password), hash_password(expected_password)
    )
    return username_match and password_match


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return -_eval_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return _eval_node(node.operand)
    raise ValueError("Unsupported expression: only +, -, *, / with numbers are allowed")


def safe_calculator(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)
