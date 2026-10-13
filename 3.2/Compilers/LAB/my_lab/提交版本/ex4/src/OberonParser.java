import java.io.*;
import flowchart.*;
import exceptions.*;

/**
 * OberonParser —— Oberon-0 递归下降 LL(1) 语法分析器.
 *
 * 每个非终结符对应一个解析方法，向前看符号驱动分支选择。
 * 语法分析期间使用 flowchart.* API 构建流程图模型：
 *   - Module.add(procName) → Procedure
 *   - Procedure.add(stmt) / IfStatement / WhileStatement / PrimitiveStatement
 *   - module.show() 最终展示可视化流程图.
 *
 * Inherited attributes: method parameters.
 * Synthesized attributes: method return values.
 */
public class OberonParser {

    /* ---- 词法扫描器 ---- */
    private OberonScanner scanner;
    private Token lookahead;

    /* ---- 流程图模型 ---- */
    private flowchart.Module module;
    private String moduleName;

    /* ---- 构造器 ---- */
    /**
     * 构造递归下降分析器.
     *
     * @param in Oberon-0 源文件的 Reader 输入流
     * @throws Exception 词法分析器初始化或首次 Token 读取时的 I/O 异常
     */
    public OberonParser(Reader in) throws Exception {
        this.scanner = new OberonScanner(in);
        advance();
    }

    /* ================================================================
     * 词法工具方法
     * ================================================================ */

    /** 读取下一个 Token */
    private void advance() throws Exception {
        lookahead = scanner.yylex();
        if (lookahead == null) {
            lookahead = new Token(Token.EOF, 0, 0);
        }
    }

    /** 匹配当前 Token 类型，成功后前进；否则抛异常 */
    private void match(int expectedType) throws Exception {
        if (lookahead.type == expectedType) {
            // System.out.println("  MATCH " + Token.typeName(expectedType)
            //     + " [" + lookahead.value + "]");
            advance();
        } else {
            throw new MismatchedCommentException(   // 复用作语法异常
                "语法错误: 期望 " + Token.typeName(expectedType)
                + "，实际 " + Token.typeName(lookahead.type)
                + " (" + lookahead + ")",
                lookahead.line, lookahead.column);
        }
    }

    /** 检查当前 Token 是否为指定类型 */
    private boolean check(int type) {
        return lookahead.type == type;
    }

    // ================================================================
    // 解析入口
    // ================================================================

    /**
     * parseModule —— 解析整个模块，返回初始化好的 flowchart.Module.
     * Module = MODULE ident ";" DeclarationSequence
     *          [BEGIN StatementSequence] END ident "." .
     */
    public flowchart.Module parseModule() throws Exception {
        // MODULE ident ";"
        match(Token.MODULE);
        Token id = lookahead;
        match(Token.IDENT);
        moduleName = (String) id.value;
        module = new flowchart.Module(moduleName);
        match(Token.SEMI);

        // DeclarationSequence
        parseDeclarationSequence();

        // [BEGIN StatementSequence]
        if (check(Token.BEGIN)) {
            match(Token.BEGIN);
            // 主程序体的语句序列: 放入一个虚拟 Procedure "main"
            Procedure mainProc = module.add(moduleName + "$body");
            parseStatementSequence(mainProc);
        }

        // END ident "."
        match(Token.END);
        match(Token.IDENT);
        match(Token.DOT);

        System.out.println("[语法分析] 模块 '" + moduleName + "' 递归下降分析完成。");
        return module;
    }

    // ================================================================
    // DeclarationSequence
    // ================================================================

    /**
     * DeclarationSequence = { CONST {ConstDecl ";"} | TYPE {TypeDecl ";"}
     *                       | VAR {VarDecl ";"} }
     *                       {ProcedureDecl ";"} .
     *
     * LL(1): 根据 lookahead 决定哪种声明段。
     */
    private void parseDeclarationSequence() throws Exception {
        while (true) {
            if (check(Token.CONST)) {
                parseConstDeclarations();
            } else if (check(Token.TYPE)) {
                parseTypeDeclarations();
            } else if (check(Token.VAR)) {
                parseVarDeclarations();
            } else if (check(Token.PROCEDURE)) {
                parseProcedureDeclaration();
                // 过程声明间以 ";" 分隔
                if (check(Token.SEMI)) {
                    match(Token.SEMI);
                }
            } else {
                break;  // 声明序列结束
            }
        }
    }

