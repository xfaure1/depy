def resolve_collisions(elements, margin=5, max_iterations=1000):
    """
    Déplace légèrement les éléments pour qu'ils ne se chevauchent pas.
    - elements : liste de tuples (id, (x, y), (w, h), color)
    - margin : marge minimale à laisser entre les objets
    """
    from itertools import combinations

    positions = {e[0]: list(e[1]) for e in elements}  # id -> [x, y]
    sizes = {e[0]: e[2] for e in elements}           # id -> (w, h)

    def rects_overlap(r1, r2):
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2
        return not (x1 + w1 + margin <= x2 or
                    x2 + w2 + margin <= x1 or
                    y1 + h1 + margin <= y2 or
                    y2 + h2 + margin <= y1)

    for _ in range(max_iterations):
        moved = False
        for a, b in combinations(elements, 2):
            id1, id2 = a[0], b[0]
            x1, y1 = positions[id1]
            w1, h1 = sizes[id1]
            x2, y2 = positions[id2]
            w2, h2 = sizes[id2]

            if rects_overlap((x1, y1, w1, h1), (x2, y2, w2, h2)):
                # Calcul d'un petit déplacement
                dx = (x1 + w1 / 2) - (x2 + w2 / 2)
                dy = (y1 + h1 / 2) - (y2 + h2 / 2)

                # Évite déplacement nul
                if dx == 0 and dy == 0:
                    dx, dy = 1, 1

                norm = max((dx ** 2 + dy ** 2) ** 0.5, 1e-5)
                shift = 1.0  # déplacement minimal
                dx, dy = dx / norm * shift, dy / norm * shift

                positions[id1][0] += dx
                positions[id1][1] += dy
                positions[id2][0] -= dx
                positions[id2][1] -= dy
                moved = True
        if not moved:
            break

    return {id_: tuple(pos) for id_, pos in positions.items()}
