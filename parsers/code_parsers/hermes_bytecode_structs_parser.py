#!/usr/bin/python3
#-*- encoding: Utf-8 -*-
from re import search, match, findall, sub, finditer, MULTILINE, DOTALL
from typing import List, Dict, Set, Sequence, Union, Optional, Any
from os.path import dirname, realpath
from dataclasses import dataclass

CODE_PARSERS_DIR = dirname(realpath(__file__))
PARSERS_DIR = realpath(CODE_PARSERS_DIR + '/..')

GIT_TAGS = 'v0.0.1 v0.0.2 v0.0.3 v0.1.0 v0.1.1 v0.2.1 v0.3.0 v0.4.0 v0.4.1 v0.4.3 v0.4.4 v0.5.0 v0.5.1 v0.5.3 v0.6.0 v0.7.0 v0.7.1 v0.7.2 v0.8.0 v0.8.1 v0.9.0 v0.10.0 v0.11.0 v0.12.0'.split(' ')

for git_tag in GIT_TAGS:

    INPUT_FILE_NAME = PARSERS_DIR + '/original_hermes_bytecode_c_src/BytecodeList-%s.def' % git_tag

    INPUT_VERSION_FILE_NAME = PARSERS_DIR + '/original_hermes_bytecode_c_src/BytecodeVersion-%s.h' % git_tag

    with open(INPUT_VERSION_FILE_NAME) as fd:
        version_file_contents = fd.read()
    bytecode_version : int = int(search(r'BYTECODE_VERSION = (\d+)', version_file_contents).group(1))

    OUTPUT_FILE_NAME = PARSERS_DIR + '/hbc_opcodes/hbc%d.py' % bytecode_version

    out_source = '''#!/usr/bin/python3
#-*- encoding: Utf-8 -*-
"""
    Note: The contents of the current file have been automatically
    generated by the "code_parsers/hermes_bytecode_structs_parser.py"
    script
    
    Please do not edit it manually. 👍
"""

from typing import List, Set, Dict, Union, Optional, Sequence, Any

# Imports from the current diretory
from .def_classes import *

_instructions : List[Instruction] = []


'''

    opcode_count = 0

    with open(INPUT_FILE_NAME) as fd:
        
        input_source = fd.read()
    
    # Backport OPERAND_FUNCTION_ID declarations added with
    # version 0.12.0 (https://github.com/facebook/hermes/commit/c20d7d8)
    # in order to improve disassembly output readability if needed.
    
    if 'OPERAND_FUNCTION_ID(CallDirect, 3)' not in input_source:
        input_source += '''
OPERAND_FUNCTION_ID(CallDirect, 3)
OPERAND_FUNCTION_ID(CreateClosure, 3)
OPERAND_FUNCTION_ID(CreateClosureLongIndex, 3)
'''

        if 'CreateGeneratorClosure' in input_source:
            input_source += '''
OPERAND_FUNCTION_ID(CreateGeneratorClosure, 3)
OPERAND_FUNCTION_ID(CreateGeneratorClosureLongIndex, 3)
'''

        if 'CreateGenerator' in input_source:
            input_source += '''
OPERAND_FUNCTION_ID(CreateGenerator, 3)
OPERAND_FUNCTION_ID(CreateGeneratorLongIndex, 3)
'''

        if 'CreateAsyncClosure' in input_source:
            input_source += '''
OPERAND_FUNCTION_ID(CreateAsyncClosure, 3)
OPERAND_FUNCTION_ID(CreateAsyncClosureLongIndex, 3)
'''
        
    lines = input_source.splitlines()
    
    for line in lines:
        
        line = match('^((?:DEFINE|OPERAND)[^(]+?)\((.+?)\)', line)
        
        if line:
            directive, args = line.groups()
            args = args.split(', ')
            
            # print('=>', directive, args)
            
            if directive.startswith('DEFINE_OPERAND_TYPE'):
                out_source = out_source[:-1] # No endline before that for readibility
                out_source += f'{args[0]} = OperandType(\'{args[0]}\', \'{args[1]}\')\n\n'
            elif directive.startswith('DEFINE_OPCODE'):
                out_source += f'{args[0]} = Instruction(\'{args[0]}\', {opcode_count}, [{", ".join(args[1:])}], globals())\n\n'
                opcode_count += 1
            elif directive.startswith('DEFINE_JUMP'):
                args += {
                    'DEFINE_JUMP_1': ['Addr8'],
                    'DEFINE_JUMP_2': ['Addr8', 'Reg8'],
                    'DEFINE_JUMP_3': ['Addr8', 'Reg8', 'Reg8']
                }[directive]
                out_source += f'{args[0]} = Instruction(\'{args[0]}\', {opcode_count}, [{", ".join(args[1:])}], globals())\n'
                out_source += f'{args[0]}Long = Instruction(\'{args[0]}Long\', {opcode_count + 1}, [{", ".join(["Addr32"] + args[2:])}], globals())\n\n'
                opcode_count += 2
            elif directive.startswith('DEFINE_RET_TARGET'):
                out_source = out_source.strip()
                out_source += f'\n{args[0]}.has_ret_target = True\n\n'
            elif directive.startswith('OPERAND_'):
                operand_meaning = {
                    'OPERAND_BIGINT_ID': 'OperandMeaning.bigint_id',
                    'OPERAND_FUNCTION_ID': 'OperandMeaning.function_id',
                    'OPERAND_STRING_ID': 'OperandMeaning.string_id'
                }[directive]
                # out_source = out_source.strip()
                out_source += f'{args[0]}.operands[{(int(args[1]) - 1)}].operand_meaning = {operand_meaning}\n\n'

    out_source += '''_opcode_to_instruction : Dict[int, Instruction] = {v.opcode: v for v in _instructions}
_name_to_instruction : Dict[str, Instruction] = {v.name: v for v in _instructions}

'''

    with open(OUTPUT_FILE_NAME, 'w') as fd:
        fd.write(out_source)


    print()
    print('[+]  Wrote File => %s' % OUTPUT_FILE_NAME)

print()