    /* ---- CONST 声明段 ---- */
    private void parseConstDeclarations() throws Exception {
        match(Token.CONST);
        do {
            match(Token.IDENT);              // ident
            match(Token.EQ);                 // "="
            parseExpression();               // ConstExpression
            match(Token.SEMI);               // ";"
        } while (check(Token.IDENT));
    }

    /* ---- TYPE 声明段 ---- */
    private void parseTypeDeclarations() throws Exception {
        match(Token.TYPE);
        do {
            match(Token.IDENT);
            match(Token.EQ);
            parseType();
            match(Token.SEMI);
        } while (check(Token.IDENT));
    }

    /* ---- VAR 声明段 ---- */
    private void parseVarDeclarations() throws Exception {
        match(Token.VAR);
        do {
            parseIdentList();                // ident {"," ident}
            match(Token.COLON);
            parseType();
            match(Token.SEMI);
        } while (check(Token.IDENT));
    }

    /** Type = qualident | ARRAY ConstExpr OF Type | RECORD FieldList END */
    private void parseType() throws Exception {
        if (check(Token.ARRAY)) {
            match(Token.ARRAY);
            parseExpression();               // 数组长度
            match(Token.OF);
            parseType();
        } else if (check(Token.RECORD)) {
            match(Token.RECORD);
            while (check(Token.IDENT)) {
                parseIdentList();
                match(Token.COLON);
                parseType();
                // 分号仅在后续仍有字段时消费 (末字段后为 END)
                if (check(Token.SEMI)) {
                    match(Token.SEMI);
                }
            }
            match(Token.END);
        } else {
            // qualident (INTEGER / BOOLEAN / 自定义类型)
            match(lookahead.type);
        }
    }

    /* ---- 过程声明 ---- */
    private void parseProcedureDeclaration() throws Exception {
        match(Token.PROCEDURE);
        Token id = lookahead;
        match(Token.IDENT);
        String procName = (String) id.value;

        // 创建 flowchart Procedure
        Procedure proc = module.add(procName);

        // FormalParameters (可选)
        if (check(Token.LPAREN)) {
            match(Token.LPAREN);
            if (!check(Token.RPAREN)) {
                parseFPSection();
                while (check(Token.SEMI)) {
                    match(Token.SEMI);
                    parseFPSection();
                }
            }
            match(Token.RPAREN);
        }

        match(Token.SEMI);

        // 局部声明 + 过程体
        parseDeclarationSequence();
        if (check(Token.BEGIN)) {
            match(Token.BEGIN);
            parseStatementSequence(proc);
        }

        match(Token.END);
        match(Token.IDENT);
        // 注: 过程中声明使用 ";", 最后一个后的分号在 DeclarationSequence 外层处理
    }

    private void parseFPSection() throws Exception {
        boolean isVar = false;
        if (check(Token.VAR)) {
            match(Token.VAR);
            isVar = true;
        }
        parseIdentList();
        match(Token.COLON);
        parseType();
    }

    // ================================================================
    // StatementSequence (含有流程图节点构造)
    // ================================================================

    /**
     * StatementSequence = Statement {";" Statement}.
     * 将解析出的语句逐个添加到 Procedure 中.
     */
    private void parseStatementSequence(StatementSequence target) throws Exception {
        AbstractStatement stmt = parseStatement();
        if (stmt != null) {
            target.add(stmt);
        }
        while (check(Token.SEMI)) {
            match(Token.SEMI);
            stmt = parseStatement();
            if (stmt != null) {
                target.add(stmt);
            }
        }
    }

    /** 重载: 添加到 Procedure (主过程体) */
    private void parseStatementSequence(Procedure proc) throws Exception {
        AbstractStatement stmt = parseStatement();
        if (stmt != null) {
            proc.add(stmt);
        }
        while (check(Token.SEMI)) {
            match(Token.SEMI);
            stmt = parseStatement();
            if (stmt != null) {
                proc.add(stmt);
            }
        }
    }

