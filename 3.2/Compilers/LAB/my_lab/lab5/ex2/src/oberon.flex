/* ===========================================================
 * OberonScanner —— Oberon-0 词法分析器 (JFlex 输入文件)
 * 目标语言: Oberon-0 (Wirth 1996)
 * 生成类名: OberonScanner
 * 自包含模式 (无外部依赖, 不使用 CUP)
 * =========================================================== */

import exceptions.*;

%%

/* ----- 用户代码段 ----- */
%class OberonScanner
%public
%unicode
%ignorecase
%line
%column

/* 返回自定义 Token 对象 */
%type Token

%{
    /* 当前词素缓冲区 */
    private StringBuilder lexeme = new StringBuilder();

    private Token token(int type) {
        return new Token(type, yyline + 1, yycolumn + 1);
    }
    private Token token(int type, Object value) {
        return new Token(type, yyline + 1, yycolumn + 1, value);
    }
%}

/* ----- 宏定义 ----- */
LineTerminator  = \r|\n|\r\n
WhiteSpace      = {LineTerminator} | [ \t\f]

Letter          = [a-zA-Z]
Digit           = [0-9]
Identifier      = {Letter}({Letter}|{Digit})*

/* 十进制整数: 单个 0 或 非0数字开头后跟任意数字 */
DecInteger      = 0 | [1-9]{Digit}*
/* 八进制整数: 0 开头后跟八进制数字 (0-7) */
OctInteger      = 0[0-7]+
/* 非法八进制: 0 开头后跟若干0-7数字, 但包含 8 或 9 */
IllegalOct      = 0[0-9]*[89]+[0-9]*

/* 允许数字后紧跟字母 → 在动作中检测并抛异常 */
DigitsAndLetter = {Digit}+{Letter}+

%state COMMENT

%%

/* ----- 分词规则 (从上到下优先匹配) ----- */

/* === 空白与换行 === */
<YYINITIAL> {
    {WhiteSpace}    { /* 跳过空白 */ }
}

/* === 注释 (不嵌套) === */
<YYINITIAL> {
    "(*"            { yybegin(COMMENT); }
}
<COMMENT> {
    "*)"            { yybegin(YYINITIAL); }
    [^]             { /* 注释内容，全部忽略 */ }
    <<EOF>>         { throw new MismatchedCommentException(
                       "注释不闭合: 缺少 '*)'", yyline + 1, yycolumn + 1); }
}

/* === 数字与标识符粘连检测 === */
<YYINITIAL> {
    {DigitsAndLetter} {
        throw new IllegalIntegerException(
            "数字与标识符粘连: \"" + yytext() + "\"", yyline + 1, yycolumn + 1);
    }
}

/* === 非法八进制检测 === */
<YYINITIAL> {
    {IllegalOct} {
        throw new IllegalOctalException(
            "非法八进制字面量: \"" + yytext() + "\"", yyline + 1, yycolumn + 1);
    }
}

/* === 十进制整数 === */
<YYINITIAL> {
    {DecInteger}    {
        return token(Token.INTEGER, Integer.valueOf(yytext()));
    }
}

/* === 八进制整数 === */
<YYINITIAL> {
    {OctInteger}    {
        return token(Token.INTEGER, Integer.valueOf(yytext(), 8));
    }
}

/* === 保留字 (大小写无关, 必须在 Identifier 之前) === */
<YYINITIAL> {
    "MODULE"        { return token(Token.MODULE); }
    "BEGIN"         { return token(Token.BEGIN); }
    "END"           { return token(Token.END); }
    "IF"            { return token(Token.IF); }
    "THEN"          { return token(Token.THEN); }
    "ELSIF"         { return token(Token.ELSIF); }
    "ELSE"          { return token(Token.ELSE); }
    "WHILE"         { return token(Token.WHILE); }
    "DO"            { return token(Token.DO); }
    "PROCEDURE"     { return token(Token.PROCEDURE); }
    "VAR"           { return token(Token.VAR); }
    "CONST"         { return token(Token.CONST); }
    "TYPE"          { return token(Token.TYPE); }
    "RECORD"        { return token(Token.RECORD); }
    "ARRAY"         { return token(Token.ARRAY); }
    "OF"            { return token(Token.OF); }
}

/* === 预定义关键字 / 类型 === */
<YYINITIAL> {
    "INTEGER"       { return token(Token.INTEGER_TYPE); }
    "BOOLEAN"       { return token(Token.BOOLEAN_TYPE); }
    "Read"          { return token(Token.READ); }
    "Write"         { return token(Token.WRITE); }
    "WriteLn"       { return token(Token.WRITELN); }
}

/* === 布尔字面量 === */
<YYINITIAL> {
    "TRUE"          { return token(Token.BOOL_LIT, Boolean.TRUE); }
    "FALSE"         { return token(Token.BOOL_LIT, Boolean.FALSE); }
}

/* === 运算符与分界符 === */
<YYINITIAL> {
    "+"             { return token(Token.PLUS); }
    "-"             { return token(Token.MINUS); }
    "*"             { return token(Token.STAR); }
    "DIV"           { return token(Token.DIV); }
    "MOD"           { return token(Token.MOD); }
    "&"             { return token(Token.AND); }
    "OR"            { return token(Token.OR); }
    "~"             { return token(Token.NOT); }
    "="             { return token(Token.EQ); }
    "#"             { return token(Token.NEQ); }
    "<"             { return token(Token.LT); }
    "<="            { return token(Token.LE); }
    ">"             { return token(Token.GT); }
    ">="            { return token(Token.GE); }
    ":="            { return token(Token.ASSIGN); }
    ":"             { return token(Token.COLON); }
    ";"             { return token(Token.SEMI); }
    "."             { return token(Token.DOT); }
    ","             { return token(Token.COMMA); }
    "("             { return token(Token.LPAREN); }
    ")"             { return token(Token.RPAREN); }
    "["             { return token(Token.LBRACK); }
    "]"             { return token(Token.RBRACK); }
}

/* === 标识符 (含长度检查) === */
<YYINITIAL> {
    {Identifier}    {
        String id = yytext();
        if (id.length() > 24) {
            throw new IllegalIdentifierLengthException(
                "标识符长度超过24: \"" + id + "\" (" + id.length() + "字符)",
                yyline + 1, yycolumn + 1);
        }
        return token(Token.IDENT, id);
    }
}

/* === 非法符号 (兜底规则) === */
<YYINITIAL> {
    [^]             {
        throw new IllegalSymbolException(
            "非法符号: '" + yytext() + "' (0x"
            + Integer.toHexString((int)yytext().charAt(0)) + ")",
            yyline + 1, yycolumn + 1);
    }
}
