'''
Created on Jun 12, 2019

@author: sarvi
'''
import json

def fixture_loadenv(fixturefile):
    env = []
    with open(fixturefile, 'r') as f:
        for l in f.readlines():
            if l.startswith('TESTCASES:'):
                env = '\n'.join(env).strip()
                return json.loads(env)
            env.append(l)
    return {}

def fixture_load(fixturefile):
    env = fixture_loadenv(fixturefile)
    testcases = False
    tcase = list()
    with open(fixturefile, 'r') as f:
        for cmd in f.readlines():
            if cmd.startswith('TESTCASES:'):
                testcases = True
                continue
            if not testcases:
                continue
            if not cmd.strip():
                yield (env, ''.join(tcase))
                tcase = list()
                continue
            tcase.append(cmd)
    if tcase:
        yield (env, ''.join(tcase))


def fixture_loadsets(fixturefile):
    env = fixture_loadenv(fixturefile)
    testcases = False
    tcase = list()
    with open(fixturefile, 'r') as f:
        for cmd in f.readlines():
            if cmd.startswith('TESTCASES:'):
                testcases = True
                continue
            if not testcases:
                continue
            if not cmd.strip():
                yield (env, tuple(tcase))
                tcase = list()
                continue
            tcase.append(cmd)
    if tcase:
        yield (env, tuple(tcase))


def fixture_loadpairsets(fixturefile):
    env = fixture_loadenv(fixturefile)
    testcases = False
    tcase = list()
    tcasepair = list()
    with open(fixturefile, 'r') as f:
        for cmd in f.readlines():
            if cmd.startswith('TESTCASES:'):
                testcases = True
                continue
            if not testcases:
                continue
            if not cmd.strip():
                tcasepair.append(tuple(tcase))
                tcase = list()
                if len(tcasepair) == 2:
                    yield (env, tuple(tcasepair))
                    tcasepair = list()
                continue
            tcase.append(cmd)
    if tcase:
        tcasepair.append(tuple(tcase))
        yield (env, tuple(tcasepair))

