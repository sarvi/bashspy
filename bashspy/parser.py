'''
Created on Jun 13, 2019

@author: sarvi
'''

from sly import Parser
from .lexer import BashLexer


class ASTCommands(list):
    def __init__(self, command):
        self.append(command)

    def __repr__(self):
        return '\n'.join([str(i) for i in self])


class ASTCommand:
    __slots__ = ('assignments', 'executable', 'arguments', 'redirections', 'pipetocmd')

    def __init__(self, executable, assignments=None, arguments=None, redirections=None, pipetocmd=None):
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
    __slots__ = ('variable', 'value')

    def __init__(self, variable, value=None):
        self.variable = variable
        self.value = value

    def __repr__(self):
        return '%s=%s'%(self.variable,  self.value or '')

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
    tokens = BashLexer.tokens

    # Grammar rules and actions
    
    @_('complex_commands')
    def program(self, p):
        print('program(%s)' % (p.complex_commands))
        return p.complex_commands

    @_('complex_command',
       'complex_command end_command',
       'complex_command end_command complex_commands')
    def complex_commands(self, p):
        if getattr(p, 'complex_commands', None):
            p.complex_commands.insert(0, p.complex_command)
            return p.complex_commands
        else:
            return ASTCommands(p.complex_command)

    @_('NEWLINE', 'CMDSEP')
    def end_command(self, p):
        return None
    
    @_('end_command complex_command',
       'simple_command',
       'if_command')
    def complex_command(self, p):
#         print('simple_command(%s)' % (list(p)))
        return getattr(p, 'simple_command', None) or getattr(p, 'complex_command', None) or getattr(p, 'if_command', None)

    @_('IF test_commands CMDSEP THEN complex_commands FI')
    @_('IF test_commands CMDSEP THEN complex_commands ELSE complex_commands FI')
    def if_command(self, p):
        if getattr(p, 'complex_commands', None):
            return ASTIfCommand(p.test_commands, p.complex_commands) 
        else:
            return ASTIfCommand(p.test_commands, p.complex_commands0,  p.complex_commands1) 

    @_('test_command',
       'test_command boolean_combination test_commands')
    def test_commands(self, p):
        if getattr(p, 'boolean_combination', None):
            return ASTTestCombination(p.boolean_combination, p.test_commands, p.test_command)
        else:
            return p.test_command

    @_('BOOL_OR', 'BOOL_AND')
    def boolean_combination(self, p):
        return p[0]

    @_('command_pipe',
       'BOOL_NOT command_pipe',
       'LBRACK test_expressions RBRACK',
       'LDBRACK test_expressions RDBRACK')
    def test_command(self, p):
        if getattr(p, 'BOOL_NOT', None):
            return ASTTestCombination(p.BOOL_NOT, p.command_pipe)
        elif getattr(p, 'command_pipe', None):
            return ASTTestCombination(None, p.command_pipe)
        else:
            return ASTTestCombination(None, p.test_expressions, test_command=True)


    @_('test_expression',
       'BOOL_NOT test_expressions',
       'LPAREN test_expressions RPAREN',
       'test_expression boolean_combination test_expressions')
    def test_expressions(self, p):
        if getattr(p, 'BOOL_NOT', None):
            return  ASTTestCombination(p.BOOL_NOT, p.test_expressions)
        elif getattr(p, 'boolean_combination', None):
            return ASTTestCombination(p.boolean_combination, p.test_expressions, p.test_expression)
        elif getattr(p, 'LPAREN', None):
            return ASTTestCombination(None, p.test_expressions, group=True)
        else:
            return p.test_expression


    @_('BOOL_NOT test_expression',
       'LPAREN test_expressions RPAREN',
       'value boolean_comparison value',
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

    @_('assignments',
       'assignments command_pipe',
       'command_pipe')
    def simple_command(self, p):
#         print('simple_command(%s)' % (list(p)))
        command = getattr(p, 'command_pipe', None) or ASTCommand(None, None, None, None)
        command.assignments.extend(getattr(p, 'assignments',  []))
        return command

    @_('echo_command',
       'command',
       'command PIPE command_pipe')
    def command_pipe(self, p):
#         print('simple_command(%s)' % (list(p)))
        topipe = getattr(p, 'command_pipe', None)
        if topipe:
            p.command.pipetocmd = topipe
        return getattr(p, 'command', None) or getattr(p, 'echo_command', None)

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
       'WORD arguments',
       'WORD redirects',
       'WORD arguments redirects')
    def command(self, p):
        return ASTCommand(p[0], None, getattr(p, 'arguments', None), getattr(p, 'redirects', None))

    @_('redirect',
       'redirect redirects')
    def redirects(self, p):
        return [p.redirect] if len(p)==1 else [p.redirect] + p.redirects
    
    @_('REDIRECT',
       'REDIRECT WORD')
    def redirect(self, p):
#         print('assignment(%s)' % (list(p)))
        return ASTRedirection(p.REDIRECT, getattr(p, 'WORD', None))
    
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
        return [p.assignment] if len(p)==1 else [p.assignment] + p.assignments
   
    @_('LET ID ASSIGN value', 'ID ASSIGN value', 'ID ASSIGN')
    def assignment(self, p):
#         print('assignment(%s)' % (list(p)))
        return ASTAssignment(p.ID, getattr(p, 'value', None))
    
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