import sys

from .window import MainWindow


def annotate(dir_path):
    MainWindow.run(dir_path)


def execute_from_cmd():
    args = sys.argv[1:]
    if not len(args):
        raise ValueError('Command was not provided')
    func = globals()[args[0]]
    func_args = args[1:]
    func(*func_args)
