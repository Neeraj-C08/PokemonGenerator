import numpy as np
import pygame


# Re-defining the array generation function for self-containment
def main_game_array(rows, cols, probability_of_one=0.5):
    if not (0 <= probability_of_one <= 1):
        print("change probability of generating 1's ")
        return None

    random_array = np.random.rand(rows, cols)
    binary_array = (random_array <= probability_of_one).astype(int)
    return binary_array


def run_pygame_visualizer():
    ARRAY_ROWS = 16
    ARRAY_COLS = 16
    PROBABILITY_OF_ONE = 0.9

    # Window dimensions
    SCREEN_WIDTH = 600
    SCREEN_HEIGHT = 600
    CAPTION = "Pokemon Map"

    # Colors
    BLACK = (0, 0, 0)

    # --- Generate the 2D array ---
    coordinate_grid = main_game_array(ARRAY_ROWS, ARRAY_COLS, PROBABILITY_OF_ONE)

    if coordinate_grid is None:
        print("Couldn't generate grid")
        return

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(CAPTION)

    square_width = SCREEN_WIDTH // ARRAY_COLS
    square_height = SCREEN_HEIGHT // ARRAY_ROWS


    try:
        grass_image_path = "images/grass.png"
        grass_original_image = pygame.image.load(grass_image_path).convert_alpha()
        grass_scaled_surface = pygame.transform.scale(grass_original_image, (square_width, square_height))

    except pygame.error as e:
        print(f"Couldn't load image: {e}.")
        GRASS_COLOR = (34, 139, 34)
        grass_scaled_surface = pygame.Surface((square_width, square_height))
        grass_scaled_surface.fill(GRASS_COLOR)

    try:
        building_image_path = "images/pokemon_building.png"
        building_original_image = pygame.image.load(building_image_path).convert_alpha()
        building_scaled_surface = pygame.transform.scale(building_original_image, (square_width, square_height))

    except pygame.error as e:
        print(f"Couldn't load image: {e}.")
        GRASS_COLOR = (34, 139, 34)
        building_scaled_surface = pygame.Surface((square_width, square_height))
        building_scaled_surface.fill(BLACK)

    # --- Game Loop ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear the screen
        screen.fill(BLACK)

        # Draw the grid
        for row_idx in range(ARRAY_ROWS):
            for col_idx in range(ARRAY_COLS):
                left = col_idx * square_width
                top = row_idx * square_height

                if coordinate_grid[row_idx, col_idx] == 1:
                    screen.blit(grass_scaled_surface, (left, top))
                else:
                    rectangle = pygame.Rect(left, top, square_width, square_height)
                    screen.blit(building_scaled_surface, (left, top))

        pygame.display.flip()

    pygame.quit()
    print("Pygame visualizer closed.")


if __name__ == "__main__":
    run_pygame_visualizer()
