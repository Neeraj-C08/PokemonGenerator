import numpy as np
import pygame
import json


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

def save_player_coords(grid_x, grid_y, filename="player_coords.json"):
    data = {
        "x": grid_x,
        "y": grid_y
    }
    with open(filename, "w") as f:
        json.dump(data, f)

def load_player_coords(filename="player_coords.json"):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            return data["x"], data["y"]
    except (FileNotFoundError, KeyError):
        return 0, 0  


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

def is_at_building_entrance(player_x, player_y, building_coords):
    for r, c in building_coords:
        if player_y == r + 1 and player_x == c:
            return True
    return False


class Player(pygame.sprite.Sprite):
    def __init__(self, image_path, start_grid_x, start_grid_y, square_width, square_height, total_rows, total_cols):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (square_width, square_height))

        self.grid_x = start_grid_x
        self.grid_y = start_grid_y

        self.rect = self.image.get_rect(topleft=(self.grid_x * square_width, self.grid_y * square_height))

        self.total_rows = total_rows
        self.total_cols = total_cols
        self.square_width = square_width
        self.square_height = square_height
        self.is_moving = False
        self.move_cooldown = 1  # frames between moves
        self.move_timer = 0


    def try_move(self, dx, dy, coordinate_grid):
            if self.move_timer > 0:
                self.move_timer -= 1
                return


            new_grid_x = self.grid_x + dx
            new_grid_y = self.grid_y + dy


            if not (0 <= new_grid_x < self.total_cols and 0 <= new_grid_y < self.total_rows):
                return


            if coordinate_grid[new_grid_y, new_grid_x] == 0:
                return


            self.grid_x = new_grid_x
            self.grid_y = new_grid_y
            self.rect.topleft = (self.grid_x * self.square_width, self.grid_y * self.square_height)
            self.is_moving = True
            self.move_timer = self.move_cooldown  # reset cooldown
    # ADDITION: Load multiple images for animation
    def load_animation_images(image_paths, width, height):
        return [pygame.transform.scale(pygame.image.load(path).convert_alpha(), (width, height)) for path in image_paths]

    def update(self):
        if self.is_moving:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.current_frame]
        else:
            self.image = self.animations[self.direction][0]


