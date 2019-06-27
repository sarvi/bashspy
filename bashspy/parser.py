'''
Created on Jun 13, 2019

@author: sarvi
'''

from sly import Parser
from .lexer import BashLexer


class ASTCommands(list):
    __slots__ = ('grouping')
    def __init__(self, command, grouping=None):
        self.append(command)
        self.grouping = grouping

    def __repr__(self):
        x=[str(i) for i in self]
        if  self.grouping:
            x.insert(0, self.grouping[0])
            x.append(self.grouping[1])
        return '\n'.join(x)


class ASTCommand:
    __slots__ = ('assignments', 'executable', 'arguments', 'redirections', 'pipetocmd')

    def __init__(self, executable=None, assignments=None, arguments=None, redirections=None, pipetocmd=None):
        self.executable = executable
        self.assignments = assignments or list()
        self.arguments = arguments or list()
        self.redirections  = redirections or list()
        self.pipetocmd = pipetocmd
        
    def __repr__(self):
        if self.executable:
            return ('%s %s %s %s %s' % (' '.join([str(i) for i in self.assignments]),
                                 self.executable,
                                 ' '.join([str(i) for i in self.arguments]),
                                 ' '.join([str(i) for i in self.redirections]),
                                 '| %s'%self.pipetocmd if self.pipetocmd else '')).strip()
        else:
            return ' '.join([str(i) for i in self.assignments])


class ASTAssignment:
    __slots__ = ('variable', 'assignop', 'value')

    def __init__(self, variable, assignop, value=None):
        self.variable = variable
        self.assignop = assignop
        self.value = value

    def __repr__(self):
        return '%s%s%s'%(self.variable,  self.assignop, self.value or '')

class ASTArgument:
    __slots__ = ('option', 'value')

    def __init__(self, option=None, value=None):
        self.option = option
        self.value = value

    def __repr__(self):
        return '%s=%s'%(self.option,  self.value) if self.option and self.value else (self.option  or self.value)

class ASTRedirection:
    __slots__ = ('redirect', 'file')

    def __init__(self, redirect, file):
        self.redirect = redirect
        self.file = file

    def __repr__(self):
        return '%s%s'%(self.redirect,  self.file) if self.file else '%s'%(self.redirect)

class ASTTestCombination:
    __slots__ = ('leftexpr', 'combination', 'rightexpr', 'test_command', 'group')

    def __init__(self, combination, rightexpr, leftexpr=None, test_command=False, group=False):
        self.combination = combination
        self.rightexpr  = rightexpr
        self.leftexpr = leftexpr
        self.test_command = test_command
        self.group = group

    def __repr__(self):
        if self.leftexpr:
            return '%s %s %s'%(self.leftexpr, self.combination, self.rightexpr)
        elif self.combination:
            return '%s %s'%(self.combination, self.rightexpr)
        elif self.test_command:
            return '[ %s ]'%(self.rightexpr)
        elif self.group:
            return '( %s )'%(self.rightexpr)
        else:
            return '%s'%(self.rightexpr)

class ASTTestCondition:
    __slots__ = ('leftvalue', 'test', 'rightvalue')

    def __init__(self, test, rightvalue, leftvalue=None):
        self.test = test
        self.leftvalue = leftvalue
        self.rightvalue = rightvalue

    def __repr__(self):
        if self.test:
            return '%s %s %s'%(self.leftvalue, self.test, self.rightvalue) if self.leftvalue  else '%s %s'%(self.test, self.rightvalue)
        else:
            return '%s' % (self.rightvalue)            


class ASTIfCommand:
    __slots__ = ('test_commands', 'then_commands', 'else_commands')

    def __init__(self, test_commands, then_commands, else_commands=None):
        self.test_commands = test_commands
        self.then_commands = then_commands
        self.else_commands = else_commands

    def __repr__(self):
        if self.else_commands:
            return 'if %s; then\n%s\nelse\n%s\nfi' % (self.test_commands, self.then_commands, self.else_commands)
        else:
            return 'if %s; then\n%s\nfi' % (self.test_commands, self.then_commands)


class BashParser(Parser):
    # Get the token list from the lexer (required)
    debugfile = 'parser.out'

    tokens = BashLexer.tokens

    precedence = (
#           ('nonassoc', BOOL_NOT),
#           ('nonassoc', BOOL_LESS, BOOL_GREATER, BOOL_EQ, BOOL_NEQ),  # Nonassociative operators
        ('left', LIST_COMMANDS),
        ('left', AMPERSAND, CMDSEP, NEWLINE),
        ('left', BOOL_COMBINATION),
        ('left', BOOL_COMPARISON),
        ('right', BOOL_NOT),
#           ('right', END_LINE)
     )

    # Grammar rules and actions
    
    @_('compound_commands')
    def program(self, p):
        print('program(%s)' % (p.compound_commands))
        return p.compound_commands

    @_('compound_command',
       'compound_command end_command',
       'compound_command end_command compound_commands'
       )
    def compound_commands(self, p):
