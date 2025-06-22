import numpy as np
import pygame
import json
import random
import os



#Camera Class
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
        return rect.move(-self.camera_x, -self.camera_y)

    def apply_pixel_coords(self, x, y):
        return x - self.camera_x, y - self.camera_y


class BiomeType:
    LAKE = "lake"
    FOREST = "forest"
    PATH = "path" 
    TALLGRASS = "tallgrass" 
    FLOWERS = "flowers"     


#Map Gen
def generate_layered_map(rows, cols, map_settings, seed=None):
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)

    SUPER_GRID_REGION_SIZE = map_settings["super_grid_region_size"]
    max_path_percentage = map_settings["max_path_percentage"]
    max_attempts = map_settings["max_map_generation_attempts"]
    tallgrass_probability = map_settings["tallgrass_probability"]
    flowers_probability = map_settings["flowers_probability"]

    # Calculate supergrid dimensions
    super_rows = rows // SUPER_GRID_REGION_SIZE
    super_cols = cols // SUPER_GRID_REGION_SIZE

    if super_rows == 0 or super_cols == 0:
        print("Error: Map dimensions too small for super-grid size.")
        return None, None

    # Initialize supergrid with paths by default
    super_grid = np.full((super_rows, super_cols), BiomeType.PATH, dtype=object)
    zone_types = [BiomeType.LAKE, BiomeType.FOREST]
    
    attempts = 0

    while attempts < max_attempts:
        current_super_grid = np.full((super_rows, super_cols), BiomeType.PATH, dtype=object)
        
        # More zones for for nonpath areas
        num_zones_to_create = random.randint(5, 12)
        for _ in range(num_zones_to_create):
            start_r = random.randint(0, super_rows - 1)
            start_c = random.randint(0, super_cols - 1)
            zone_type = random.choice(zone_types)
            
           
            blob_size = random.randint(10, 35)

            q = [(start_r, start_c)] 
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

                    
                    if random.random() < 0.8:
                        neighbors = []
                        if r > 0: neighbors.append((r - 1, c))
                        if r < super_rows - 1: neighbors.append((r + 1, c))
                        if c > 0: neighbors.append((r, c - 1))
                        if c < super_cols - 1: neighbors.append((r, c + 1))
                        random.shuffle(neighbors) 
                        q.extend(neighbors)
            
        path_cells = np.sum(current_super_grid == BiomeType.PATH)
        current_path_percentage = path_cells / (super_rows * super_cols)

        # Check if the current path percentage is within the allowed limit
        if current_path_percentage <= max_path_percentage:
            super_grid = current_super_grid
            break
        attempts += 1
    
    if attempts == max_attempts:
        print(f"Couldn't generate map with the current path percentage")
    else:
        print(f"Map generation successful after {attempts} attempts.")


    # Translate supergrid to tile level coordinate grid
    coordinate_grid = np.zeros((rows, cols), dtype=int)
    tile_map = np.empty((rows, cols), dtype=object)


    for super_r in range(super_rows):
        for super_c in range(super_cols):
            zone_type = super_grid[super_r, super_c]


            start_tile_r = super_r * SUPER_GRID_REGION_SIZE
            start_tile_c = super_c * SUPER_GRID_REGION_SIZE


            for r in range(start_tile_r, start_tile_r + SUPER_GRID_REGION_SIZE):
                for c in range(start_tile_c, start_tile_c + SUPER_GRID_REGION_SIZE):
                    if zone_type == BiomeType.LAKE:
                        coordinate_grid[r, c] = 0 #0 for impassable
                        tile_map[r, c] = "water"
                    elif zone_type == BiomeType.FOREST:
                        coordinate_grid[r, c] = 0 #0 for impassable
                        tile_map[r, c] = "forest_tree"
                    else: # BiomeType.PATH
                        coordinate_grid[r, c] = 1 #1 for walkable
                        tile_map[r, c] = "grassland"


    for r in range(rows):
        for c in range(cols):
            if coordinate_grid[r, c] == 1: 
                if random.random() < tallgrass_probability:
                    tile_map[r, c] = "tallgrass"
                elif random.random() < flowers_probability: 
                    tile_map[r, c] = "flowers"


    return coordinate_grid, tile_map


