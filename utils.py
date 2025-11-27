import math

def calculate_arrow_points(x1, y1, x2, y2, arrow_size=10):
    """Calculates the points for an arrowhead at (x2, y2) pointing from (x1, y1)."""
    angle = math.atan2(y2 - y1, x2 - x1)
    
    # Arrowhead points
    p1_x = x2 - arrow_size * math.cos(angle - math.pi / 6)
    p1_y = y2 - arrow_size * math.sin(angle - math.pi / 6)
    
    p2_x = x2 - arrow_size * math.cos(angle + math.pi / 6)
    p2_y = y2 - arrow_size * math.sin(angle + math.pi / 6)
    
    return [x2, y2, p1_x, p1_y, p2_x, p2_y]

def point_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
