import sys

from deceptgold.helper.opencanary.help_opencanary import start_opencanary_internal

def main(parametro=None):
    start_opencanary_internal(parametro)

if __name__ == "__main__":
    parametro = sys.argv[1] if len(sys.argv) > 1 else None
    main(parametro)