def generate_interior_map(rows, cols, interior_settings):
    coordinate_grid = np.zeros((rows, cols), dtype=int)
    tile_map = np.empty((rows, cols), dtype=object)

    floor_tile_type = interior_settings["floor_tile_type"]
    wall_tile_type = interior_settings["wall_tile_type"]
    door_tile_type = interior_settings["door_tile_type"]


    tile_map.fill(floor_tile_type)
    coordinate_grid.fill(1) 

    # Create walls around the perimeter
    for r in range(rows):
        for c in range(cols):
            if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                tile_map[r, c] = wall_tile_type
                coordinate_grid[r, c] = 0 #Walls are impassable

    # Place a door in the middle of the bottom wall
    door_col = cols // 2
    #door is on the bottom wall and in bounds
    if rows - 1 >= 0 and 0 <= door_col < cols:
        tile_map[rows - 1, door_col] = door_tile_type
        coordinate_grid[rows - 1, door_col] = 1 

    print(f"Interior map generated: {rows}x{cols} with door at ({rows-1}, {door_col})")
    return coordinate_grid, tile_map, (rows - 1, door_col)


def place_buildings_on_map(coordinate_grid, num_buildings, building_definitions):
    rows, cols = coordinate_grid.shape
    placed_buildings_objects = []

    # Collect all possible top-left starting points (must be a path tile)
    possible_top_lefts = []
    for r in range(rows):
        for c in range(cols):
            if coordinate_grid[r, c] == 1:
                possible_top_lefts.append((r, c))
    
    random.shuffle(possible_top_lefts) 

    building_types = list(building_definitions.keys())

    for r_start, c_start in possible_top_lefts:
        if len(placed_buildings_objects) >= num_buildings:
            break 

        building_type_name = random.choice(building_types)
        building_info = building_definitions[building_type_name]
        
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
                
                # Building can only be placed on path tiles
                if not (0 <= current_r < rows and 0 <= current_c < cols and coordinate_grid[current_r, current_c] == 1):
                    is_clear = False
                    break
            if not is_clear:
                break
        

        interaction_tile_x = c_start + b_width // 2
        interaction_tile_y = r_start + b_height 


        if not (0 <= interaction_tile_y < rows and 0 <= interaction_tile_x < cols and coordinate_grid[interaction_tile_y, interaction_tile_x] == 1):
            is_clear = False

        if is_clear:
            # Mark the tiles occupied by the building as impassable (2)
            for r_offset in range(b_height):
                for c_offset in range(b_width):
                    coordinate_grid[r_start + r_offset, c_start + c_offset] = 2
            
            coordinate_grid[interaction_tile_y, interaction_tile_x] = 1 

            placed_buildings_objects.append({
                "type": building_type_name,
                "grid_x": c_start,
                "grid_y": r_start,
                "width_tiles": b_width,
                "height_tiles": b_height,
                "entrance_tile_world_coords": (interaction_tile_x, interaction_tile_y) #The player stands on this tile to interact
            })
            
    return placed_buildings_objects


#Player Class 
class Player(pygame.sprite.Sprite):
    def __init__(self, start_grid_x, start_grid_y, square_width, square_height, total_rows, total_cols, player_images, game_settings):
        super().__init__()

        self.images = player_images
        self.direction = "down"
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = game_settings["player_animation_speed"]

        self.image = self.images[self.direction][self.current_frame]
        self.rect = self.image.get_rect(topleft=(start_grid_x * square_width, start_grid_y * square_height))

        self.grid_x = start_grid_x
        self.grid_y = start_grid_y

        self.total_rows = total_rows
        self.total_cols = total_cols
        self.square_width = square_width
        self.square_height = square_height

        self.move_cooldown_initial = game_settings["player_move_cooldown_initial"]
        self.move_cooldown_subsequent = game_settings["player_move_cooldown_subsequent"]
        self.move_timer = 0
        self.moving_direction = None

        self.interaction_cooldown = 0 
        self.max_interaction_cooldown = 20 

    def update(self, coordinate_grid):
        if self.move_timer > 0:
            self.move_timer -= 1
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1

        if self.moving_direction:
            moved = False
            if self.move_timer == 0:
                moved = self.try_move(*self.moving_direction, coordinate_grid, self.total_rows, self.total_cols, is_continuous=True)
            self.update_animation()
        else:
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


    def try_move(self, dx, dy, coordinate_grid, map_rows, map_cols, is_continuous=False):
        if is_continuous and self.move_timer > 0:
            return False

        new_grid_x = self.grid_x + dx
        new_grid_y = self.grid_y + dy

        #Check map bounds
        if not (0 <= new_grid_x < map_cols and 0 <= new_grid_y < map_rows):
            return False
            
        #Player can only move on walkable tiles
        if coordinate_grid[new_grid_y, new_grid_x] != 1:
            return False

        self.grid_x = new_grid_x
        self.grid_y = new_grid_y
        self.rect.topleft = (self.grid_x * self.square_width, self.grid_y * self.square_height)
        self.move_timer = self.move_cooldown_subsequent if is_continuous else self.move_cooldown_initial
        return True


