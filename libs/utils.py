from __future__ import print_function
import ConfigParser
import logging

class Smoother:
    def __init__(self, size=3):
        self.size = size
        self.buffer = [0] * self.size

    def input(self, value):
        self.buffer.append(value)
        self.buffer.pop(0)

    def set(self, value):
        self.buffer = []
        for i in range(self.size):
            self.buffer.append(value)

    def value(self):
        return sum(self.buffer) / len(self.buffer)

def get_config_variable(name, type=''):
    config = ConfigParser.ConfigParser()
    config.read('config/global.ini')

    if type == '':
        for section in config.sections():
            if name in config.options(section):
                if config.get(section, name) == '':
                    break
                logging.info('config_parser->{}, {}'.format(name, config.get(section, name)))
                return config.get(section, name)

        logging.info('config_parser->{}, {}'.format(name, 'None'))
        return None

    try:
        variable = get_config_variable(name).strip()
        if type == 'int':
            return int(variable)
        if type == 'float':
            return float(variable)
        if type == 'string':
            return str(variable)
        if type == 'bool':
            if variable.lower() == 'true':
                return True
            else:
                return False
    except:
        return None