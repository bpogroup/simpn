"""
Visual constants and configuration for the visualization system.

This module defines colors, sizes, and other visual parameters used throughout
the visualization components to maintain consistent appearance.

Constants are organized into:
- Screen/Display: Maximum sizes and dimensions
- Colors: TU/e brand colors and standard colors
- Sizes: Node dimensions, line widths, text sizes, etc.
"""

# Screen size
MAX_SIZE = 1920, 1080  # Maximum display resolution

# TU/e Brand Colors
TUE_RED = (200, 25, 25)           # Primary TU/e red
TUE_LIGHTRED = (249, 204, 204)    # Light red for highlights
TUE_BLUE = (16, 16, 115)          # Primary TU/e blue
TUE_LIGHTBLUE = (188, 188, 246)   # Light blue for highlights and backgrounds
TUE_GREY = (242, 242, 242)        # Light grey for backgrounds

# Standard Colors
WHITE = (255, 255, 255)
GREEN = (0, 159, 107)

# Node Sizes
STANDARD_NODE_WIDTH, STANDARD_NODE_HEIGHT = 50, 50  # Default node dimensions in pixels

# Line and Border Properties
LINE_WIDTH = 2                    # Width for drawing edges and borders
ARROW_WIDTH, ARROW_HEIGHT = 12, 10  # Arrowhead dimensions for edges

# Text Properties
TEXT_SIZE = 16                    # Default font size for node labels

# UI Element Positions
BUTTON_POSITION = (16, 16)        # Default position for UI buttons
BUTTON_SIZE = (50, 50)            # Default button dimensions
