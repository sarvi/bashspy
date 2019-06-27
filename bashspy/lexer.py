'''
Created on Jun 12, 2019

@author: sarvi
'''

from functools import partial
from sly import lex, Lexer
from sly.lex import LexError, Token


class BashToken(Token):
    __slots__ = ('changes', )
    
    def __init__(self):
        Token.__init__(self)
        self.changes = []
        
        
    def doinsert(self, modstr, index=0):
        def insert(modstr, index, out):
            if index < 0:
                return out[:index] + modstr + out[index:]
            else:
                return out[:index] + modstr + out[index:]
        if self.changes is None:
            self.changes = []
        self.changes.append(partial(insert, modstr, index))

    def doappend(self, modstr):
        def append(modst, out):
            return out + modstr
        self.changes.append(partial(append, modstr))

    def doreplace(self, old, new):
        def replace(old, new, out):
            return out.replace(old, new)
        self.changes.append(partial(replace, old, new))

lex.Token = BashToken


class BashLexer(Lexer):
    # Set of token names.   This is always required
    tokens = { QSTRING, DQSTRING, ECHO_STRING, BTQUOTED,
               ID, WHILE, IF, THEN, ELSE, FI, ECHO,
               WHILE, DONE, DO, FOR, LET,
               REDIRECT,
               CMD_EXP, VAR_SUBST, VARIABLE, VAL_STRING, OPTION, TIME_OPTP, WORD, TIME,
               BOOL_AND, BOOL_OR, BOOL_EQ, STAR, BOOL_NEQ, BOOL_LESS, BOOL_GREATER, BOOL_NEQ, BOOL_NOT,
               ARITH_ASSIGN, ASSIGN, LDBRACK, LPAREN, RDBRACK, LBRACK, RBRACK, RPAREN, LBRACE, RBRACE,
               PIPE, CMDSEP, NEWLINE, AMPERSAND}


    # Regular expression rules for tokens
    ECHO_STRING    = r'(?<=echo[\s])[^;\n]+'
    QSTRING        = r"'([^']|(?<=\\)')*'"
    DQSTRING        = r'"([^"]|(?<=\\)")*"'
    BTQUOTED        = r"`([^`]|(?<=\\)`)*`"
    CMD_EXP        = r'\$\([^\)]+\)'
    VAR_SUBST      = r'\${[^{]+}'
    VARIABLE       = r'\$(\?|[A-Za-z_][A-Za-z_0-9]*)'
    VAL_STRING        = r'(?<==)[^ \t\n]+'

    # Keywords
    IF = r'(?<=\b)if(?=\b)'
    THEN = r'(?<=\b)then(?=\b)'
    ELSE = r'(?<=\b)else(?=\b)'
    FI = r'(?<=\b)fi(?=\b)'
    FOR = r'(?<=\b)for(?=\b)'
    WHILE = r'(?<=\b)while(?=\b)'
    DONE = r'(?<=\b)done(?=\b)'
    DO = r'(?<=\b)do(?=\b)'
    ECHO = r'(?<=\b)echo(?=\b)'
#    PRINT = r'(?<=\b)print(?=\b)'
    LET = r'(?<=\b)let(?=\b)'

    # Identifiers and keywords
    ID = r'(?<!=)[a-zA-Z_][a-zA-Z0-9_]*(?=[\+\-]?=)'
    
    REDIRECT       = r'(\[[0-9a-z]\]|[&]?|[0-9a-z]*)(>>|<>|<|>)(&([\-]|[0-9a-z]))?'

    OPTION = r'(?<!=)[\-][a-zA-Z0-9_\-]+'
    OPTION['-p']   = TIME_OPTP

    WORD = r'(?<!=)[a-zA-Z0-9_\/\-\.]+(?!=<|>)'
    WORD['time']   = TIME

    BOOL_AND       = r'&&'
    BOOL_OR        = r'\|\|'
    BOOL_EQ        = r'=='
    BOOL_NEQ       = r'!='
    BOOL_LESS      = r'<'
    BOOL_GREATER   = r'>'
    LPAREN         = r'\('
    RPAREN         = r'\)'
    LBRACE         = r'{'
    RBRACE         = r'}'
    LDBRACK        = r'\[\['
    RDBRACK        = r'\]\]'
    LBRACK         = r'\['
    RBRACK         = r'\]'
    ARITH_ASSIGN   = r'\-=|\+='
    ASSIGN         = r'='
    PIPE           = r'\|'
    STAR           = r'\*'
    CMDSEP         = r';'
    AMPERSAND      = r'(?<=\b)&(?=\b)'
    BOOL_NOT       = r'!'

    # Line number tracking
    @_(r'\n+')
    def NEWLINE(self, t):
        self.lineno += t.value.count('\n')
        return t

    # String containing ignored characters
    ignore = ' \t'
    # ignore_linecontinuation = r'(?:\\\n){1}'
    ignore_comment = r'\#.*'

    @_(r'(?:\\\n)+')
    def ignore_linecontinuation(self,  t):
        self.lineno += t.value.count('\\\n')


#     @_(r'\d+')
#     def NUMBER(self, t):
#         return t

    def error(self, t):
        print('Line %d: Bad character %r' % (self.lineno, t.value[0]))
        self.index += 1
        raise LexError(f'Illegal character {t.value[0]!r} at index {self.index}', t.value, self.index)
    
    def tokenize(self, text, lineno=1, index=0):
        self._token_list =[]
        for tok in Lexer.tokenize(self, text, lineno=lineno, index=index):
            self._token_list.append(tok)
            yield tok

    def regenerate(self):
        retstr = []
        index = 0
        for tok in self._token_list:
            if  tok.index > index:
                retstr.append(self.text[index:tok.index])
            value = tok.value
            if tok.changes:
                for change in tok.changes:
                    value = change(value)             
            retstr.append(value)
            index = tok.index + len(tok.value)
        if index != len(self.text):
            retstr.append(self.text[index:])
        return ''.join(retstr)

if __name__ == '__main__':
    data = '''
# Counting
x = 0;
while (x < 10) {
    print x:
    x = x + 1;
}
'''
    lexer = BashLexer()
    for tok in lexer.tokenize(data):
        print(tok)