def run_pygame_visualizer():
    clock = pygame.time.Clock()
    ARRAY_ROWS = 16
    ARRAY_COLS = 16
    PROBABILITY_OF_ONE = 0.85
    SEED = 3465

    SCREEN_WIDTH = 600
    SCREEN_HEIGHT = 600
    CAPTION = f"Pokemon Map (Seed: {SEED})"
    BLACK = (0, 0, 0)

    coordinate_grid = main_game_array(ARRAY_ROWS, ARRAY_COLS, PROBABILITY_OF_ONE, seed=SEED)
    if coordinate_grid is None:
        print("Failed to generate coordinate grid.")
        return

    # Store all building positions
    building_coords = [(r, c) for r in range(ARRAY_ROWS) for c in range(ARRAY_COLS) if coordinate_grid[r, c] == 0]

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(CAPTION)

    square_width = SCREEN_WIDTH // ARRAY_COLS
    square_height = SCREEN_HEIGHT // ARRAY_ROWS

    # Load and scale biome textures once
    try:
        biome_textures = {
            "grassland": pygame.transform.scale(pygame.image.load("images/grass.png").convert_alpha(), (square_width, square_height)),
            "desert": pygame.transform.scale(pygame.image.load("images/32x32_sand_desert_dune.png").convert_alpha(), (square_width, square_height)),
            "snow": pygame.transform.scale(pygame.image.load("images/snow.png").convert_alpha(), (square_width, square_height)),
        }
    except pygame.error as e:
        print(f"Error loading biome textures: {e}. Some textures might be missing.")
        biome_textures = {
            "grassland": pygame.Surface((square_width, square_height)),
            "desert": pygame.Surface((square_width, square_height)),
            "snow": pygame.Surface((square_width, square_height)),
        }
        biome_textures["grassland"].fill((34, 139, 34))
        biome_textures["desert"].fill((210, 180, 140)) 
        biome_textures["snow"].fill((245, 245, 245))    


    try:
        building_image = pygame.image.load("images/pokemon_building.png").convert_alpha()
        building_scaled = pygame.transform.scale(building_image, (square_width, square_height))
    except pygame.error as e:
        print(f"Couldn't load building image: {e}. Using fallback.")
        building_scaled = pygame.Surface((square_width, square_height))
        building_scaled.fill((100, 100, 100)) 


    # Generate grid + biome map
    coordinate_grid = main_game_array(ARRAY_ROWS, ARRAY_COLS, PROBABILITY_OF_ONE, seed=SEED)
    biome_map = generate_biome_map(ARRAY_ROWS, ARRAY_COLS, seed=SEED)

    players = pygame.sprite.Group()


    start_x, start_y = 0, 0
    found_start = False
    for r in range(ARRAY_ROWS):
        for c in range(ARRAY_COLS):
            if coordinate_grid[r, c] == 1: 
                start_x, start_y = c, r
                found_start = True
                break
        if found_start:
            break

    player = Player("images/down1.png", start_x, start_y,square_width, square_height, ARRAY_ROWS, ARRAY_COLS) 
    players.add(player)
        # Setup directional animations
    image_sets = {
        "up": ["images/up1.png", "images/up2.png", "images/up3.png", "images/up4.png"],
        "down": ["images/down1.png", "images/down2.png", "images/down3.png", "images/down4.png"],
        "left": ["images/left1.png", "images/left2.png", "images/left3.png", "images/left4.png"],
        "right": ["images/right1.png", "images/right2.png", "images/right3.png", "images/right4.png"]
    }


    # --- Game Loop ---
    def load_directional_animations(base_names, width, height):
        animations = {}
        for direction, image_files in base_names.items():
            animations[direction] = [pygame.transform.scale(
                pygame.image.load(img).convert_alpha(), (width, height)) for img in image_files]
        return animations
    
    player.animations = load_directional_animations(image_sets, player.square_width, player.square_height)
    player.direction = "down"  # starting direction
    player.current_frame = 0
    player.animation_timer = 0
    player.animation_speed = 100
    player.image = player.animations[player.direction][0]  # Set initial image


    # in the game loop
    clock.tick(60)  # 60 FPS

    running = True
    while running:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            player.is_moving = False

            if keys[pygame.K_UP]:
                player.direction = "up"
                above_y = player.grid_y - 1
                if (above_y, player.grid_x) in building_coords:
                    print(f"Entered building at ({player.grid_x}, {above_y})")
                    save_player_coords(player.grid_x, player.grid_y) 
                    # Handle building entrance logic here
                else:
                    player.try_move(0, -1, coordinate_grid)
            elif keys[pygame.K_DOWN]:
                player.direction = "down"
                player.try_move(0, 1, coordinate_grid)
            elif keys[pygame.K_LEFT]:
                player.direction = "left"
                player.try_move(-1, 0, coordinate_grid)
            elif keys[pygame.K_RIGHT]:
                player.direction = "right"
                player.try_move(1, 0, coordinate_grid)


        # Clear the screen
        screen.fill(BLACK)

        # Draw the grid
        for row_idx in range(ARRAY_ROWS):
            for col_idx in range(ARRAY_COLS):
                x = col_idx * square_width
                y = row_idx * square_height
                biome = biome_map[row_idx][col_idx]

                if coordinate_grid[row_idx, col_idx] == 1: 
                    screen.blit(biome_textures[biome], (x, y))
                else: 
                    screen.blit(building_scaled, (x, y))

        players.update()
        players.draw(screen)
        pygame.display.flip()
        print(player.grid_x, player.grid_y)
        

    pygame.quit()
    print("Pygame visualizer closed.")


if __name__ == "__main__":
    run_pygame_visualizer()