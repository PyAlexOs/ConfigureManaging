import requests
import graphviz
import os
from threading import Thread


def get_dependencies(package_name: str) -> list:
    url = f"https://pypi.org/pypi/{package_name}/json"
    data = requests.get(url=url).json()

    try:
        if data['info']['requires_dist']:
            return data['info']['requires_dist']
        else:
            return list()
    except KeyError or ValueError:
        return list()


def erase_version(dependencies: list) -> list:
    dependencies_without_versions = list()
    for dependency in dependencies:
        dependency = dependency.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
        indexes = [dependency.find('>') if dependency.find('>') != -1 else len(dependency),
                   dependency.find('<') if dependency.find('<') != -1 else len(dependency),
                   dependency.find(';') if dependency.find(';') != -1 else len(dependency),
                   dependency.find('!') if dependency.find('!') != -1 else len(dependency),
                   dependency.find('=') if dependency.find('=') != -1 else len(dependency),
                   dependency.find('~') if dependency.find('~') != -1 else len(dependency)]

        dependencies_without_versions.append(dependency[:min(indexes):].strip().strip('"').lower())
    return dependencies_without_versions


def make_graph(dependencies: dict, package_name: str):
    graph = graphviz.Digraph(name=f'Package dependencies {package_name}')

    for (key, value) in dependencies.items():
        graph.node(key)
        for lib in value:
            graph.node(lib)
            graph.edge(key, lib)

    graph.render(f'files/dependency_graphs/{package_name}_dependencies_graph.gv', view=True)


if __name__ == '__main__':
    os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'
    name = input('Enter the library name: ')
    libs_list = erase_version(get_dependencies(name))

    dependencies_dict = dict()
    dependencies_dict[name] = list(libs_list)

    for lib in libs_list:
        dependencies_dict[lib] = list(set(erase_version(get_dependencies(lib))))
        t = Thread(target=get_dependencies, args=lib)
        for new_dependency in dependencies_dict[lib]:
            if new_dependency not in libs_list:
                print(new_dependency)
                libs_list.append(new_dependency)

    make_graph(dependencies_dict, name)
    for (key, value) in dependencies_dict.items():
        print(key, value)
