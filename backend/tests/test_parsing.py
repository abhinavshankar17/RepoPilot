import pytest
from app.services.parser_service import ParserService
from app.parsers.python_parser import PythonASTParser
from app.parsers.js_ts_parser import JSTSParser
from app.parsers.fallback_parser import FallbackParser


def test_python_ast_parsing():
    sample_code = '''import os
from datetime import datetime

@app.get("/users/{user_id}")
def get_user(user_id: int):
    """Retrieve user details."""
    return {"user_id": user_id}

class UserController:
    def __init__(self, db):
        self.db = db

    def create_user(self, name: str, email: str):
        return self.db.save(name, email)
'''

    service = ParserService()
    symbols = service.parse_file("repo-123", "app/controllers.py", sample_code, "Python")

    assert len(symbols) >= 4

    # Verify imports
    import_names = [s.symbol_name for s in symbols if s.symbol_type == "import"]
    assert "os" in import_names
    assert "datetime.datetime" in import_names

    # Verify class
    classes = [s for s in symbols if s.symbol_type == "class"]
    assert len(classes) == 1
    assert classes[0].symbol_name == "UserController"
    assert classes[0].start_line == 9

    # Verify function & API route
    funcs = [s for s in symbols if s.symbol_name == "get_user"]
    assert len(funcs) == 1
    assert funcs[0].symbol_type == "function"
    assert funcs[0].parameters == ["user_id"]
    assert len(funcs[0].decorators) == 1
    assert any("@app.get" in dec for dec in funcs[0].decorators)

    # Verify method & parent relationship
    methods = [s for s in symbols if s.symbol_name == "create_user"]
    assert len(methods) == 1
    assert methods[0].symbol_type == "method"
    assert methods[0].parent_symbol == "UserController"
    assert methods[0].parameters == ["name", "email"]


def test_js_ts_ast_parsing():
    sample_code = '''import { AuthService } from './auth';

class UserController {
    constructor(authService) {
        this.auth = authService;
    }

    async createUser(req, res) {
        const user = await this.auth.register(req.body);
        return res.json(user);
    }
}

export const authenticateUser = (req, res, next) => {
    // Middleware logic
    next();
};
'''

    service = ParserService()
    symbols = service.parse_file("repo-123", "src/middleware/auth.js", sample_code, "JavaScript")

    assert len(symbols) >= 3

    # Verify class
    classes = [s for s in symbols if s.symbol_type == "class"]
    assert len(classes) == 1
    assert classes[0].symbol_name == "UserController"

    # Verify method & parent relationship
    methods = [s for s in symbols if s.symbol_name == "createUser"]
    assert len(methods) == 1
    assert methods[0].symbol_type == "method"
    assert methods[0].parent_symbol == "UserController"
    assert methods[0].parameters == ["req", "res"]

    # Verify exported arrow function
    funcs = [s for s in symbols if s.symbol_name == "authenticateUser"]
    assert len(funcs) == 1
    assert funcs[0].symbol_type == "function"
    assert funcs[0].parameters == ["req", "res", "next"]


def test_parsing_graceful_fallback():
    # Invalid python code (syntax error)
    invalid_code = '''def broken_function(:
    print("missing closing paren"
'''

    service = ParserService()
    symbols = service.parse_file("repo-123", "broken.py", invalid_code, "Python")

    # Should fall back to plain text block symbols without crashing
    assert len(symbols) > 0
    assert symbols[0].symbol_type == "block"
    assert symbols[0].start_line == 1


def test_line_number_accuracy():
    sample_code = '''line 1
line 2
line 3
line 4
line 5
'''

    fallback = FallbackParser()
    symbols = fallback.parse("repo-123", "plain.txt", sample_code, "Plain Text")

    assert len(symbols) == 1
    assert symbols[0].start_line == 1
    assert symbols[0].end_line == 5
