from getpass import getuser
from socket import gethostname
import sys
import zipfile
import argparse


def get_files(filesystem: zipfile.ZipFile, current_path: str) -> dict:
    """ Returns a dictionary containing the names of all files and folders
        in the current directory, the hierarchy level of the current directory,
        the maximum length of the file name in the current directory, the number
        of file names that can be output in one line, taking into account the
        alignment and the maximum length of the file name. """

    name_length = 1
    hierarchy_level = len(current_path.strip("/").split("/"))
    if len(current_path.strip("/")) == 0:
        hierarchy_level = 0

    entities = set()
    for entity in filesystem.filelist:
        try:
            name = entity.filename.strip("/").split("/")[hierarchy_level]
            if current_path.strip("/") in entity.filename:
                entities.add(name)
                if len(name) > name_length:
                    name_length = len(name)
        except IndexError:
            # current path could be shorter than path we're searching for
            pass

    per_line = 80 / (name_length + 4)
    return {'level': hierarchy_level,
            'length': name_length,
            'per_line': per_line,
            'entities': entities}


def ls(filesystem: zipfile.ZipFile, current_path: str):
    """ Displays all files and folders in the current directory. """

    data = get_files(filesystem, current_path)
    c = 0
    for entity in sorted(data['entities']):
        c += 1
        sys.stdout.write(entity + (" " * (data['length'] - len(entity) + 4)))
        if c >= data['per_line']:
            c = 0
            sys.stdout.write("\n")
    sys.stdout.write("\n")


def get_path(filesystem: zipfile.ZipFile, data: dict, current_path: str, path: str) -> str:
    """ Tries to get to the path from the current_path, if there is no such path,
        returns the path passed as an argument. """

    default = current_path
    for level in path.strip("/").split("/"):
        if level in data['entities']:
            current_path += "/" + level
            data = get_files(filesystem, current_path)
        else:
            current_path = default
            break

    return current_path


def cd(filesystem: zipfile.ZipFile, current_path: str, path: str) -> str:
    """ Returns the updated path. """

    if path.startswith(".."):
        path = path[2::]
        if path.startswith("/"):
            path = path[1::]
        parent_directory = current_path.strip("/").split("/")[:-1:]
        return cd(filesystem, "/" + '/'.join(parent_directory) if len(parent_directory) != 0 else "", path)

    elif path.startswith("~/") or path.startswith("/"):
        if path.startswith("~/"):
            path = path[1::]
        return get_path(filesystem, get_files(filesystem, ''), '', path[1::])

    else:
        if path.startswith("."):
            path = path[1::]
            if path.startswith("/"):
                path = path[1::]

        return get_path(filesystem, get_files(filesystem, current_path), current_path, path)


def cat(filesystem: zipfile.ZipFile, current_path: str, args: list):
    """ Outputs the contents of the files passed as arguments. """

    for filename in args[1::]:
        filepath = cd(filesystem, current_path, filename)
        if filepath != current_path:    # File found, the filepath wasn't set to default
            file = filesystem.open(filepath.strip("/"), 'r')

            while line := file.readline():
                sys.stdout.write(line.decode())
            sys.stdout.write("\n")
            file.close()
        else:
            sys.stdout.write("File not found.\n")


def get_filesystem(filename: str) -> zipfile.ZipFile:
    """ Returns a zipfile.ZipFile object if a file system image exists along the passed path. """

    if not zipfile.is_zipfile(filename):
        exit("File system image not found.")

    return zipfile.ZipFile(filename)


def execute_console(filepath: str):
    """ Reads commands from the console and sends them for processing. """

    filesystem = get_filesystem(filepath)
    current_path = ''
    args = input(f'{getuser()}@{gethostname()}:~{current_path}$ ').split(' ')
    while args[0] != 'exit':
        current_path = shell(args, filesystem, current_path)
        args = input(f'{getuser()}@{gethostname()}:~{current_path}$ ').split(' ')
    filesystem.close()


def execute_script(filepath: str, script_filename: str):
    """ Reads commands from a file and sends them for processing. """

    filesystem = get_filesystem(filepath)
    current_path = ''
    with open(script_filename, 'r') as script:
        while line := script.readline().strip('\n'):
            sys.stdout.write(f'{getuser()}@{gethostname()}:~{current_path}$ ' + line + "\n")
            current_path = shell(line.split(' '), filesystem, current_path)
    filesystem.close()


def shell(args: list, filesystem: zipfile.ZipFile, current_path: str) -> str:
    """ Processes the passed commands and returns the modified current path. """

    if args[0] == 'pwd':
        sys.stdout.write(f'{filesystem.filename.split("/")[-1].split(".")[0]}/{getuser()}{current_path}\n')
    elif args[0] == 'ls':
        ls(filesystem, current_path)
    elif args[0] == 'cd':
        current_path = cd(filesystem, current_path, args[1] if len(args) > 1 else ".")
    elif args[0] == 'cat':
        cat(filesystem, current_path, args)

    return current_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--script", default=None)
    named_args = parser.parse_args(sys.argv[2:])

    try:
        filepath = sys.argv[1]  # [0] stands for program-name
    except IndexError:
        exit("File system image path wasn't given.")

    if named_args.script:
        execute_script(filepath, named_args.script)
    else:
        execute_console(filepath)


# python emulator.py files/emulator_files/archive.zip --script files/emulator_files/test_script.txt
if __name__ == '__main__':
    main()