    /**
     * Statement = [ Assignment | ProcCall | IfStatement
     *               | WhileStatement | Read | Write | WriteLn ] .
     */
    private AbstractStatement parseStatement() throws Exception {
        if (check(Token.IF)) {
            return parseIfStatement();
        } else if (check(Token.WHILE)) {
            return parseWhileStatement();
        } else if (check(Token.READ)) {
            match(Token.READ);
            match(Token.LPAREN);
            String expr = parseExpression();
            match(Token.RPAREN);
            return new PrimitiveStatement("Read(" + expr + ")");
        } else if (check(Token.WRITE)) {
            match(Token.WRITE);
            match(Token.LPAREN);
            String expr = parseExpression();
            match(Token.RPAREN);
            return new PrimitiveStatement("Write(" + expr + ")");
        } else if (check(Token.WRITELN)) {
            match(Token.WRITELN);
            return new PrimitiveStatement("WriteLn");
        } else if (check(Token.IDENT)) {
            // 赋值 or 过程调用 —— 需要 LL(1) 前瞻第二个 Token
            Token first = lookahead;
            match(Token.IDENT);
            String id = (String) first.value;

            if (check(Token.LPAREN)) {
                // 过程调用
                match(Token.LPAREN);
                StringBuilder args = new StringBuilder();
                if (!check(Token.RPAREN)) {
                    args.append(parseExpression());
                    while (check(Token.COMMA)) {
                        match(Token.COMMA);
                        args.append(", ").append(parseExpression());
                    }
                }
                match(Token.RPAREN);
                return new PrimitiveStatement(id + "(" + args + ")");
            } else {
                // 赋值: ident Selector {"," ident Selector} ":=" Expression
                StringBuilder lhs = new StringBuilder(id);
                lhs.append(parseSelectorPartList());
                while (check(Token.COMMA)) {
                    match(Token.COMMA);
                    lhs.append(", ");
                    match(Token.IDENT);
                    lhs.append(lookahead.value);  // 已经前进所以需要回退...简化处理
                    lhs.append(parseSelectorPartList());
                }
                match(Token.ASSIGN);
                String rhs = parseExpression();
                return new PrimitiveStatement(lhs + " := " + rhs);
            }
        } else if (check(Token.END) || check(Token.ELSIF) || check(Token.ELSE)
                   || check(Token.SEMI)) {
            // 空语句
            return null;
        } else {
            throw new MismatchedCommentException(
                "语法错误: 非法的语句开始符号 " + Token.typeName(lookahead.type),
                lookahead.line, lookahead.column);
        }
    }

    private String parseSelectorPartList() throws Exception {
        StringBuilder sb = new StringBuilder();
        while (check(Token.DOT) || check(Token.LBRACK)) {
            if (check(Token.DOT)) {
                match(Token.DOT);
                Token field = lookahead;
                match(Token.IDENT);
                sb.append(".").append(field.value);
            } else {
                match(Token.LBRACK);
                String idx = parseExpression();
                match(Token.RBRACK);
                sb.append("[").append(idx).append("]");
            }
        }
        return sb.toString();
    }

    /* ---- IF 语句 ---- */
    private IfStatement parseIfStatement() throws Exception {
        match(Token.IF);
        String cond = parseExpression();
        match(Token.THEN);

        IfStatement ifStmt = new IfStatement(cond);

        // True 分支
        parseStatementSequence(ifStmt.getTrueBody());

        // ELSIF 分支
        while (check(Token.ELSIF)) {
            match(Token.ELSIF);
            // ELSIF 在 flowchart API 中没有直接对应...
            // 使用嵌套 IfStatement 模拟:
            // 将 ELSIF 条件转为: IF cond2 THEN ... 放在当前 if 的 false 分支中
            String elsifCond = parseExpression();
            match(Token.THEN);
            IfStatement nestedIf = new IfStatement(elsifCond);
            parseStatementSequence(nestedIf.getTrueBody());
            // 将此嵌套 if 加入原 if 的 false body
            ifStmt.getFalseBody().add(nestedIf);
            // 后续 ELSIF 继续挂在 nestedIf 的 false 分支上
            ifStmt = nestedIf;
        }

        // ELSE 分支
        if (check(Token.ELSE)) {
            match(Token.ELSE);
            parseStatementSequence(ifStmt.getFalseBody());
        }

        match(Token.END);
        return ifStmt;
    }

