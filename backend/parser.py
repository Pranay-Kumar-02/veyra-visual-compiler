"""
Recursive-descent Parser for VCL (Visual Compiler Language).
Constructs a typed AST from the token stream while enforcing operator precedence
and capturing syntax errors with exact line and column numbers.
"""

from typing import List, Optional
from backend.tokens import Token, TokenType
from backend.errors import SyntaxError
from backend.ast_nodes import (
    ASTNode,
    Program,
    VarDeclaration,
    Assignment,
    PrintStatement,
    IfStatement,
    BlockStatement,
    BinaryExpression,
    UnaryExpression,
    Literal,
    Identifier,
)


class Parser:
    """
    Hand-written recursive-descent parser for VCL.
    Implements standard arithmetic precedence, statement parsing, and syntax diagnostics.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens: List[Token] = tokens
        self.current: int = 0

    def parse(self) -> Program:
        """Parses the full token stream into a Program AST node."""
        statements: List[ASTNode] = []
        first_line = self._peek().line if self.tokens else 1
        first_col = self._peek().column if self.tokens else 1

        while not self._is_at_end():
            stmt = self._statement()
            if stmt is not None:
                statements.append(stmt)

        return Program(statements, line=first_line, column=first_col)

    # -------------------------------------------------------------------------
    # Helper & Navigation Methods
    # -------------------------------------------------------------------------

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, error_message: str, hint: Optional[str] = None) -> Token:
        if self._check(token_type):
            return self._advance()
        token = self._peek()
        raise SyntaxError(
            message=error_message,
            line=token.line,
            column=token.column,
            hint=hint,
        )

    # -------------------------------------------------------------------------
    # Statement Parsing
    # -------------------------------------------------------------------------

    def _statement(self) -> ASTNode:
        if self._match(TokenType.LET):
            return self._var_declaration()
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.LBRACE):
            return self._block_statement()
        if self._check(TokenType.IDENTIFIER):
            # Check if this is an assignment statement: IDENTIFIER '='
            if self.current + 1 < len(self.tokens) and self.tokens[self.current + 1].type == TokenType.ASSIGN:
                return self._assignment_statement()

        # Fallback / unexpected statement start
        token = self._peek()
        raise SyntaxError(
            message=f"Unexpected token '{token.lexeme}' at start of statement.",
            line=token.line,
            column=token.column,
            hint="Statements must begin with 'let', an identifier assignment, 'print', 'if', or '{'.",
        )

    def _var_declaration(self) -> ASTNode:
        let_token = self._previous()
        id_token = self._consume(
            TokenType.IDENTIFIER,
            "Expected variable name after 'let'.",
            hint="Syntax: let <variable_name> = <expression>;",
        )
        self._consume(
            TokenType.ASSIGN,
            f"Expected '=' after variable name '{id_token.lexeme}'.",
            hint="Variable declarations must be initialized.",
        )
        initializer = self._expression()
        self._consume(
            TokenType.SEMICOLON,
            f"Expected ';' after declaration of '{id_token.lexeme}'.",
            hint="VCL requires semicolons at the end of declarations.",
        )
        return VarDeclaration(
            name=id_token.lexeme,
            initializer=initializer,
            line=let_token.line,
            column=let_token.column,
        )

    def _assignment_statement(self) -> ASTNode:
        id_token = self._advance()  # Consume IDENTIFIER
        assign_token = self._advance()  # Consume '='
        value = self._expression()
        self._consume(
            TokenType.SEMICOLON,
            f"Expected ';' after assignment to '{id_token.lexeme}'.",
            hint="VCL requires semicolons at the end of assignments.",
        )
        return Assignment(
            target=id_token.lexeme,
            value=value,
            line=id_token.line,
            column=id_token.column,
        )

    def _print_statement(self) -> ASTNode:
        print_token = self._previous()
        self._consume(
            TokenType.LPAREN,
            "Expected '(' after 'print'.",
            hint="Syntax: print(<expression>);",
        )
        expr = self._expression()
        self._consume(
            TokenType.RPAREN,
            "Expected ')' after print expression.",
            hint="Close the parenthesis after the expression.",
        )
        self._consume(
            TokenType.SEMICOLON,
            "Expected ';' after print statement.",
            hint="VCL requires semicolons at the end of print statements.",
        )
        return PrintStatement(
            expression=expr,
            line=print_token.line,
            column=print_token.column,
        )

    def _if_statement(self) -> ASTNode:
        if_token = self._previous()
        self._consume(
            TokenType.LPAREN,
            "Expected '(' after 'if'.",
            hint="Condition in if statement must be parenthesized: if (<condition>) { ... }",
        )
        condition = self._expression()
        self._consume(
            TokenType.RPAREN,
            "Expected ')' after if condition.",
        )

        then_branch = self._statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()

        return IfStatement(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
            line=if_token.line,
            column=if_token.column,
        )

    def _block_statement(self) -> ASTNode:
        brace_token = self._previous()
        statements: List[ASTNode] = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmt = self._statement()
            statements.append(stmt)
        self._consume(
            TokenType.RBRACE,
            "Expected '}' at the end of block.",
            hint="Ensure every opening '{' has a matching '}'.",
        )
        return BlockStatement(
            statements=statements,
            line=brace_token.line,
            column=brace_token.column,
        )

    # -------------------------------------------------------------------------
    # Expression Parsing with Operator Precedence
    # -------------------------------------------------------------------------

    def _expression(self) -> ASTNode:
        return self._logical_or()

    def _logical_or(self) -> ASTNode:
        expr = self._logical_and()
        while self._match(TokenType.OR_OR):
            op_token = self._previous()
            right = self._logical_and()
            expr = BinaryExpression(
                left=expr,
                operator=op_token.lexeme,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )
        return expr

    def _logical_and(self) -> ASTNode:
        expr = self._equality()
        while self._match(TokenType.AND_AND):
            op_token = self._previous()
            right = self._equality()
            expr = BinaryExpression(
                left=expr,
                operator=op_token.lexeme,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )
        return expr

    def _equality(self) -> ASTNode:
        expr = self._relational()
        while self._match(TokenType.EQ_EQ, TokenType.BANG_EQ):
            op_token = self._previous()
            right = self._relational()
            expr = BinaryExpression(
                left=expr,
                operator=op_token.lexeme,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )
        return expr

    def _relational(self) -> ASTNode:
        expr = self._additive()
        while self._match(TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ):
            op_token = self._previous()
            right = self._additive()
            expr = BinaryExpression(
                left=expr,
                operator=op_token.lexeme,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )
        return expr

    def _additive(self) -> ASTNode:
        expr = self._multiplicative()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op_token = self._previous()
            right = self._multiplicative()
            expr = BinaryExpression(
                left=expr,
                operator=op_token.lexeme,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )
        return expr

    def _multiplicative(self) -> ASTNode:
        expr = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_token = self._previous()
            right = self._unary()
            expr = BinaryExpression(
                left=expr,
                operator=op_token.lexeme,
                right=right,
                line=op_token.line,
                column=op_token.column,
            )
        return expr

    def _unary(self) -> ASTNode:
        if self._match(TokenType.BANG, TokenType.MINUS):
            op_token = self._previous()
            operand = self._unary()
            return UnaryExpression(
                operator=op_token.lexeme,
                operand=operand,
                line=op_token.line,
                column=op_token.column,
            )
        return self._primary()

    def _primary(self) -> ASTNode:
        # Integer literal
        if self._match(TokenType.INTEGER):
            tok = self._previous()
            return Literal(value=tok.literal, raw_type="int", line=tok.line, column=tok.column)

        # Float literal
        if self._match(TokenType.FLOAT):
            tok = self._previous()
            return Literal(value=tok.literal, raw_type="float", line=tok.line, column=tok.column)

        # Boolean literal
        if self._match(TokenType.BOOLEAN):
            tok = self._previous()
            return Literal(value=tok.literal, raw_type="bool", line=tok.line, column=tok.column)

        # Identifier
        if self._match(TokenType.IDENTIFIER):
            tok = self._previous()
            return Identifier(name=tok.lexeme, line=tok.line, column=tok.column)

        # Grouped expression: ( expr )
        if self._match(TokenType.LPAREN):
            paren_token = self._previous()
            expr = self._expression()
            self._consume(
                TokenType.RPAREN,
                "Expected ')' after expression.",
                hint="Make sure every '(' has a corresponding closing ')'.",
            )
            return expr

        # Error: Unexpected token in expression
        tok = self._peek()
        raise SyntaxError(
            message=f"Unexpected token '{tok.lexeme}' in expression.",
            line=tok.line,
            column=tok.column,
            hint="Expected a literal, variable name, or '(' expression.",
        )
