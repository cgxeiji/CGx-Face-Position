from __future__ import print_function
import ConfigParser

config = ConfigParser.ConfigParser()
print(config)
config.read('poses.ini')
print(config.sections())
for section in config.sections():
    print(section)
    print(config.options(section))