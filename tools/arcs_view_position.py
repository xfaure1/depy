import math

def sum_of_arc_lengths(start_angle_deg, end_angle_deg, start_radius, end_radius, number_of_arcs):
    """
    Calculate the total length of arcs placed between start_radius and end_radius
    on a circular segment defined by start_angle and end_angle (in degrees).

    Parameters:
    - start_angle_deg (float): Starting angle of the disk portion (in degrees)
    - end_angle_deg (float): Ending angle of the disk portion (in degrees)
    - start_radius (float): Inner radius
    - end_radius (float): Outer radius
    - number_of_arcs (int): Number of arcs to place between start_radius and end_radius

    Returns:
    - float: Total length of all arcs
    """
    if number_of_arcs <= 0 or start_radius < 0 or end_radius <= start_radius:
        raise ValueError("Invalid input parameters.")

    angle_rad = math.radians(end_angle_deg - start_angle_deg)
    radius_step = (end_radius - start_radius) / number_of_arcs

    total_length = 0.0
    for i in range(number_of_arcs):
        # Radius at this arc's position (e.g. at center of the ring)
        radius = start_radius + (i + 0.5) * radius_step
        arc_length = angle_rad * radius
        total_length += arc_length

    return total_length

def point_on_stacked_arcs(start_angle_deg, end_angle_deg, start_radius, end_radius, number_of_arcs, length_along_arcs):
    """
    Given a length along multiple stacked arcs (from inner to outer radius),
    return the (x,y) coordinate of the point on the "super arc".

    Parameters:
    - start_angle_deg (float): Start angle of the sector (degrees)
    - end_angle_deg (float): End angle of the sector (degrees)
    - start_radius (float): Inner radius
    - end_radius (float): Outer radius
    - number_of_arcs (int): Number of arcs stacked radially
    - length_along_arcs (float): Length traveled along the stacked arcs (<= total arcs length)

    Returns:
    - (x, y): Coordinates of the point on the arcs
    """

    if number_of_arcs <= 0:
        raise ValueError("Number of arcs must be positive")
    if start_radius < 0 or end_radius <= start_radius:
        raise ValueError("Invalid radius values")
    if length_along_arcs < 0:
        raise ValueError("Length along arcs must be non-negative")

    # Convert angles to radians
    angle_rad = math.radians(end_angle_deg - start_angle_deg)

    # Compute step in radius
    radius_step = (end_radius - start_radius) / number_of_arcs

    # Calculate lengths of each arc at mid-radius of each band
    arc_lengths = []
    for num_arc in range(number_of_arcs):
        radius = start_radius + (num_arc + 0.5) * radius_step
        arc_length = angle_rad * radius
        arc_lengths.append(arc_length)

    total_length = sum(arc_lengths)
    if length_along_arcs > total_length:
        raise ValueError(f"Length along arcs ({length_along_arcs}) exceeds total arcs length ({total_length})")

    # Find which arc the length_along_arcs falls into
    accumulate_length = 0
    for num_arc, current_arc_len in enumerate(arc_lengths):
        if accumulate_length + current_arc_len >= length_along_arcs:
            # length inside this arc
            length_inside_arc = length_along_arcs - accumulate_length
            ratio = length_inside_arc / current_arc_len
            radius = start_radius + (num_arc + 0.5) * radius_step
            local_angle_rad = angle_rad * ratio

            # Compute x,y position
            start_angle_rad = math.radians(start_angle_deg)
            my_angle = start_angle_rad + local_angle_rad
            x = radius * math.cos(my_angle)
            y = radius * math.sin(my_angle)
            return (x, y)

        accumulate_length += current_arc_len

    # If we reach here, length_along_arcs == total_length exactly
    # Return the end point of the last arc
    radius = start_radius + (number_of_arcs - 0.5) * radius_step
    x = radius * math.cos(math.radians(end_angle_deg))
    y = radius * math.sin(math.radians(end_angle_deg))
    return (x, y)

def place_words_on_annular_arcs(start_angle, end_angle, start_radius, end_radius, words, num_arcs):

    sum_arc_lengths = sum_of_arc_lengths(start_angle, end_angle, start_radius, end_radius, num_arcs)
    sum_letters = sum(len(word) for word in words)
    nb_letters = 0
    results = []

    for word in words:

        middle = len(word) / 2.0
        current_length = sum_arc_lengths * (nb_letters + middle) / sum_letters

        pt = point_on_stacked_arcs(start_angle, end_angle, start_radius, end_radius, num_arcs, current_length)

        results.append(pt)

        nb_letters += len(word)

    return results

