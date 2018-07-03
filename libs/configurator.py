from __future__ import print_function
import configparser
import logging

class Configurator:
    def __init__(self):
        self.sections = {}
        self.sections_data = []

    def load(self, file_path):
        config = configparser.ConfigParser()
        config.read(file_path)
        for section in config.sections():
            self.sections[section] = config.items(section)

    def parse(self, *argv):
        for value in argv:
            print(value)
