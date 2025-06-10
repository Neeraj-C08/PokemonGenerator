import numpy as np
import pygame

# Re-defining the array generation function for self-containment
def create_random_binary_2d_array(rows, cols, probability_of_one=0.5):
    """
    Creates a 2D array (matrix) of specified dimensions, filled with random 1s and 0s.

    Args:
        rows (int): The number of rows in the array.
        cols (int): The number of columns in the array.
        probability_of_one (float): The probability (between 0 and 1) that
                                    a cell will contain a 1. Default is 0.5 (50%).

    Returns:
        numpy.ndarray: A 2D array filled with 1s and 0s.
    """
    if not (0 <= probability_of_one <= 1):
        print("Error: probability_of_one must be between 0 and 1.")
        return None

    random_array = np.random.rand(rows, cols)
    binary_array = (random_array <= probability_of_one).astype(int)
    return binary_array

def run_pygame_visualizer():
    """
    Initializes Pygame, generates a 2D binary array, and displays it
    as white (1s) and black (0s) squares in a Pygame window.
    """
    # --- Configuration ---
    ARRAY_ROWS = 50  # Number of rows in the 2D array
    ARRAY_COLS = 50  # Number of columns in the 2D array
    PROBABILITY_OF_ONE = 0.7  # 70% chance for a cell to be 1

    # Window dimensions (adjust as needed, squares will scale)
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 800
    CAPTION = "Randomized Binary Array Visualizer"

    # Colors
    BLACK = (0, 0, 0)      # For 0s
    WHITE = (255, 255, 255) # For 1s

    # --- Generate the 2D array ---
    binary_grid = create_random_binary_2d_array(ARRAY_ROWS, ARRAY_COLS, PROBABILITY_OF_ONE)

    if binary_grid is None:
        print("Failed to generate the binary grid. Exiting Pygame visualizer.")
        return

    # --- Pygame Initialization ---
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(CAPTION)

    # Calculate square size dynamically
    # This ensures the grid fills the window
    square_width = SCREEN_WIDTH // ARRAY_COLS
    square_height = SCREEN_HEIGHT // ARRAY_ROWS

    # If the squares are not perfectly divisible, there might be a small border/padding,
    # or the last row/column might be slightly cut off.
    # For a perfect fit, you could make SCREEN_WIDTH and SCREEN_HEIGHT
    # multiples of ARRAY_COLS and ARRAY_ROWS respectively.

    # --- Game Loop ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear the screen (optional, as we redraw everything)
        screen.fill(BLACK) # Fill with black before drawing

        # Draw the grid
        for row_idx in range(ARRAY_ROWS):
            for col_idx in range(ARRAY_COLS):
                # Determine the color based on the array value
                color = WHITE if binary_grid[row_idx, col_idx] == 1 else BLACK

                # Calculate the position and size of the square
                left = col_idx * square_width
                top = row_idx * square_height
                rect = pygame.Rect(left, top, square_width, square_height)

                # Draw the rectangle
                pygame.draw.rect(screen, color, rect)

        # Update the display to show the newly drawn elements
        pygame.display.flip()

    # --- Quit Pygame ---
    pygame.quit()
    print("Pygame visualizer closed.")

# Run the visualizer when the script is executed
if __name__ == "__main__":
    run_pygame_visualizer()