import requests
import graphviz
import os
import sys
import argparse


def get_dependencies(package_name: str) -> list:
    """ Retrieves the dependencies of the current package, returns a list
        of the direct dependencies of the transmitted package without versions. """

    url = f"https://pypi.org/pypi/{package_name}/json"
    data = requests.get(url=url).json()

    try:
        if data['info']['requires_dist']:
            return parse_dependencies(data['info']['requires_dist'])
        else:
            return list()
    except KeyError:
        return list()


def parse_dependencies(dependencies: list) -> list:
    """ Truncates versions of the transmitted package list. """

    replace_list = ["(", ")", "[", "]", "'", '"']
    separators_list = [">", "<", ";", "!", "=", "~"]

    dependencies_without_versions = list()
    for dependency in dependencies:
        if 'extra' in dependency:
            continue

        for element in replace_list:
            dependency = dependency.replace(element, '')

        index = len(dependency)
        for separator in separators_list:
            alternative_index = dependency.find(separator)
            if alternative_index != -1:
                index = min(index, alternative_index)

        dependencies_without_versions.append(dependency[:index:].strip().lower())
    return dependencies_without_versions


def make_graph(dependencies: dict, package_name: str):
    """ Generates a graph in graphviz language based on the passed dictionary.
        The generated graph is a dependency tree of the package, which is the root. """

    graph = graphviz.Digraph(name=f'{package_name} package dependencies')

    for (key, value) in dependencies.items():
        graph.node(key)
        for lib in value:
            graph.edge(key, lib)

    graph.render(f'files/dependency_graphs/{package_name}_dependencies_graph.gv', view=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--extra", action="append", default=None)
    named_args = parser.parse_args(sys.argv[2:])

    try:
        name = sys.argv[1]
    except IndexError:
        exit("Package name wasn't given.")

    os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'
    libs_list = get_dependencies(name)

    dependencies_dict = dict()
    dependencies_dict[name] = set(libs_list)

    for lib in libs_list:
        dependencies_dict[lib] = set(get_dependencies(lib))
        for new_dependency in dependencies_dict[lib]:
            if new_dependency not in libs_list:
                libs_list.append(new_dependency)

    if len(libs_list) != 0:
        make_graph(dependencies_dict, name)


# python package_dependencies.py aiogram
if __name__ == '__main__':
    main()