#Game State 
player = None
camera = None
current_map_data = {} # Stores the current map's grid, tile types, and other info
outdoor_map_data = {} # Stores the outdoor map's state when player is indoors (grid, tiles, buildings, last entrance)
placed_buildings_data = [] # Stores placed building objects for outdoor map


def switch_to_outdoor():
    global player, camera, current_map_data, outdoor_map_data

    # Restore outdoor map data
    current_map_data = outdoor_map_data['map_details']
    global placed_buildings_data 
    placed_buildings_data = outdoor_map_data['buildings']


    # Put player where they entered the building from
    return_coords = outdoor_map_data['player_last_outdoor_pos']
    player.grid_x = return_coords[0]
    player.grid_y = return_coords[1]
    
    # Update player's internal map dimensions
    player.total_rows = current_map_data["grid"].shape[0]
    player.total_cols = current_map_data["grid"].shape[1]

    camera = Camera(current_map_data["screen_width"], current_map_data["screen_height"], 
                    current_map_data["grid"].shape[1], current_map_data["grid"].shape[0], 
                    current_map_data["tile_size"])

 
    player.rect.topleft = (player.grid_x * current_map_data["tile_size"], player.grid_y * current_map_data["tile_size"])
    
    # cooldown for entry/exit
    player.interaction_cooldown = player.max_interaction_cooldown 
    
    print(f"Switched to outdoor map. Player at {player.grid_x},{player.grid_y}")


def switch_to_indoor(outdoor_entrance_coords, interior_settings, game_settings):
    global player, camera, current_map_data, outdoor_map_data

    # Store current outdoor map state before switching
    outdoor_map_data['map_details'] = current_map_data.copy() 
    outdoor_map_data['player_last_outdoor_pos'] = outdoor_entrance_coords # Store where we entered from
    outdoor_map_data['buildings'] = placed_buildings_data # Reference to the global list of buildings

    # Generate interior map
    interior_coord_grid, interior_tile_map, interior_door_pos = generate_interior_map(
        interior_settings["interior_rows"], interior_settings["interior_cols"], interior_settings
    )

    # Set current map data to interior map
    current_map_data = {
        "grid": interior_coord_grid,
        "tiles": interior_tile_map,
        "type": "indoor",
        "exit_point": interior_door_pos,
        "tile_size": game_settings["tile_size"],
        "screen_width": game_settings["screen_width"],
        "screen_height": game_settings["screen_height"]
    }

   
    player.grid_x = interior_door_pos[1] 
    player.grid_y = interior_door_pos[0] - 1

    # Update player's internal map dimensions
    player.total_rows = current_map_data["grid"].shape[0]
    player.total_cols = current_map_data["grid"].shape[1]

    camera = Camera(current_map_data["screen_width"], current_map_data["screen_height"], 
                    current_map_data["grid"].shape[1], current_map_data["grid"].shape[0], 
                    current_map_data["tile_size"])

  
    player.rect.topleft = (player.grid_x * current_map_data["tile_size"], player.grid_y * current_map_data["tile_size"])

  
    player.interaction_cooldown = player.max_interaction_cooldown

    print(f"Switched to indoor map. Player at {player.grid_x},{player.grid_y}")