    /* ---- WHILE 语句 ---- */
    private WhileStatement parseWhileStatement() throws Exception {
        match(Token.WHILE);
        String cond = parseExpression();
        match(Token.DO);

        WhileStatement whileStmt = new WhileStatement(cond);

        // 循环体
        parseStatementSequence(whileStmt.getLoopBody());

        match(Token.END);
        return whileStmt;
    }

    // ================================================================
    // Expression (运算符优先级用递归下降分层实现)
    // ================================================================

    /**
     * Expression = SimpleExpression [Relation SimpleExpression].
     */
    private String parseExpression() throws Exception {
        String left = parseSimpleExpression();
        if (isRelationOp()) {
            String op = getRelationOp();
            String right = parseSimpleExpression();
            return left + " " + op + " " + right;
        }
        return left;
    }

    private boolean isRelationOp() {
        switch (lookahead.type) {
            case Token.EQ: case Token.NEQ: case Token.LT:
            case Token.LE: case Token.GT: case Token.GE:
                return true;
            default: return false;
        }
    }

    private String getRelationOp() throws Exception {
        String op = lookahead.type == Token.EQ ? "="
                  : lookahead.type == Token.NEQ ? "#"
                  : lookahead.type == Token.LT ? "<"
                  : lookahead.type == Token.LE ? "<="
                  : lookahead.type == Token.GT ? ">"
                  : ">=";
        advance();
        return op;
    }

    /**
     * SimpleExpression = ["+"|"-"] Term {AddOperator Term}.
     * 用 while 循环处理 {AddOperator Term} 闭包.
     */
    private String parseSimpleExpression() throws Exception {
        String sign = "";
        if (check(Token.PLUS)) {
            sign = "+";
            advance();
        } else if (check(Token.MINUS)) {
            sign = "-";
            advance();
        }
        String result = sign + parseTerm();
        // {AddOperator Term}
        while (check(Token.PLUS) || check(Token.MINUS) || check(Token.OR)) {
            String op = check(Token.PLUS) ? "+" : check(Token.MINUS) ? "-" : "OR";
            advance();
            result = result + " " + op + " " + parseTerm();
        }
        return result;
    }

    /**
     * Term = Factor {MulOperator Factor}.
     */
    private String parseTerm() throws Exception {
        String result = parseFactor();
        while (check(Token.STAR) || check(Token.DIV) || check(Token.MOD)
               || check(Token.AND)) {
            String op = check(Token.STAR) ? "*"
                      : check(Token.DIV) ? "DIV"
                      : check(Token.MOD) ? "MOD"
                      : "&";
            advance();
            result = result + " " + op + " " + parseFactor();
        }
        return result;
    }

    /**
     * Factor = Number | BoolLit | Designator
     *        | "(" Expression ")" | "~" Factor .
     */
    private String parseFactor() throws Exception {
        if (check(Token.INTEGER)) {
            String val = lookahead.value.toString();
            advance();
            return val;
        } else if (check(Token.BOOL_LIT)) {
            String val = lookahead.value.toString();
            advance();
            return val;
        } else if (check(Token.IDENT)) {
            return parseDesignator();
        } else if (check(Token.LPAREN)) {
            match(Token.LPAREN);
            String inner = parseExpression();
            match(Token.RPAREN);
            return "(" + inner + ")";
        } else if (check(Token.NOT)) {
            match(Token.NOT);
            return "~" + parseFactor();
        } else {
            throw new MismatchedCommentException(
                "语法错误: 非法的因子开始符号 " + Token.typeName(lookahead.type),
                lookahead.line, lookahead.column);
        }
    }

    /**
     * Designator = qualident {"." ident | "[" Expression "]"}.
     */
    private String parseDesignator() throws Exception {
        Token id = lookahead;
        match(Token.IDENT);
        StringBuilder sb = new StringBuilder((String) id.value);
        sb.append(parseSelectorPartList());
        return sb.toString();
    }

    /* ---- ident list ---- */
    private void parseIdentList() throws Exception {
        match(Token.IDENT);
        while (check(Token.COMMA)) {
            match(Token.COMMA);
            match(Token.IDENT);
        }
    }
}
