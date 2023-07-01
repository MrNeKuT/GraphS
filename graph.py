import itertools
import matplotlib.pyplot as plt
import networkx as nx
import re
import string

from collections import Counter
from multipledispatch import dispatch
from networkx.classes.graph import NodeView
from networkx.classes.graph import Graph
from operator import itemgetter
from pprint import pprint
from pyvis.network import Network
from random import randint, choice


def no_main():
    def sys_view(nodes: NodeView, edges_num: int, types: list) -> None:
        types_num = Counter([g.nodes[n]["group"] for n in g.nodes])
        assert sum(types_num.values()) == len(nodes)

        print(f'Количество узлов сети: {len(nodes)};\n' + \
              f'Количество ребер сети: {edges_num};\n' + \
              f'Количество типов узлов:')
        for row, value in dict(sorted(types_num.items(), key=itemgetter(1), reverse=True)).items():
            print(f'\t{row}: {value}')

        print(f'Общее: {len(types)}.')

    def get_route_types(routes: list):
        route_types = []
        for route in routes:
            for part_idx in range(len(route) - 1):
                if route[part_idx][0] < route[part_idx + 1][0]:
                    route_types.append(route[part_idx][1] + '-' + route[part_idx + 1][1])
                else:
                    route_types.append(route[part_idx + 1][1] + '-' + route[part_idx][1])
        return Counter(route_types)

    def generate_few_routes(num_of_routes: int, _graph: Graph) -> (list, Counter):
        # unused_nodes = [_node for _node in _graph.nodes]
        routes = []
        node_types_in_route = []
        # route_types = []
        print(f'Число генерируемых маршрутов: {num_of_routes}')
        for _ in range(num_of_routes):
            route = []
            num_route_nodes = randint(4, 10)
            while len(route) < num_route_nodes:
                if not route:
                    # noda = choice(unused_nodes)
                    noda = choice(list(_graph.nodes))
                else:
                    noda = choice(list(_graph.neighbors(route[-1][0])))
                    # while noda not in unused_nodes:
                    #     noda = choice(list(_graph.neighbors(route[-1][0])))

                # unused_nodes.remove(noda)
                route.append(
                    (noda, _graph.nodes[noda]['group']))

            # print(route)
            # for part_idx in range(len(route) - 1):
            #     if route[part_idx][0] < route[part_idx + 1][0]:
            #         route_types.append(route[part_idx][1] + '-' + route[part_idx + 1][1])
            #     else:
            #         route_types.append(route[part_idx + 1][1] + '-' + route[part_idx][1])

            routes.append(route)
            node_types_in_route.append(_graph.nodes[noda]['group'])

        route_types = get_route_types(routes)
        return routes, route_types

    @dispatch(list, int)
    def del_node_from_routes(routes: list, node: int) -> list:
        c = 0
        modified_routes = []
        for route in routes:
            modified_route = [_node for _node in route if _node[0] != node]
            modified_routes.append(modified_route)
            if len(route) != len(modified_route):
                c += 1

        print(f'Узел ({node}) удален из {c} {"целевых маршрутов" if c != 1 else "целевого маршрута"}.')
        return modified_routes

    @dispatch(list, list)
    def del_node_from_routes(routes: list, nodes: list) -> list:
        print_nodes = list(reversed(nodes))
        modified_routes = []
        for route in routes:
            c = 0
            modified_route = [_node for _node in route if _node[0] not in nodes]
            modified_routes.append(modified_route)
            deleted_num = len(route) - len(modified_route)
            if len(route) != len(modified_route):
                c += 1
                for _ in range(deleted_num):
                    if print_nodes:
                        print(
                            f'Узел ({print_nodes.pop()}) удален из {c} {"целевых маршрутов" if c != 1 else "целевого маршрута"}.')
        return modified_routes

    def get_critical_nodes(_graph: Graph, target_routes: list) -> dict:
        critical_nodes = {}
        for route in routes:
            for node in route:
                if critical_nodes.get(node[0]) is None:
                    critical_nodes[node[0]] = 1
                else:
                    critical_nodes[node[0]] += 1
        return critical_nodes

    def route_types_difference(route_types1: dict, route_types2: dict) -> dict:
        difference_route_types = {}
        for route_type, type_num in route_types1.items():
            if route_type not in route_types2.keys():
                difference_route_types[route_type] = 0
            else:
                if route_types2[route_type] <= route_types1[route_type]:
                    difference_route_types[route_type] = route_types2[route_type]
                else:
                    difference_route_types[route_type] = route_types1[route_type]
        return difference_route_types
        pass

    def closeness_centrality_criticality(_graph: Graph) -> dict:
        """
        Вычисляет критичность каждого узла графа G с помощью центральности по близости (closeness centrality)
        и возвращает словарь с узлами и их критичностью.
        """
        # Вычисляем центральность по близости для каждого узла графа
        closeness = nx.closeness_centrality(_graph)

        # Сортируем узлы по убыванию критичности
        sorted_nodes = sorted(closeness.items(), key=lambda x: x[1], reverse=True)

        # Создаем словарь с узлами и их критичностью
        node_criticality = {}
        for node, closeness_centrality in sorted_nodes:
            node_criticality[node] = closeness_centrality

        node_criticality = dict(sorted(node_criticality.items(), key=itemgetter(1), reverse=True))
        print(node_criticality)
        return node_criticality

    def critical_scoring(g: Graph,
                         routes: list,
                         critical_score: dict = None,
                         templ_path: str = './templates/nx_rr.html',
                         prefix: str = '',
                         mode: int = 1) -> None:
        """

        :param g:
        :param routes:
        :param templ_path:
        :param prefix:
        :param mode: mode=1 - классические пп.4-7; mode=2 - альтернативный вариант расчета критичности узлов
        :return:

        """
        critical_nodes = get_critical_nodes(g, routes)
        if mode == 1:
            print(dict(sorted(critical_nodes.items(), key=itemgetter(1), reverse=True)))

        COLORS = {0: '#B0BBB8', 1: '#26C72D', 2: '#ECEF32', 3: '#D86C0C', 4: '#FF0000'}
        COLORS_MY = {0: '#B0BBB8', 0.65: '#B0BBB8', 0.67: '#ECEF32', 0.69: '#D86C0C', 0.705: '#FF0000'}
        default_color = '#B0BBB8'

        node_colors = nx.get_node_attributes(g, 'color')
        for node in node_colors.keys():
            if mode == 1:
                if node in critical_nodes.keys():
                    if critical_nodes[node] <= 3:
                        node_colors[node] = COLORS[critical_nodes[node]]
                    else:
                        node_colors[node] = COLORS[4]
                else:
                    node_colors[node] = default_color
            else:
                if node in critical_score.keys():
                    if critical_score[node] <= .65:
                        node_colors[node] = COLORS_MY[.65]
                    elif (critical_score[node] > .65) and (critical_score[node] <= .67):
                        node_colors[node] = COLORS_MY[.67]
                    elif (critical_score[node] > .67) and (critical_score[node] <= .69):
                        node_colors[node] = COLORS_MY[.69]
                    else:
                        node_colors[node] = COLORS_MY[.705]
                else:
                    node_colors[node] = default_color
                # critical_score

        # Make the pyvis graph object
        net_rr = Network('800px', notebook=True, select_menu=True, cdn_resources='remote', filter_menu=True)
        # Turn on physics
        net_rr.barnes_hut()
        # ToolMenu to bottom
        net_rr.show_buttons(filter_=['nodes'])
        net_rr.add_nodes(list(g.nodes),
                         label=[g.nodes[n]['label'] for n in g.nodes],
                         title=[f"{g.nodes[n]['label']}, {g.nodes[n]['group']}" for n in g.nodes],
                         # color=[rr_edge_colors[_node] if _node in rr_edge_colors.keys() else default_color for _node in g.nodes]
                         color=node_colors
                         # x=[pos[0] for pos in positions.values()],
                         # y=[pos[1] for pos in positions.values()])
                         )
        net_rr.add_edges(g.edges)
        net_rr.show(templ_path)

        # Save PNG critical nodes histogram
        if mode == 1:
            fig, ax = plt.subplots(figsize=(25, 10))
            sorted_critical_nodes = dict(sorted(critical_nodes.items(), key=itemgetter(1), reverse=True))
            sorted_critical_nodes = dict(itertools.islice(sorted_critical_nodes.items(), 10))
            # sorted_critical_nodes = dict(sorted(critical_nodes.items(), key=itemgetter(0)))
            x_bar = [f"{g.nodes[n]['label']}, {g.nodes[n]['group']}" for n in sorted_critical_nodes.keys()]
            # x_bar = list(map(str, sorted_critical_nodes.keys()))
            ax.bar(x_bar, sorted_critical_nodes.values())
            plt.xticks(rotation=45)
            # ax.bar(list(map(str, sorted_critical_nodes.keys())), sorted_critical_nodes.values())
            # giving X and Y labels
            plt.xlabel("ID нод")
            plt.ylabel("Количество вхождений в целевые маршруты")
            plt.savefig(f"./graph/Critic_hist_2{prefix}.png", format="PNG")
        else:
            after_critical_score = critical_score
            fig, ax = plt.subplots(figsize=(25, 10))
            critical_score = dict(itertools.islice(critical_score.items(), 10))
            x_bar = [f"{g.nodes[n]['label']}, {g.nodes[n]['group']}" for n in critical_score.keys()]
            ax.bar(x_bar, critical_score.values())
            plt.xticks(rotation=45)
            plt.xlabel("ID ноды")
            plt.ylabel("Коэффициент критичности узла")
            plt.savefig(f"./graph/Critic_hist_2{prefix}.png", format="PNG")

        if mode == 1:
            node_variants_noncrit = [key for key, value in critical_nodes.items() if value < 2]
        else:
            limited_critical_score = {}
            for route in routes:
                for node in route:
                    limited_critical_score[node[0]] = after_critical_score[node[0]]
            node_variants_noncrit = list(limited_critical_score.keys())
        node_variants_noncrit.sort()
        node_variants_noncrit = list(map(str, node_variants_noncrit))
        # one_arg = int(input(f'Введите номер узла для удаления ({",".join(node_variants_noncrit)})\n>> '))
        # modified_routes = del_node_from_routes(routes, one_arg)
        # pprint(modified_routes)

        many_args = list(map(int, input(
            f'Введите номер(а) 10 НЕ критичных узлов для удаления({",".join(node_variants_noncrit)})\n>> ').split(
            sep=' ')))
        modified_routes = del_node_from_routes(routes, many_args)
        pprint(modified_routes)

        modified_route_types = get_route_types(modified_routes)
        difference_route_types = route_types_difference(route_types, modified_route_types)
        # print(modified_route_types)
        print('Оценка количества маршрутов каждого типа:')
        for idx, (route_type, type_num) in enumerate(difference_route_types.items(), 1):
            print(f'{idx}, {route_type}: {type_num}')

        # critical_nodes = get_critical_nodes(g, routes)
        # print(critical_nodes)

        """

        GRAPH PLOTTING # 2 (5-6)

        """

        # Save PNG critical routes histogram 2
        fig, ax = plt.subplots(figsize=(25, 12))
        x_bar, h_values = list(difference_route_types.keys()), list(difference_route_types.values())
        ax.bar(x_bar, h_values)
        plt.title('Количество маршрутов каждого типа после удаления 3 критичных узлов', fontdict={'fontsize': 24,
                                                                                                  'fontweight': 'bold'})
        plt.xticks(rotation=45)
        plt.xlabel("Типа маршрута")
        plt.ylabel("Количество вхождений в целевые маршруты")
        plt.ylim(0, y_route_type_max + .2)
        plt.savefig(f"./graph/Critic_hist_1_2{prefix}.png", format="PNG")

        if mode == 1:
            node_variants_crit = [key for key, value in critical_nodes.items() if value > 1]
        else:
            node_variants_crit = list(critical_score.keys())
        node_variants_crit.sort()
        node_variants_crit = list(map(str, node_variants_crit))
        # one_arg = int(input(f'Введите номер узла для удаления ({",".join(node_variants_noncrit)})\n>> '))
        # modified_routes = del_node_from_routes(routes, one_arg)
        # pprint(modified_routes)

        many_args = list(map(int, input(
            f'Введите номер(а) 3 критичных узлов для удаления({",".join(node_variants_crit)})\n>> ').split(sep=' ')))
        modified_routes = del_node_from_routes(routes, many_args)
        pprint(modified_routes)

        modified_route_types = get_route_types(modified_routes)
        difference_route_types = route_types_difference(route_types, modified_route_types)
        # print(modified_route_types)
        print('Оценка количества маршрутов каждого типа:')
        for idx, (route_type, type_num) in enumerate(difference_route_types.items(), 1):
            print(f'{idx}, {route_type}: {type_num}')

        """

            GRAPH PLOTTING # 3 (7-8)

        """

        # Save PNG critical routes histogram 2
        fig, ax = plt.subplots(figsize=(25, 12))
        x_bar, h_values = list(difference_route_types.keys()), list(difference_route_types.values())
        ax.bar(x_bar, h_values)
        plt.title('Количество маршрутов каждого типа после удаления 10 НЕ критичных узлов', fontdict={'fontsize': 24,
                                                                                                      'fontweight': 'bold'})
        plt.xticks(rotation=45)
        plt.xlabel("Типа маршрута")
        plt.ylabel("Количество вхождений в целевые маршруты")
        plt.ylim(0, y_route_type_max + .2)
        plt.savefig(f"./graph/Critic_hist_1_3{prefix}.png", format="PNG")

    _uppers = list(string.ascii_uppercase)
    TYPO_LIST = ['TYPE_' + type_let for type_let in \
                 [_uppers.pop() for _ in range(randint(10, 20))]]

    node_num = randint(80, 120)
    # Generate renyi graph
    g = nx.erdos_renyi_graph(node_num, 0.5)
    # Set fixed positions to nodes
    positions = nx.kamada_kawai_layout(g)

    NUM_EDGES = len(g.edges)

    # Set attrs to graph`s nodes
    for node in g.nodes:
        g.nodes[node]['label'] = str(node)
        g.nodes[node]['group'] = choice(TYPO_LIST)
        g.nodes[node]['color'] = '#23A8FA'

    # Make the pyvis graph object
    net = Network('800px', notebook=True, select_menu=True, cdn_resources='remote', filter_menu=True)
    # Turn on physics
    net.barnes_hut()
    # ToolMenu to bottom
    net.show_buttons(filter_=['nodes'])
    net.add_nodes(list(g.nodes),
                  label=[g.nodes[n]['label'] for n in g.nodes],
                  title=[f"{g.nodes[n]['label']}, {g.nodes[n]['group']}" for n in g.nodes],
                  # color=[g.nodes[n]['color'] for n in g.nodes],
                  # x=[pos[0] for pos in positions.values()],
                  # y=[pos[1] for pos in  positions.values()])
                  )
    net.add_edges(g.edges)

    # net.write_html('./templates/nx.html') # alternative .show()
    # Save visualization in 'graph.html'
    net.show('./templates/nx.html')

    # Print info about Graph
    sys_view(g.nodes, NUM_EDGES, TYPO_LIST)
    # print(nx.get_node_attributes(g))
    routes, route_types = generate_few_routes(randint(3, 7), g)
    # route_types = Counter(route_types)
    pprint(routes)

    print('Оценка количества маршрутов каждого типа:')
    for idx, route_type in enumerate(route_types, 1):
        print(f'{idx}, {route_type}: {route_types[route_type]}')

    """
    # Save graph
    nx.write_gexf(g, './graph/graph.gexf')
    # Read graph
    H = nx.read_gexf('./graph/graph.gexf')
    positions = nx.kamada_kawai_layout(H)
    """

    """
    
    GRAPH PLOTTING # 1 (1)
    
    """
    # Save PNG graph
    nx.draw(g, pos=positions, labels=nx.get_node_attributes(g, 'label'), font_size=11, font_color="lime")
    plt.savefig("./graph/Graph.png", format="PNG")

    # Save PNG critical routes histogram 1
    fig, ax = plt.subplots(figsize=(25, 12))
    x_bar, h_values = list(route_types.keys()), list(route_types.values())
    ax.bar(x_bar, h_values)
    y_route_type_max = max(list(route_types.values()))
    plt.title('Количество маршрутов каждого типа', fontdict={'fontsize': 24,
                                                             'fontweight': 'bold'})
    plt.xticks(rotation=45)
    plt.xlabel("Типа маршрута")
    plt.ylabel("Количество вхождений в целевые маршруты")
    plt.ylim(0, y_route_type_max + .2)
    plt.savefig("./graph/Critic_hist_1.png", format="PNG")

    critical_scoring(g=g, routes=routes)

    centrality_criticality = closeness_centrality_criticality(g)
    print('Альтернативная оценка критичности узлов по критерию Центральность по близости')

    critical_scoring(g=g,
                     routes=routes,
                     critical_score=centrality_criticality,
                     templ_path='./templates/nx_rr_my.html',
                     prefix='_1',
                     mode=2)

    with open('./templates/nx.html', 'r') as file:
        pattern = '<p align="right"><a href="http://localhost:5000/random-routes" title="random-routes">Next page >></a></p>'
        data = ''.join(file.readlines())
        nx_html = re.sub(r'</script>\W*</body>', f'</script>\n\t\t{pattern}\n\t</body>', data)
        with open('./templates/nx.html', 'w') as ffile:
            ffile.write(nx_html)


if __name__ == '__main__':
    no_main()
    pass
