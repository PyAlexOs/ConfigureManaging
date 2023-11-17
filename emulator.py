from getpass import getuser
from socket import gethostname
import zipfile
import sys


def get_files(filesysytem: zipfile.ZipFile, current_path: str) -> dict:
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
    data = get_files(filesystem, current_path)
    c = 0
    for entity in data['entities']:
        c += 1
        sys.stdout.write(entity + (" " * (data['length'] - len(entity) + 4)))
        if c >= data['per_line']:
            c = 0
            sys.stdout.write('\n')

    sys.stdout.write('\n')


def get_path(data: dict, current_path: str, path: str) -> str:
    default = current_path
    for level in path.split("/"):
        if level in data['entities']:
            current_path += "/" + level
            data = get_files(filesystem, current_path)
        else:
            current_path = default
            break

    return current_path


def cd(filesystem: zipfile.ZipFile, current_path: str, path: str) -> str:
    if path.startswith(".."):
        return cd(filesystem, '/'.join(current_path.strip("/").split("/")[:-1:]), path[2::])

    elif path.startswith("~/"):
        return cd(filesystem, '', path[2::])

    else:
        if path.startswith("/"):
            data = get_files(filesystem, '')
            current_path = ''
        else:
            if path.startswith("."):
                path = path[1::]
            if path.startswith("/"):
                path = path[1::]
            data = get_files(filesystem, current_path)

    return get_path(data, current_path, path)


def cat(filesystem: zipfile.ZipFile, current_path: str, args: list):
    for filename in args[1::]:
        filepath = cd(filesystem, current_path, filename)
        if filepath != current_path:    # Путь к искомому файлу найден, а не сброшен
            file = filesystem.open(filepath.strip("/"), 'r')

            while line := file.readline():
                sys.stdout.write(line.decode())
            sys.stdout.write("\n")
            file.close()
        else:
            sys.stdout.write("File not found.\n")


#  D:/MIREA/ConfigureManaging/files/archive.zip
if __name__ == '__main__':
    try:
        filepath = sys.argv[1]  # [0] stands for program
    except IndexError as e:
        # exit("File system image path wasn't given.")
        filepath = "D:/MIREA/ConfigureManaging/files/archive.zip"

    if not zipfile.is_zipfile(filepath):
        exit("File system image not found.")

    filesystem = zipfile.ZipFile(filepath)
    current_path = ''

    args = input(f'{getuser()}@{gethostname()}:~{current_path}$ ').split(' ')
    while args[0] != 'exit':
        if args[0] == 'pwd':
            sys.stdout.write(f'{filepath.split("/")[-1].split(".")[0]}/{getuser()}{current_path}\n')
        elif args[0] == 'ls':
            ls(filesystem, current_path)
        elif args[0] == 'cd':
            current_path = cd(filesystem, current_path, args[1])
        elif args[0] == 'cat':
            cat(filesystem, current_path, args)

        args = input(f'{getuser()}@{gethostname()}:~{current_path}$ ').split(' ')
    filesystem.close()
