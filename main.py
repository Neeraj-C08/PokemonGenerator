import numpy as np
import pygame
import json
import random
import os

# --- SpriteSheet Class (Not currently used for player or map, but kept if needed for future animated sprites) ---
class SpriteSheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error as e:
            print(f"Unable to load spritesheet image: {filename}: {e}")
            raise SystemExit(e)

    def get_image(self, x, y, width, height):
        image = pygame.Surface([width, height], pygame.SRCALPHA).convert_alpha()
        image.blit(self.sheet, (0, 0), (x, y, width, height))
        return image 

    def load_strip(self, rect, image_count):
        x, y, sprite_width, sprite_height = rect
        images = []
        for i in range(image_count):
            images.append(self.get_image(x + i * sprite_width, y, sprite_width, sprite_height))
        return images

# --- Camera Class ---
class Camera:
    def __init__(self, screen_width_pixels, screen_height_pixels, map_width_tiles, map_height_tiles, tile_size):
        self.camera_x = 0
        self.camera_y = 0
        self.screen_width_pixels = screen_width_pixels
        self.screen_height_pixels = screen_height_pixels
        self.map_width_pixels = map_width_tiles * tile_size
        self.map_height_pixels = map_height_tiles * tile_size
        self.tile_size = tile_size

    def update(self, target_rect):
        """
        Updates the camera's position to center on the target rectangle.
        Clamps the camera position to stay within the map boundaries.
        """
        target_center_x = target_rect.centerx
        target_center_y = target_rect.centery
        
        # Calculate camera's top-left corner to center the target
        self.camera_x = target_center_x - (self.screen_width_pixels // 2)
        self.camera_y = target_center_y - (self.screen_height_pixels // 2)

        # Clamp camera position to map boundaries
        self.camera_x = max(0, min(self.camera_x, self.map_width_pixels - self.screen_width_pixels))
        self.camera_y = max(0, min(self.camera_y, self.map_height_pixels - self.screen_height_pixels))

    def apply(self, rect):
        """
        Adjusts a pygame.Rect's position based on the camera's offset.
        Useful for drawing sprites/objects.
        """
        return rect.move(-self.camera_x, -self.camera_y)

    def apply_pixel_coords(self, x, y):
        """
        Adjusts raw pixel coordinates based on the camera's offset.
        Useful for drawing background tiles or anything drawn by pixel.
        """
        return x - self.camera_x, y - self.camera_y

# --- Constants for Map Generation ---
SUPER_GRID_REGION_SIZE = 4 # Each super-grid cell represents a 4x4 tile area

class BiomeType:
    LAKE = "lake"
    FOREST = "forest"
    PATH = "path" # Represents walkable grass areas (base layer)
    TALLGRASS = "tallgrass" # Cosmetic, walkable
    FLOWERS = "flowers"     # Cosmetic, walkable


# --- Building Definitions ---
BUILDINGS_DATA = {
    "pokecenter": {
        "width_tiles": 4,  # Building will occupy 4x4 tiles
        "height_tiles": 4, 
        "file": "images/house.png" 
    },
    "bakery": { 
        "width_tiles": 4,  # Building will occupy 4x4 tiles
        "height_tiles": 4, 
        "file": "images/house2.png" 
    }
}

# --- Map Generation Functions ---

def generate_layered_map(rows, cols, seed=None):
    """
    Generates a layered map with biomes (lake, forest, path) and a coordinate grid.
    The map generation uses a "super-grid" for larger biome regions.
    Ensures at least 65% of the map is non-path (trees/water).
    After main biome generation, randomly places tallgrass and flowers on path tiles.
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)

    # Calculate super-grid dimensions
    super_rows = rows // SUPER_GRID_REGION_SIZE
    super_cols = cols // SUPER_GRID_REGION_SIZE

    if super_rows == 0 or super_cols == 0:
        print("Error: Map dimensions too small for super-grid size.")
        return None, None

    # Initialize super-grid with paths by default
    super_grid = np.full((super_rows, super_cols), BiomeType.PATH, dtype=object)
    zone_types = [BiomeType.LAKE, BiomeType.FOREST]
    
    # Target: 65% trees/water means 35% or less path
    max_path_percentage = 0.35

    attempts = 0
    max_attempts = 200 # Increased attempts for a better chance of meeting criteria

    while attempts < max_attempts:
        current_super_grid = np.full((super_rows, super_cols), BiomeType.PATH, dtype=object)
        
        # Increase the number of zones to create more non-path areas
        num_zones_to_create = random.randint(5, 12) 
        for _ in range(num_zones_to_create):
            start_r = random.randint(0, super_rows - 1)
            start_c = random.randint(0, super_cols - 1)
            zone_type = random.choice(zone_types)
            
            # Allow for slightly larger blob sizes for biomes
            blob_size = random.randint(10, 35) 

            q = [(start_r, start_c)] # Queue for BFS-like blob generation
            visited = set()
            count = 0

            while q and count < blob_size:
                r, c = q.pop(0)

                if (r, c) in visited:
                    continue
                visited.add((r, c))

                if 0 <= r < super_rows and 0 <= c < super_cols:
                    current_super_grid[r, c] = zone_type
                    count += 1

                    # Add neighbors to the queue with a probability
                    if random.random() < 0.8:
                        neighbors = []
                        if r > 0: neighbors.append((r - 1, c))
                        if r < super_rows - 1: neighbors.append((r + 1, c))
                        if c > 0: neighbors.append((r, c - 1))
                        if c < super_cols - 1: neighbors.append((r, c + 1))
                        random.shuffle(neighbors) # Randomize neighbor order
                        q.extend(neighbors)
            
        path_cells = np.sum(current_super_grid == BiomeType.PATH)
        current_path_percentage = path_cells / (super_rows * super_cols)

        # Check if the current path percentage is within the allowed limit
        if current_path_percentage <= max_path_percentage:
            super_grid = current_super_grid
            print(f"Map generated with {current_path_percentage:.2f} path percentage.")
            break
        attempts += 1
    
    if attempts == max_attempts:
        print(f"Warning: Could not generate map with desired path percentage (<= {max_path_percentage:.2f}) after {max_attempts} attempts. Using last attempt which has {current_path_percentage:.2f} path percentage.")
    else:
        print(f"Map generation successful after {attempts} attempts.")

    # Translate super-grid to tile-level coordinate grid and biome map
    coordinate_grid = np.zeros((rows, cols), dtype=int) 
    biome_map = np.empty((rows, cols), dtype=object)

    for super_r in range(super_rows):
        for super_c in range(super_cols):
            zone_type = super_grid[super_r, super_c]

            start_tile_r = super_r * SUPER_GRID_REGION_SIZE
            start_tile_c = super_c * SUPER_GRID_REGION_SIZE

            for r in range(start_tile_r, start_tile_r + SUPER_GRID_REGION_SIZE):
                for c in range(start_tile_c, start_tile_c + SUPER_GRID_REGION_SIZE):
                    if zone_type == BiomeType.LAKE:
                        coordinate_grid[r, c] = 0 # 0 for impassable (water, trees)
                        biome_map[r, c] = "water"
                    elif zone_type == BiomeType.FOREST:
                        coordinate_grid[r, c] = 0 # 0 for impassable
                        biome_map[r, c] = "forest_tree"
                    else: # BiomeType.PATH
                        coordinate_grid[r, c] = 1 # 1 for walkable (grassland base)
                        biome_map[r, c] = "grassland"

    # --- Add tallgrass and flowers to path tiles ---
    tallgrass_probability = 0.20 # 20% chance for a path tile to become tallgrass
    flowers_probability = 0.10   # 10% chance for a path tile to become flowers (after tallgrass check)

    for r in range(rows):
        for c in range(cols):
            if coordinate_grid[r, c] == 1: # Only modify walkable path tiles
                if random.random() < tallgrass_probability:
                    biome_map[r, c] = "tallgrass"
                elif random.random() < flowers_probability: # Only if not already tallgrass
                    biome_map[r, c] = "flowers"

    return coordinate_grid, biome_map

def place_buildings_on_map(coordinate_grid, num_buildings=5, building_types=["pokecenter", "bakery"]): 
    """
    Places buildings randomly on the map's path tiles.
    Buildings occupy multiple tiles and are marked as impassable (value 2).
    """
    rows, cols = coordinate_grid.shape
    placed_buildings_objects = []

    # Collect all possible top-left starting points (must be a path tile)
    possible_top_lefts = []
    for r in range(rows):
        for c in range(cols):
            if coordinate_grid[r, c] == 1:
                possible_top_lefts.append((r, c))
    
    random.shuffle(possible_top_lefts) # Randomize placement order

    for r_start, c_start in possible_top_lefts:
        if len(placed_buildings_objects) >= num_buildings:
            break # Stop once desired number of buildings is placed

        building_type_name = random.choice(building_types)
        building_info = BUILDINGS_DATA[building_type_name]
        
        b_width = building_info["width_tiles"]
        b_height = building_info["height_tiles"]

        # Check if building fits within map boundaries
        if r_start + b_height > rows or c_start + b_width > cols:
            continue

        is_clear = True
        # Check if all tiles under the building are clear and are path tiles
        for r_offset in range(b_height):
            for c_offset in range(b_width):
                current_r = r_start + r_offset
                current_c = c_start + c_offset
                
                # Ensure it's within bounds (redundant due to earlier check, but good for safety)
                if not (0 <= current_r < rows and 0 <= current_c < cols): 
                    is_clear = False
                    break
                # Building can only be placed on path tiles (coordinate_grid value 1)
                # It must NOT be on water, trees, or another building (0 or 2)
                if coordinate_grid[current_r, current_c] != 1: 
                    is_clear = False
                    break
            if not is_clear:
                break
        
        if is_clear:
            # Mark the tiles occupied by the building as impassable (2)
            for r_offset in range(b_height):
                for c_offset in range(b_width):
                    coordinate_grid[r_start + r_offset, c_start + c_offset] = 2 
            
            placed_buildings_objects.append({
                "type": building_type_name,
                "grid_x": c_start,
                "grid_y": r_start,
                "width_tiles": b_width,
                "height_tiles": b_height
            })
            
    return placed_buildings_objects

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self, start_grid_x, start_grid_y, square_width, square_height, total_rows, total_cols, player_images):
        super().__init__()

        # player_images is a dict with direction keys and lists of images: {"down": [img1, img2], ...}
        self.images = player_images
        self.direction = "down"
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 10  # Lower is faster

        self.image = self.images[self.direction][self.current_frame]
        self.rect = self.image.get_rect(topleft=(start_grid_x * square_width, start_grid_y * square_height))

        self.grid_x = start_grid_x
        self.grid_y = start_grid_y

        self.total_rows = total_rows
        self.total_cols = total_cols
        self.square_width = square_width
        self.square_height = square_height

        self.move_cooldown_initial = 15
        self.move_cooldown_subsequent = 5
        self.move_timer = 0
        self.moving_direction = None

    def update(self, coordinate_grid):
        if self.move_timer > 0:
            self.move_timer -= 1

        if self.moving_direction:
            moved = False
            if self.move_timer == 0:
                moved = self.try_move(*self.moving_direction, coordinate_grid, is_continuous=True)

            # Update animation regardless of whether player moved (for visual feedback while walking)
            self.update_animation()
        else:
            # Reset to default idle frame when not moving
            self.animation_timer = 0
            self.current_frame = 0
            self.image = self.images[self.direction][self.current_frame]
    def update_animation(self):
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.images[self.direction])
            self.image = self.images[self.direction][self.current_frame]
            self.animation_timer = 0
    def set_moving_direction(self, dx, dy):
        direction_map = {
            (0, -1): "up",
            (0, 1): "down",
            (-1, 0): "left",
            (1, 0): "right"
        }
        new_direction = direction_map.get((dx, dy), "down")

        if self.moving_direction != (dx, dy):
            self.moving_direction = (dx, dy)
            self.direction = new_direction
            self.move_timer = self.move_cooldown_initial

    def clear_moving_direction(self):
        self.moving_direction = None
        self.move_timer = 0

    def try_move(self, dx, dy, coordinate_grid, is_continuous=False):
        if is_continuous and self.move_timer > 0:
            return False

        new_grid_x = self.grid_x + dx
        new_grid_y = self.grid_y + dy

        if not (0 <= new_grid_x < self.total_cols and 0 <= new_grid_y < self.total_rows):
            return False
            
        # Collision check: Player can only move on path tiles (coordinate_grid value 1)
        # 0 = impassable (water/tree), 1 = walkable (grass/tallgrass/flowers), 2 = impassable (building)
        if coordinate_grid[new_grid_y, new_grid_x] != 1:
            return False

        self.grid_x = new_grid_x
        self.grid_y = new_grid_y
        self.rect.topleft = (self.grid_x * self.square_width, self.grid_y * self.square_height)
        self.move_timer = self.move_cooldown_subsequent if is_continuous else self.move_cooldown_initial
        return True

# --- Save/Load Player Coords (Optional: if you want to save game state) ---
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
        return 0, 0 # Return default if file not found or data is missing

# --- Pygame Visualizer Main Function ---
def run_pygame_visualizer():
    # Print current working directory for debugging file paths (important for images!)
    print(f"Current working directory: {os.getcwd()}")

    clock = pygame.time.Clock()
    ARRAY_ROWS = 64
    ARRAY_COLS = 64
    SEED = 6969 # Seed for reproducible map generation

    TILE_SIZE = 32 # Size of one tile in pixels
    
    # --- Screen Size (This is the camera's viewport size, not the whole map size) ---
    SCREEN_WIDTH = 800  
    SCREEN_HEIGHT = 600 

    CAPTION = f"Pokemon Map (Seed: {SEED})"
    # Removed BLACK and GREEN constants that were not used or incorrectly defined as sets
    # We will use direct RGB tuples where needed or replace them with loaded textures.

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(CAPTION)

    square_width = TILE_SIZE
    square_height = TILE_SIZE

    # --- Generate Map ---
    coordinate_grid, biome_map = generate_layered_map(ARRAY_ROWS, ARRAY_COLS, seed=SEED)
    if coordinate_grid is None:
        print("Failed to generate map. Exiting.")
        pygame.quit()
        return

    # --- Load and scale biome textures from individual files ---
    biome_textures = {}
    try:
        biome_textures["grassland"] = pygame.transform.scale(
            pygame.image.load("images/grass.png").convert_alpha(), (square_width, square_height)
        )
        biome_textures["water"] = pygame.transform.scale(
            pygame.image.load("images/water.png").convert_alpha(), (square_width, square_height)
        )
        biome_textures["forest_tree"] = pygame.transform.scale(
            pygame.image.load("images/tree.png").convert_alpha(), (square_width, square_height)
        )
        # NEW: Load tallgrass and flowers
        biome_textures["tallgrass"] = pygame.transform.scale(
            pygame.image.load("images/tallgrass.png").convert_alpha(), (square_width, square_height)
        )
        biome_textures["flowers"] = pygame.transform.scale(
            pygame.image.load("images/flowers.png").convert_alpha(), (square_width, square_height)
        )
        print("Biome textures loaded successfully.")
    except pygame.error as e:
        print(f"Error loading biome textures from individual files: {e}. Using fallback colors.")
        # Fallback: create solid colored surfaces if images are not found
        fallback_grass = pygame.Surface((square_width, square_height))
        fallback_grass.fill((34, 139, 34)) # Forest Green
        biome_textures["grassland"] = fallback_grass

        fallback_water = pygame.Surface((square_width, square_height))
        fallback_water.fill((60, 120, 200)) # Blue
        biome_textures["water"] = fallback_water

        fallback_tree = pygame.Surface((square_width, square_height))
        fallback_tree.fill((30, 80, 0)) # Dark Green
        biome_textures["forest_tree"] = fallback_tree

        # Fallback for tallgrass and flowers
        fallback_tallgrass = pygame.Surface((square_width, square_height))
        fallback_tallgrass.fill((50, 160, 50)) # Slightly darker green for tallgrass
        biome_textures["tallgrass"] = fallback_tallgrass

        fallback_flowers = pygame.Surface((square_width, square_height))
        fallback_flowers.fill((200, 100, 200)) # Pinkish for flowers
        biome_textures["flowers"] = fallback_flowers


    # --- Load Building Sprites from individual files ---
    building_images = {}
    try:
        for b_type, b_info in BUILDINGS_DATA.items():
            building_sprite_original = pygame.image.load(b_info["file"]).convert_alpha()
            scaled_sprite = pygame.transform.scale(
                building_sprite_original,
                (b_info["width_tiles"] * square_width, # Scale based on tiles occupied
                 b_info["height_tiles"] * square_height)
            )
            building_images[b_type] = scaled_sprite
        print("Building images loaded successfully.")
    except pygame.error as e:
        print(f"Couldn't load building images from individual files: {e}. Using fallback colored rectangles for buildings.")
        # Fallback for buildings if loading fails
        for b_type, b_info in BUILDINGS_DATA.items():
            fallback_surface = pygame.Surface((b_info["width_tiles"] * square_width, b_info["height_tiles"] * square_height))
            if b_type == "pokecenter":
                fallback_surface.fill((150, 0, 150)) # Purple
            elif b_type == "bakery":
                fallback_surface.fill((100, 100, 100)) # Grey
            building_images[b_type] = fallback_surface

    placed_buildings_objects = place_buildings_on_map(coordinate_grid, num_buildings=8)

    # --- Player Setup ---
    players = pygame.sprite.Group()

    # Load the single player sprite image
    player_images = {}
    directions = ["up", "down", "left", "right"]
    for direction in directions:
        player_images[direction] = []
        for frame_num in [1, 2, 3, 4]:  # Assumes 2 frames per direction: up1.png, up2.png, etc.
            try:
                img = pygame.image.load(f"images/{direction}{frame_num}.png").convert_alpha()
                img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                player_images[direction].append(img)
            except pygame.error as e:
                print(f"Missing image: images/{direction}{frame_num}.png — using fallback")
                fallback = pygame.Surface((TILE_SIZE, TILE_SIZE))
                fallback.fill((255, 0, 0))  # Bright red placeholder
                player_images[direction].append(fallback) 
                
    # Find a valid starting position (a '1' in coordinate_grid) for the player
    start_x, start_y = 0, 0
    found_start = False
    for r in range(ARRAY_ROWS):
        for c in range(ARRAY_COLS):
            if coordinate_grid[r, c] == 1: # '1' means path/grassland (which includes tallgrass/flowers)
                start_x, start_y = c, r
                found_start = True
                break
        if found_start:
            break
    
    if not found_start:
        print("Could not find a valid starting position for the player (no path tiles available). Exiting.")
        pygame.quit()
        return

    player = Player(start_x, start_y, square_width, square_height, ARRAY_ROWS, ARRAY_COLS, player_images)
    players.add(player)

    # --- Camera Setup ---
    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, ARRAY_COLS, ARRAY_ROWS, TILE_SIZE)

    # --- Game Loop ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN: # Check for any key press event
                if event.key == pygame.K_UP:
                    player.set_moving_direction(0, -1)
                elif event.key == pygame.K_DOWN:
                    player.set_moving_direction(0, 1)
                elif event.key == pygame.K_LEFT:
                    player.set_moving_direction(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    player.set_moving_direction(1, 0)
                
                # For the initial press, immediately try to move (without cooldown)
                # Only attempt if a directional key was actually pressed and set moving_direction
                if player.moving_direction: 
                    player.try_move(*player.moving_direction, coordinate_grid, is_continuous=False) 
            elif event.type == pygame.KEYUP: # Check for any key release event
                # Stop continuous movement when a directional key is released
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    player.clear_moving_direction()

        # Update player position (handles continuous movement if a key is held)
        players.update(coordinate_grid) 
        # Update camera to follow the player
        camera.update(player.rect) 

        # Clear the screen
        screen.fill((114,199,160)) # Using a direct RGB tuple for screen clear

        # --- Draw all tiles (optimized with camera culling) ---
        # Calculate which range of tiles are currently visible on screen
        start_col = max(0, camera.camera_x // TILE_SIZE)
        end_col = min(ARRAY_COLS, (camera.camera_x + SCREEN_WIDTH) // TILE_SIZE + 1)
        start_row = max(0, camera.camera_y // TILE_SIZE)
        end_row = min(ARRAY_ROWS, (camera.camera_y + SCREEN_HEIGHT) // TILE_SIZE + 1)

        for row_idx in range(start_row, end_row): 
            for col_idx in range(start_col, end_col):
                # Calculate the tile's world position (its actual position on the large map)
                world_x, world_y = col_idx * TILE_SIZE, row_idx * TILE_SIZE 
                # Apply camera offset to get its position relative to the screen
                draw_x, draw_y = camera.apply_pixel_coords(world_x, world_y)
                
                biome = biome_map[row_idx][col_idx] # This now includes 'tallgrass' and 'flowers'

                # Draw tiles based on their biome type
                if biome in biome_textures: # Ensure we have a texture for this biome
                    screen.blit(biome_textures[biome], (draw_x, draw_y))
                else: # Fallback for unknown biomes (shouldn't happen with current logic)
                    pygame.draw.rect(screen, (255, 0, 255), (draw_x, draw_y, TILE_SIZE, TILE_SIZE))

        # --- Draw multi-tile buildings (with camera application) ---
        for building_obj in placed_buildings_objects:
            # Calculate building's world position
            world_x, world_y = building_obj["grid_x"] * square_width, building_obj["grid_y"] * square_height
            # Apply camera offset
            draw_x, draw_y = camera.apply_pixel_coords(world_x, world_y)
            
            building_pixel_width = building_obj["width_tiles"] * square_width
            building_pixel_height = building_obj["height_tiles"] * square_height
            
            # Optimization: Only draw if building is within the visible screen area
            if (draw_x + building_pixel_width > 0 and draw_x < SCREEN_WIDTH and
                draw_y + building_pixel_height > 0 and draw_y < SCREEN_HEIGHT):
                
                building_sprite = building_images.get(building_obj["type"])
                if building_sprite:
                    screen.blit(building_sprite, (draw_x, draw_y))
                else:
                    # Fallback if image load failed: draw a magenta rectangle
                    pygame.draw.rect(screen, (255, 0, 255), (draw_x, draw_y, 
                                                            building_pixel_width, 
                                                            building_pixel_height))

        # --- Draw player (with camera application) ---
        # The player's rect is in "world" coordinates; camera.apply() converts it to screen coordinates
        screen.blit(player.image, camera.apply(player.rect))
        
        # Update the full display surface to show everything drawn
        pygame.display.flip()
        # Cap the frame rate
        clock.tick(60)

    # Quit Pygame when the loop ends
    pygame.quit()
    print("Pygame visualizer closed.")

# --- Entry point of the script ---
if __name__ == "__main__":
    run_pygame_visualizer()