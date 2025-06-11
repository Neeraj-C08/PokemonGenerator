import numpy as np
import pygame

BIOMES = ["grassland", "desert", "snow"]


# Re-defining the array generation function for self-containment
def main_game_array(rows, cols, probability_of_one=0.5, seed=None):
    if not (0 <= probability_of_one <= 1):
        print("change probability of generating 1's ")
        return None

    if seed is not None:
        np.random.seed(seed) 

    random_array = np.random.rand(rows, cols)
    binary_array = (random_array <= probability_of_one).astype(int)
    return binary_array

def generate_biome_map(rows, cols, seed):
    np.random.seed(seed)
    biome_grid = np.empty((rows, cols), dtype=object)

    REGION_SIZE = 4  # every 4x4 block is one biome
    biome_choices = ["grassland", "desert", "snow"]

    for row in range(0, rows, REGION_SIZE):
        for col in range(0, cols, REGION_SIZE):
            biome = np.random.choice(biome_choices)

            for r in range(row, min(row + REGION_SIZE, rows)):
                for c in range(col, min(col + REGION_SIZE, cols)):
                    biome_grid[r, c] = biome

    return biome_grid




def run_pygame_visualizer():
    ARRAY_ROWS = 16
    ARRAY_COLS = 16
    PROBABILITY_OF_ONE = 0.85
    SEED = 3465

    SCREEN_WIDTH = 600
    SCREEN_HEIGHT = 600
    CAPTION = f"Biomes Map (Seed: {SEED})"
    BLACK = (0, 0, 0)

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(CAPTION)

    square_width = SCREEN_WIDTH // ARRAY_COLS
    square_height = SCREEN_HEIGHT // ARRAY_ROWS

    # --- Load placeholder biome images ---

    def load_placeholder(name):
        surf = pygame.Surface((square_width, square_height))
        if name == "grassland":
          pygame.image.load("images/grass.png").convert_alpha()  # green
        elif name == "desert":
            pygame.image.load("images/32x32_sand_desert_dune.png").convert_alpha() # sand
        elif name == "snow":
            surf.fill((245, 245, 245))  # white
        return surf
 

    biome_textures = {
        "grassland": pygame.image.load("images/grass.png").convert_alpha() ,
        "desert": pygame.image.load("images/32x32_sand_desert_dune.png").convert_alpha(),
        "snow": pygame.image.load("images/snow.png").convert_alpha(),
    }

    # Generate grid + biome map
    coordinate_grid = main_game_array(ARRAY_ROWS, ARRAY_COLS, PROBABILITY_OF_ONE, seed=SEED)
    biome_map = generate_biome_map(ARRAY_ROWS, ARRAY_COLS, seed=SEED)

    class Player(pygame.sprite.Sprite):
        def __init__(self, image_path, position, size):
            super().__init__()
            self.image = pygame.image.load("images/PokeEnd4-removebg-preview.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, size)
            self.rect = self.image.get_rect(topleft=position)


        def update(self):
            # Update player position or state if needed
            pass
    players = pygame.sprite.Group()


    player = Player("images/PokeEnd4-removebg-preview.png", (10, 10), (32, 32))
    players.add(player)




    # --- Game Loop ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BLACK)

        for row_idx in range(ARRAY_ROWS):
            for col_idx in range(ARRAY_COLS):
                x = col_idx * square_width
                y = row_idx * square_height
                biome = biome_map[row_idx][col_idx]

                if coordinate_grid[row_idx][col_idx] == 1:
                    screen.blit(biome_textures[biome], (x, y))
                else:
                    building_image = pygame.image.load("images/pokemon_building.png").convert_alpha()
                    building_scaled = pygame.transform.scale(building_image, (square_width, square_height))

                    screen.blit(building_scaled, (x, y))

                    

        pygame.display.flip()

        players.update()
        players.draw(screen)
        pygame.display.flip()


    pygame.quit()
    print("Pygame visualizer closed.")



if __name__ == "__main__":
    run_pygame_visualizer()
