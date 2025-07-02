import math

from PySide6.QtGui import QColor, QBrush

from tools.arcs_view_position import place_words_on_annular_arcs
from tools.optimistation_position import resolve_collisions


def get_color(num_color, nb_color, shade, nb_shade):
    """
    Return color :
    - num_color : index de couleur (0 à total_colors - 1)
    - nb_color : nombre total de teintes différentes (réparties sur le cercle HSV)
    - shade : niveau de clarté (0 = clair, nb_shade-1 = foncé)
    - nb_shade : nombre total de niveaux d’ombre
    """
    hue = int(360 * num_color / nb_color)  # Teinte : répartition circulaire
    saturation = 80

    if nb_shade == 1:
        value = 255
    else:
        value = int(255 * (1 - shade / (3*nb_shade-1)))  # 255 → clair, 0 → foncé

    return QColor.fromHsv(hue, saturation, value)


def find_independent_key(dep_map):
    all_keys = set(dep_map.keys())
    all_dependencies = set()

    for deps in dep_map.values():
        all_dependencies.update(deps)

    independent_keys = all_keys - all_dependencies

    return next(iter(independent_keys), None)  # Retourne une clé ou None s'il n'y en a pas


def get_children(child, dep_map, visited=None):
    if visited is None:
        visited = set()

    if child in visited:
        return []

    visited.add(child)

    children = []
    for dep in dep_map.get(child, []):
        if dep not in visited:
            children.append(dep)
            children.extend(get_children(dep, dep_map, visited))

    return children



def update_representation(state_machine, graphics_scene):
    # Get semantics and graphics
    map_simple = state_machine.get_simple_graph()
    graphics_vertices = graphics_scene.get_vertices()
    element_to_update = []

    # Get root and children of root
    root_key = find_independent_key(map_simple)
    children = map_simple[root_key]
    step_angle = 360 / len(children)

    # Do not the job if not enough children
    if len(children) < 3:
        return

    # Init center
    graphics_vertices[root_key].set_vertex_gi([0, 0], [150, 150])
    graphics_vertices[root_key].setbackground_color(QColor(255, 255, 255))
    max_key_length = max(len(k) for k in graphics_vertices.keys())

    # Compute position of children
    dimension = [150, 150]
    radius = 200
    for num_child in range(0, len(children)):
        color = get_color(num_child, len(children), 1, 1)
        angle = (num_child + 0.5) * 360 / len(children)
        x = radius * math.cos(math.radians(angle))
        y = radius * math.sin(math.radians(angle))
        element_to_update.append([children[num_child], [x, y], dimension, color])

    # Init value for sub children
    radius_start = 300
    radius_end = 900
    nb_arcs = 7

    for num_child in range(0, len(children)):
        child = children[num_child]
        sub_children = get_children(child, map_simple)

        start_angle = num_child*step_angle
        end_angle = start_angle+step_angle
        positions = place_words_on_annular_arcs(start_angle, end_angle, radius_start, radius_end, sub_children, nb_arcs)

        for num_position in range(0, len(positions)):
            color = get_color(num_child, len(children), num_position, len(positions))
            position = positions[num_position]
            width = 50 + 150 * len(sub_children[num_position]) / max_key_length
            element_to_update.append([sub_children[num_position], position, [int(width), 50], color])

    # Met à jour les positions sans chevauchement
    new_positions = resolve_collisions(element_to_update)

    # Appliquer les nouvelles positions aux objets graphiques
    for element in element_to_update:
        vertex = graphics_vertices[element[0]]
        new_pos = new_positions[element[0]]
        vertex.set_vertex_gi(new_pos, element[2])  # (position, dimension)
        vertex.setbackground_color(element[3])

