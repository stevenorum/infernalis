#!/usr/bin/env python3

import argparse
from calvin.cli import Argument, CLIDispatcher
import json
import logging
from infernalis.core import get_deployer
import traceback

class InfernalisDispatcher(CLIDispatcher):
    description = 'Run a set of commands against an interactive prompt.'

    shared_args = [
        Argument('--config', required=True, help='The path to the rokkr config file.'),
        Argument('--region', default=None, help='The AWS region.  May be specified in the config file instead.'),
        Argument("-v", "--verbosity", dest="verbosity", action="count", default=0, help='How verbose rokkr should be.  More -v\'s, more verbose.')
    ]

    operation_info={
        'deploy':{
            'help':'Deploy a stack.'
        },
    }

    @classmethod
    def execute(cls, action, **kwargs):
        deployer = get_deployer(**kwargs)
        method = getattr(deployer, action)
        response = method(**kwargs)
        print(response)

class InfernalisDaemonDispatcher(CLIDispatcher):
    description = 'Spin up a long-lived Infernalis session.'

    shared_args = [
        Argument('--config', required=True, help='The path to the rokkr config file.'),
        Argument('--region', default=None, help='The AWS region.  May be specified in the config file instead.'),
        Argument("-v", "--verbosity", dest="verbosity", action="count", default=0, help='How verbose rokkr should be.  More -v\'s, more verbose.')
    ]

    operation_info={
        'deploy':{
            'help':'Deploy a stack.'
        },
    }

    @classmethod
    def execute(cls, action, **kwargs):
        deployer = get_deployer(**kwargs)
        method = getattr(deployer, action)
        response = method(**kwargs)
        print(response)

class InfernalisClientDispatcher(CLIDispatcher):
    description = 'Interact with a long-lived Infernalis daemon.'

    shared_args = [
        Argument('--config', required=True, help='The path to the rokkr config file.'),
        Argument('--region', default=None, help='The AWS region.  May be specified in the config file instead.'),
        Argument("-v", "--verbosity", dest="verbosity", action="count", default=0, help='How verbose rokkr should be.  More -v\'s, more verbose.')
    ]

    operation_info={
        'deploy':{
            'help':'Deploy a stack.'
        },
    }

    @classmethod
    def execute(cls, action, **kwargs):
        deployer = get_deployer(**kwargs)
        method = getattr(deployer, action)
        response = method(**kwargs)
        print(response)

