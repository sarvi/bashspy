'''
Created on Jun 13, 2019

@author: sarvi
'''

import sys
from sly import Parser
from .lexer import BashLexer, BashToken


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

class BashParser(Parser):
    # Get the token list from the lexer (required)
    tokens = BashLexer.tokens

    # Grammar rules and actions
    
    @_('simple_commands')
    def program(self, p):
        print('program(%s)' % (p.simple_commands))
        return p.simple_commands

    @_('simple_command',
       'simple_command end_command',
       'simple_command end_command simple_commands')
    def simple_commands(self, p):
#         print('simple_command(%s)' % (list(p)))
        return [p.simple_command] if getattr(p, 'simple_commands', None) is None else [p.simple_command] + p.simple_commands
    
    @_('NEWLINE', 'CMDSEP')
    def end_command(self, p):
        return None
    
    @_('assignments',
       'assignments command_pipe',
       'command_pipe')
    def simple_command(self, p):
#         print('simple_command(%s)' % (list(p)))
        command = getattr(p, 'command_pipe', None) or ASTCommand(None, None, None, None)
        command.assignments.extend(getattr(p, 'assignments',  []))
        return command

    @_('command',
       'command PIPE command_pipe')
    def command_pipe(self, p):
#         print('simple_command(%s)' % (list(p)))
        topipe = getattr(p, 'command_pipe', None)
        if topipe:
            p.command.pipetocmd = topipe
        return p.command

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


    @_('WORD',
       'WORD arguments',
       'WORD redirects',
       'WORD arguments redirects')
#        'WORD arguments',
#        'WORD redirects',
#        'WORD arguments redirects')
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
    
    @_('OPTION ASSIGN arg_value', 'OPTION', 'arg_value')
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