#!/usr/bin/env python3

import json
import logging
import pexpect
import re
import shlex
import signal
import time

def ensureRE(s):
    # if isinstance(s, str):
    #     return re.compile(s)
    return s

class Session(object):

    def __init__(self, params, prompt_re, filter_output=True, ignore_tail_whitespace=True, quit_string='exit'):
        self.__connection = None
        self.__params = params
        self.__prompt_re = r'\s*{}\s*'.format(prompt_re) if ignore_tail_whitespace else prompt_re
        self.__prompt_stripper = re.compile(self.__prompt_re + r'\Z')
        self.__create_time = time.time()
        self.__output_filter = (lambda s: self.__prompt_stripper.sub('', s)) if filter_output else (lambda s: s)
        self.__builtins = None
        self.__builtins = list(dir(self))
        self.__quit_string = quit_string

    def __del__(self):
        self.__disconnect()

    def __enter__(self):
        self.__connect()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.__disconnect()

    def __get_end_regex(self, end_regex=None):
        end_regex = end_regex if end_regex else self.__prompt_re
        if isinstance(end_regex, str):
            return {ensureRE(end_regex):None}
        elif isinstance(end_regex, dict):
            return {ensureRE(k):end_regex[k] for k in end_regex}
        elif isinstance(end_regex, list):
            return {ensureRE(e):None for e in end_regex}

    # def __read_raw(self, end_matcher, timeout=10, **kwargs):
    #     if not self.__connection:
    #         raise RuntimeError("Must connect first.")
    #     buff = ""
    #     while True:
    #         buff = buff + self.__connection.read_nonblocking(size=1024, timeout=timeout).decode('utf-8')
    #         if end_matcher.search(buff):
    #             return buff

    def __read_raw(self, end_matcher, timeout=None, **kwargs):
        timeout = timeout if timeout else 10
        if not self.__connection:
            raise RuntimeError("Must connect first.")
        buff = ""
        while True:
            try:
                buff = buff + self.__connection.read_nonblocking(size=1024, timeout=timeout).decode('utf-8')
                print("Buff: " + buff)
                if end_matcher.search(buff):
                    return buff
            except pexpect.EOF:
                print(buff)
                return buff
            except pexpect.TIMEOUT:
                print(buff)
                return buff


            
    def __process(self, handler, timeout=10, maxdepth=10, depth=0):
        print('process called...')
        patterns = list(handler.keys()) + [pexpect.EOF, pexpect.TIMEOUT]
        # patterns = list(handler.keys())
        index = self.__connection.expect(pattern=patterns, timeout=timeout)
        print('Index: {}'.format(index))
        if index >= len(handler):
            print('EOF or timeout encountered')
            return None
        response = self.__connection.match.string
        matched = patterns[index]
        print('Matched: {} ({})'.format(matched, type(matched)))
        print(self.__connection.match)
        print(self.__connection.match.string)
        # response = self.__read_raw(matched)
        action = handler.get(matched)
        if action and callable(action):
            action = action(response)
        if action:
            self.__connection.sendline(action)
            return response + self.__process(handler, timeout, depth = depth + 1)
        else:
            return response

    def __connect(self, force=False, end_regex=None, **kwargs):
        end_handler = self.__get_end_regex(end_regex)
        if not self.__connected() or force:
            self.__create_time = time.time()
            self.__connection = pexpect.spawn(self.__params)
            self.__process(end_handler)
            # patterns = list(end_handler.keys())
            # response = self.__connection.expect(pattern=patterns, timeout=10)
            # if response > 0:
            #     self.__connection = None
            #     raise RuntimeError("Unable to connect.")
            # else:
            #     pass

    def __disconnect(self, **kwargs):
        if self.__connected():
            self.__connection.sendline(self.__quit_string)
            patterns = [pexpect.EOF, pexpect.TIMEOUT]
            response = self.__connection.expect(pattern=patterns, timeout=10)
            if response != 0:
                self.__connection.kill(signal.SIGTERM)
                pass
            self.__connection = None

    def __clean_up_white_space(self, string_to_clean_up):
        return re.sub(r"\s+", " ", string_to_clean_up.strip())

    def __read(self, timeout=None, end_condition_regex=None, **kwargs):
        timeout = timeout if timeout else 120
        if not self.__connection:
            raise RuntimeError("Must connect first.")
        buff = ""
        sanitized_matcher = None
        if end_condition_regex:
            sanitized_matcher = re.compile(self.__clean_up_white_space(end_condition_regex))
        while True:
            try:
                buff = buff + self.__connection.read_nonblocking(size=1024, timeout=timeout).decode('utf-8')
                if end_condition_regex:
                    sanitized_buff = self.__clean_up_white_space(buff)
                    if sanitized_matcher.search(sanitized_buff):
                        return buff
            except pexpect.EOF:
                return buff
            except pexpect.TIMEOUT:
                return buff

    def _run(self, command, end_regex=None, **kwargs):
        self.__connection.sendline(command)
        output = self.__read(end_condition_regex=end_regex if end_regex else self.__prompt_re, **kwargs)
        response = re.sub(r'\A{}\r\n'.format(re.escape(command)), r'', self.__output_filter(output))
        logging.debug(response)
        return response

    def _stop(self, **kwargs):
        self.__disconnect(**kwargs)
        logging.info("Session disconnected.")
        return True

    def _start(self, **kwargs):
        self.__connect(**kwargs)
        logging.info("Session connected.")
        return True

    def _restart(self, **kwargs):
        self._stop()
        response = self._start()
        logging.info("Session restarted.")
        return response

    def __connected(self):
        return not not self.__connection

    def _status(self, **kwargs):
        if self.__connected():
            logging.info("Session is connected.")
            return True
        else:
            logging.info("Session is not connected.")
            return False

    def _define(self, name, output_filter=(lambda s: s), input_filter=None, cmd=None):
        if name in self.__builtins:
            raise RuntimeError("Overriding a builtin method isn't supported as it'll likely break everything.")
        cmd = cmd if cmd else name
        input_filter = input_filter if input_filter else (lambda *args: shjoin(*([cmd] + list(args))))
        func = lambda *args, **kwargs: output_filter(self._run(input_filter(*args, **kwargs)))
        setattr(self, name, func)

    def _undefine(self, name):
        if name in self.__builtins:
            raise RuntimeError("Removing a builtin method isn't supported as it'll likely break everything.")
        if hasattr(self, name) and name not in self.__builtins:
            delattr(self, name)

def shjoin(*args):
    try:
        return ' '.join(shlex.quote(str(s)) for s in args)
    except:
        # shlex.quote wasn't added until python3.3
        return ' '.join(json.dumps(str(s)) for s in args)