#         print('simple_command(%s)' % (list(p)))
        if getattr(p, 'compound_commands', None):
            p.compound_commands.insert(0, p.compound_command)
            return p.compound_commands
        else:
            return ASTCommands(p.compound_command)

    @_(
       'group_command',
       'list_commands',
       'if_command',
       )
    def compound_command(self, p):
        return p[0]


    @_(
       'LBRACE NEWLINE compound_commands RBRACE',
       'LBRACE compound_commands RBRACE',
       'LPAREN compound_commands RPAREN',
       )
    def group_command(self, p):
        if getattr(p, 'LBRACE', None):
            p.compound_commands.grouping = '{}'
        elif getattr(p, 'LPAREN', None):
            p.compound_commands.grouping = '()'
        return getattr(p, 'compound_commands', None)


    @_('pipe_command %prec LIST_COMMANDS',
       'pipe_command end_pipe',
       'pipe_command end_pipe list_commands',
       'pipe_command boolean_combination list_commands')
    def list_commands(self, p):
        if getattr(p, 'boolean_combination', None):
            return ASTTestCombination(p.boolean_combination, p.list_commands, p.pipe_command)
        elif getattr(p, 'list_commands', None):
            p.list_commands.insert(0, p.pipe_command)
            return p.list_commands
        else:
            return ASTCommands(p.pipe_command)


    @_('NEWLINE', 'CMDSEP', 'AMPERSAND')
    def end_pipe(self, p):
        return None


    @_('NEWLINE', 'CMDSEP')
    def end_command(self, p):
        return None


    @_('IF list_commands THEN compound_commands FI',
       'IF list_commands THEN NEWLINE compound_commands FI',
       'IF list_commands THEN compound_commands ELSE compound_commands FI',
       'IF list_commands THEN NEWLINE compound_commands ELSE NEWLINE compound_commands FI')
    def if_command(self, p):
        if getattr(p, 'ELSE', None):
            return ASTIfCommand(p.list_commands, p.compound_commands0,  p.compound_commands1) 
        else:
            return ASTIfCommand(p.list_commands, p.compound_commands) 

#     @_( #'test_command',
#        'command_pipe',
#        # 'test_command boolean_combination compound_command',
# #        'command_pipe boolean_combination compound_command'
#        )
#     def compound_command(self, p):
#         if getattr(p, 'boolean_combination', None):
#             return ASTTestCombination(p.boolean_combination, p.test_commands, p.test_command)
#         else:
#             return p.test_command

    @_('time_command pipe_commands',
       'time_command BOOL_NOT pipe_commands',
       'pipe_commands',
       'BOOL_NOT pipe_commands')
    def pipe_command(self, p):
#         print('simple_command(%s)' % (list(p)))
        cmd = p.pipe_commands
        if getattr(p,  'BOOL_NOT', None):
            cmd = ASTTestCombination(p.BOOL_NOT, p.pipe_commands)
        return cmd


    @_('TIME',
       'TIME TIME_OPTP')
    def time_command(self, p):
        cmd = ASTCommand(p.TIME)
        if getattr(p, 'TIME_OPTP', None):
            cmd.arguments = [p.TIME_OPTP]
        return cmd

    @_('simple_command',
       'simple_command PIPE pipe_commands')
    def pipe_commands(self, p):
#         print('simple_command(%s)' % (list(p)))
        if getattr(p, 'PIPE', None):
            p.simple_command.pipetocmd = p.pipe_commands
        return p.simple_command

    @_('assignments',
       'base_command',
       'assignments base_command',
       'base_command redirects',
       'assignments base_command redirects')
    def simple_command(self, p):
#         print('simple_command(%s)' % (list(p)))
        cmd = p.base_command if getattr(p, 'base_command', None) else ASTCommand()
        if getattr(p, 'redirects', None):
            cmd.redirections = p.redirects
        if getattr(p, 'assignments', None):
            cmd.assignments = p.assignments
        return cmd

    @_('redirect',
       'redirect redirects')
    def redirects(self, p):
        return [p.redirect] if len(p)==1 else [p.redirect] + p.redirects

    @_('REDIRECT',
       'REDIRECT WORD')
    def redirect(self, p):
