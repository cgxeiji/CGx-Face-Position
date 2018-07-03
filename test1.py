from __future__ import print_function
from libs.configurator import Configurator

def main():
    config = Configurator()
    config.load('config/poses.ini')
    
    for section in config.sections:
        print(section)

    config.parse('a', 'b', 'c')

if __name__ == "__main__":
    main()