#Pygame Visualizer Main
def run_pygame_visualizer():
    global player, camera, current_map_data, outdoor_map_data, placed_buildings_data

    print(f"Current working directory: {os.getcwd()}")

    config_file = "config.json"
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        print(f"Configuration loaded from {config_file}")
    except FileNotFoundError:
        print(f"Error: {config_file} not found. Please create it.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {config_file}. Check syntax.")
        return

    map_settings = config["map_settings"]
    interior_settings = config["interior_map_settings"]
    game_settings = config["game_settings"]
    building_definitions = config["building_definitions"]
    image_paths = config["image_paths"]

    clock = pygame.time.Clock()
    ARRAY_ROWS = map_settings["array_rows"]
    ARRAY_COLS = map_settings["array_cols"]
    SEED = map_settings["seed"]

    TILE_SIZE = game_settings["tile_size"]
    
    SCREEN_WIDTH = game_settings["screen_width"]  
    SCREEN_HEIGHT = game_settings["screen_height"]

    CAPTION = f"{game_settings['caption']} (Seed: {SEED})"

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(CAPTION)


    square_width = TILE_SIZE
    square_height = TILE_SIZE


    # Generate outdoor map-
    outdoor_coordinate_grid, outdoor_tile_map = generate_layered_map(ARRAY_ROWS, ARRAY_COLS, map_settings, seed=SEED)
    placed_buildings_data = place_buildings_on_map(outdoor_coordinate_grid, game_settings["num_buildings"], building_definitions)


    #Load + Scale all textures
    all_tile_textures = {}
    fallback_colors = {
        "grassland": (34, 139, 34), 
        "water": (60, 120, 200),    
        "forest_tree": (30, 80, 0), 
        "tallgrass": (50, 160, 50), 
        "flowers": (200, 100, 200), 
        "wood_floor": (180, 140, 90), 
        "stone_wall": (100, 100, 100), 
        "door": (80, 40, 0) 
    }

    print("Loading tile textures...")
    for tile_type, path in image_paths.items():
        if tile_type not in ["player_base_path"]: 
            try:
                texture_original = pygame.image.load(path).convert_alpha()
                all_tile_textures[tile_type] = pygame.transform.scale(
                    texture_original, (square_width, square_height)
                )
            except pygame.error as e:
                print(f"Error loading {path}: {e}. Using fallback color for {tile_type}.")
                fallback_surface = pygame.Surface((square_width, square_height))
                fallback_surface.fill(fallback_colors.get(tile_type, (255, 0, 255))) 
                all_tile_textures[tile_type] = fallback_surface
    print("All tile textures loaded (or fallbacks created).")


    # Load building sprites
    building_images = {}
    print("Loading building images...")
    try:
        for b_type, b_info in building_definitions.items():
            building_sprite_original = pygame.image.load(b_info["file"]).convert_alpha()
            scaled_sprite = pygame.transform.scale(
                building_sprite_original,
                (b_info["width_tiles"] * square_width, 
                 b_info["height_tiles"] * square_height)
            )
            building_images[b_type] = scaled_sprite
        print("Building images loaded successfully.")
    except pygame.error as e:
        print(f"Couldn't load building images from individual files: {e}. Using fallback colored rectangles for buildings.")
        for b_type, b_info in building_definitions.items():
            fallback_surface = pygame.Surface((b_info["width_tiles"] * square_width, b_info["height_tiles"] * square_height))
            if b_type == "pokecenter":
                fallback_surface.fill((150, 0, 150)) 
            elif b_type == "bakery":
                fallback_surface.fill((100, 100, 100)) 
            building_images[b_type] = fallback_surface


    #Player Setup
    players = pygame.sprite.Group()

    player_images = {}
    directions = ["up", "down", "left", "right"]
    player_base_path = image_paths["player_base_path"]
    print("Loading player images...")
    for direction in directions:
        player_images[direction] = []
        for frame_num in [1, 2, 3, 4]: 
            try:
                img = pygame.image.load(f"{player_base_path}{direction}{frame_num}.png").convert_alpha()
                img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                player_images[direction].append(img)
            except pygame.error as e:
                print(f"Missing image: {player_base_path}{direction}{frame_num}.png — using fallback")
                fallback = pygame.Surface((TILE_SIZE, TILE_SIZE))
                fallback.fill((255, 0, 0))  
                player_images[direction].append(fallback)
    print("Player images loaded (or fallbacks created).")
                
    start_x, start_y = 0, 0
    found_start = False
    for r in range(ARRAY_ROWS):
        for c in range(ARRAY_COLS):
            if outdoor_coordinate_grid[r, c] == 1: 
                start_x, start_y = c, r
                found_start = True
                break
        if found_start:
            break
    
    if not found_start:
        print("Could not find a valid starting position for the player (no path tiles available). Exiting.")
        pygame.quit()
        return

    player = Player(start_x, start_y, square_width, square_height, ARRAY_ROWS, ARRAY_COLS, player_images, game_settings)
    players.add(player)

    current_map_data = {
        "grid": outdoor_coordinate_grid,
        "tiles": outdoor_tile_map,
        "type": "outdoor",
        "tile_size": TILE_SIZE,
        "screen_width": SCREEN_WIDTH,
        "screen_height": SCREEN_HEIGHT
    }
    # Store outdoor map data for later use when coming from interior 
    outdoor_map_data = {
        'map_details': current_map_data.copy(), 
        'player_last_outdoor_pos': (player.grid_x, player.grid_y), 
        'buildings': placed_buildings_data 
    }

    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, ARRAY_COLS, ARRAY_ROWS, TILE_SIZE)


    #Main Game Loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                interaction_happened = False
                if event.key == pygame.K_UP and player.interaction_cooldown == 0:
                    if current_map_data["type"] == "outdoor":
                        for building_obj in placed_buildings_data:
                            ent_x, ent_y = building_obj["entrance_tile_world_coords"]
                            if player.grid_x == ent_x and player.grid_y == ent_y:
                                print(f"Interacting with {building_obj['type']} at ({ent_x}, {ent_y}) to enter.")
                                switch_to_indoor((ent_x, ent_y), interior_settings, game_settings)
                                interaction_happened = True
                                break
                    elif current_map_data["type"] == "indoor":
                        exit_r, exit_c = current_map_data["exit_point"]
                        if player.grid_x == exit_c and player.grid_y == exit_r: 
                             print("Interacting to exit interior.")
                             switch_to_outdoor()
                             interaction_happened = True
                             break
            
                if not interaction_happened:
                    dx, dy = 0, 0
                    if event.key == pygame.K_UP:
                        dy = -1
                    elif event.key == pygame.K_DOWN:
                        dy = 1
                    elif event.key == pygame.K_LEFT:
                        dx = -1
                    elif event.key == pygame.K_RIGHT:
                        dx = 1
                    
                    if dx != 0 or dy != 0:
                        player.set_moving_direction(dx, dy)
                        player.try_move(dx, dy, current_map_data["grid"], player.total_rows, player.total_cols, is_continuous=False)
            
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    player.clear_moving_direction()



        player.update(current_map_data["grid"])
        camera.update(player.rect)

        screen.fill((114,199,160)) 

        #Drawing Logic
        map_rows_to_draw, map_cols_to_draw = current_map_data["grid"].shape
        start_col = max(0, camera.camera_x // TILE_SIZE)
        end_col = min(map_cols_to_draw, (camera.camera_x + SCREEN_WIDTH) // TILE_SIZE + 1)
        start_row = max(0, camera.camera_y // TILE_SIZE)
        end_row = min(map_rows_to_draw, (camera.camera_y + SCREEN_HEIGHT) // TILE_SIZE + 1)

        for row_idx in range(start_row, end_row):
            for col_idx in range(start_col, end_col):
                world_x, world_y = col_idx * TILE_SIZE, row_idx * TILE_SIZE
                draw_x, draw_y = camera.apply_pixel_coords(world_x, world_y)
                
                tile_type = current_map_data["tiles"][row_idx][col_idx]

                if tile_type in all_tile_textures:
                    screen.blit(all_tile_textures[tile_type], (draw_x, draw_y))
                else: 
                    pygame.draw.rect(screen, (255, 0, 255), (draw_x, draw_y, TILE_SIZE, TILE_SIZE))


        if current_map_data["type"] == "outdoor":
            for building_obj in placed_buildings_data:
                world_x, world_y = building_obj["grid_x"] * square_width, building_obj["grid_y"] * square_height
                draw_x, draw_y = camera.apply_pixel_coords(world_x, world_y)
                
                building_pixel_width = building_obj["width_tiles"] * square_width
                building_pixel_height = building_obj["height_tiles"] * square_height
                
                if (draw_x + building_pixel_width > 0 and draw_x < SCREEN_WIDTH and
                    draw_y + building_pixel_height > 0 and draw_y < SCREEN_HEIGHT):
                    
                    building_sprite = building_images.get(building_obj["type"])
                    if building_sprite:
                        screen.blit(building_sprite, (draw_x, draw_y))
                    else:
                        pygame.draw.rect(screen, (255, 0, 255), (draw_x, draw_y,
                                                                building_pixel_width,
                                                                building_pixel_height))


        screen.blit(player.image, camera.apply(player.rect))
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print("Pygame visualizer closed.")


if __name__ == "__main__":
    run_pygame_visualizer()