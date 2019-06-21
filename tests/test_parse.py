'''
Created on May 13, 2019

@author: sarvi
'''
import json
import unittest
from parameterized import parameterized_class
from bashspy.lexer import BashLexer
from bashspy.parser import BashParser

def fixture_loadparse(fixturefile):
    tcase = list()
    data = list()
    idx = 0
    with open(fixturefile, 'r') as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            if line.strip() !=  '':
                data.append(line)
                continue
            if not  data:
                if tcase:
                    raise Exception('Incomplete Test Case: %s in file %s' % (tcase[0], fixturefile))
                continue
            if not tcase:
                try:
                    tcase.append(''.join(data))
                except json.decoder.JSONDecodeError:
                    print('Error parsing Jsob object in text fixtures: %s'%(''.join(data)))
                    raise
            elif len(tcase) == 1:
                tcase.append(''.join(data))
                yield tuple([idx]+tcase)
                idx = idx + 1
                tcase = list()
            else:
                raise Exception('Incorrect number of entries in test case data')
            data =  list()
    return


@parameterized_class(('index', 'parsed_command', 'command'), list(fixture_loadparse('tests/fixtures/parse.fix')))
class TestParseCmds(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        pass


    def tearDown(self):
        pass

    def testParseCmds(self):
        print('\nTest Case: testParseCmds_%d\nOriginal Command:\n%s\nParsed Out:\n%s' % (self.index, self.command, self.parsed_command))
        lexer = BashLexer()
        parser = BashParser()
        result = parser.parse(lexer.tokenize(self.command))
        self.assertEqual(self.parsed_command.strip(), str(result).strip())
#         errmsg = 'Length expected=%d, got=%s\nTokens:\nexpected:\n%s\ngot:\n%s\n' % (
#             len(self.tokens), len(lexer._token_list),
#             json.dumps(self.tokens),
#             json.dumps([(i.type, i.value) for i in lexer._token_list]))
#         self.assertEqual(len(self.tokens), len(lexer._token_list), errmsg)
#         for i, tok in  enumerate(lexer._token_list):
#             self.assertEqual(self.tokens[i][0], tok.type, errmsg + 'Index: %d\n'%i)
#             self.assertEqual(self.tokens[i][1], tok.value, errmsg + 'Index: %d\n'%i)

#     def testModifyAndRegenerate(self):
#         print('Original Command:\n', self.environment, self.command)
#         lexer = BashLexer()
#         for tok in lexer.tokenize(self.command):
#             print(type(tok), tok)
#         lexer._token_list[0].doinsert(' beginning ')
#         lexer._token_list[-1].doappend(' ending ')
#         lexer._token_list[3].doreplace('PLATFORM', 'MACHINE')
#         regstr = lexer.regenerate()
#         print('Regenerated: ', regstr)
#         self.assertRegex(regstr, r'^\s*(\\\n\s*)*beginning ')
#         self.assertRegex(regstr, r' ending\s*(\\\n\s*)*$')
#         if 'PLATFORM' in self.command:
#             self.assertIn('MACHINE', regstr)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()