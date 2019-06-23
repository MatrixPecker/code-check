#!/usr/bin/python3

import subprocess
import re
from pprint import pprint
import shlex


class FunctionDeclaration:
    def __init__(self, line):
        self.error = False

        # use regexp to parse the start and end line number
        function_range = re.findall(r"line:(\d+)", line)
        if len(function_range) < 2:
            self.error = True
            return
        self.start = int(function_range[0])
        self.end = int(function_range[1])

        # use a trick to split the line
        splitter = shlex.shlex(line, posix=True)
        splitter.whitespace += ','
        splitter.whitespace_split = True
        args = list(splitter)
        if len(args) < 2:
            self.error = True
            return
        self.name = args[-2]

        # use another trick to split the args
        splitter = shlex.shlex(args[-1], posix=True)
        splitter.whitespace += ',()'
        splitter.whitespace_split = True
        args = list(splitter)
        if len(args) < 1:
            self.error = True
            return
        self.ret_type = args[0]
        self.args_type = args[1:]
        self.prototype_comments = 0
        self.body_comments = 0
        self.body = []

    def set_body(self, lines):
        self.body = lines

    def analyze_comments(self):
        def add_comment():
            if state < 2:
                self.prototype_comments += 1
            else:
                self.body_comments += 1

        state = 0
        block_comment = False
        for i, line in self.body:
            line = line.strip()
            if len(line) == 0:
                if i > self.start:
                    state += 1
                continue
            left_block = len(re.findall(r'/\*', line))
            right_block = len(re.findall(r'\*/', line))
            if left_block > right_block:
                add_comment()
                block_comment = True
            elif left_block < right_block:
                add_comment()
                block_comment = False
            elif block_comment:
                add_comment()
            elif line.startswith('//'):
                add_comment()
            elif i > self.start:
                state += 1
        print('comments:', self.prototype_comments, self.body_comments)

    def __str__(self):
        return '%d:%d %s %s(%s)' % (self.start, self.end, self.ret_type, self.name, ', '.join(self.args_type))


def main():
    main_cpp = 'p1.cpp'
    main_cpp_found = False
    function_declares = []

    p = subprocess.Popen("clang-check-8 -ast-dump %s --" % main_cpp, shell=True, stdout=subprocess.PIPE)

    while p.poll() is None:
        line = p.stdout.readline().decode('utf-8')
        if main_cpp in line:
            main_cpp_found = True
        if main_cpp_found and 'FunctionDecl' in line and 'line' in line:
            line = re.sub(r'\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))', '', line).strip()
            function_declares.append(FunctionDeclaration(line))
        # if main_cpp_found:
        #    print(line.strip())

    # pprint(function_declares, width=120)

    with open(main_cpp, 'r') as main_cpp_file:
        main_cpp_contents = main_cpp_file.readlines()

    for i, func in enumerate(function_declares):
        # print(line)
        print(func)
        if func.end <= len(main_cpp_contents):
            if i > 1:
                start = function_declares[i - 1].end
            else:
                start = func.start - 1
            end = func.end
            func.set_body([(x, main_cpp_contents[x]) for x in range(start, end)])
            func.analyze_comments()


main()