#         print('assignment(%s)' % (list(p)))
        return ASTRedirection(p.REDIRECT, getattr(p, 'WORD', None))

    @_('echo_command',
       'exec_command',
       'test_command')
    def base_command(self, p):
        if len(p)==2:
            p[1].assignments = p.assignments.assignments
            return p[1]
        else:
            return p[0]

    @_('LBRACK test_expressions RBRACK',
       'LDBRACK test_expressions RDBRACK')
    def test_command(self, p):
        if getattr(p, 'BOOL_NOT', None):
            return ASTTestCombination(p.BOOL_NOT, p.command_pipe)
        elif getattr(p, 'command_pipe', None):
            return ASTTestCombination(None, p.command_pipe)
        else:
            return ASTTestCombination(None, p.test_expressions, test_command=True)

    @_('test_expression',
       'LPAREN test_expressions RPAREN',
       'BOOL_NOT test_expressions %prec BOOL_NOT',
       'test_expressions boolean_combination test_expressions %prec BOOL_COMBINATION'
       )
    def test_expressions(self, p):
        if getattr(p, 'BOOL_NOT', None):
            return  ASTTestCombination(p.BOOL_NOT, p.test_expressions)
        elif getattr(p, 'boolean_combination', None):
            return ASTTestCombination(p.boolean_combination, p.test_expressions1, p.test_expressions0)
        elif getattr(p, 'LPAREN', None):
            return ASTTestCombination(None, p.test_expressions, group=True)
        else:
            return p.test_expression


    @_('BOOL_OR', 'BOOL_AND')
    def boolean_combination(self, p):
        return p[0]


    @_('value boolean_comparison value %prec BOOL_COMPARISON',
       'OPTION value')
    def test_expression(self, p):
        if getattr(p, 'BOOL_NOT', None):
            return  ASTTestCombination(p.BOOL_NOT, p.test_expression)
        elif getattr(p, 'LPAREN', None):
            return ASTTestCombination(None, p.test_expressions, group=True)
        elif getattr(p, 'OPTION', None):
            return ASTTestCondition(p.boolean_comparison, p.value)
        else:
            return ASTTestCondition(p.boolean_comparison, p.value1, p.value0)

    @_('OPTION', 'BOOL_EQ', 'BOOL_NEQ', 'BOOL_LESS', 'BOOL_GREATER', 'ASSIGN')
    def boolean_comparison(self, p):
        return p[0]

#     @_(
#        'for_command',
#        'case_command',
#        'WHILE compound_list DO compound_list DONE',
#        'UNTIL compound_list DO compound_list DONE', 
#        'select_command',
#        'if_command',
#        'subshell',
#        'group_command',
#        'arith_command'
#        'cond_command',
#        'arith_for_command'
#        )
#     def shell_command(self, p):
#         print('assignments(%s)' % (list(p)))
#         return list(p)


    @_('ECHO  ECHO_STRING')
    def echo_command(self, p):
        return ASTCommand(p[0], None, [p[1]])

    @_('WORD',
       'WORD arguments')
    def exec_command(self, p):
        return ASTCommand(p[0], None, getattr(p, 'arguments', None), getattr(p, 'redirects', None))

    @_('argument',
       'argument arguments')
    def arguments(self, p):
        return [p.argument] if len(p)==1 else [p.argument] + p.arguments
    
    @_('OPTION ASSIGN', 'OPTION', 'arg_value')
    def argument(self, p):
#         print('assignment(%s)' % (list(p)))
        return ASTArgument(getattr(p, 'OPTION', None), getattr(p, 'arg_value', None))
    
    @_('value', 'WORD')
    def arg_value(self, p):
#         print('value(%s)' % (list(p)))
        return p[0]

    @_('assignment',
       'assignment assignments')
    def assignments(self, p):
        return [p.assignment] if len(p) == 1 else [p.assignment] + p.assignments
   
    @_('LET ID assignop value', 'ID assignop value', 'ID assignop')
    def assignment(self, p):
#         print('assignment(%s)' % (list(p)))
        return ASTAssignment(p.ID, p.assignop, getattr(p, 'value', None))
    
    @_('ASSIGN', 'ARITH_ASSIGN')
    def assignop(self, p):
        return p[0]

    @_('QSTRING', 'DQSTRING', 'BTQUOTED', 'CMD_EXP', 'VAL_STRING', 'VAR_SUBST', 'VARIABLE')
    def value(self, p):
#         print('value(%s)' % (list(p)))
        return p[0]

if __name__ == '__main__':
    lexer = BashLexer()
    parser = BashParser()

    while True:
        try:
            text = input('Command:>')
            result = parser.parse(lexer.tokenize(text))
            print(result)
        except EOFError:
            break