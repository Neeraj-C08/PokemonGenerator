import pygame
import sys

pygame.init()

TILE_SIZE = 32

maze_layout = [
    "1010101010101010101010101010",
    "0101010101010101010101010101",
    "1010101010101010101010101010",
    "0101010101010101010101010101",
    "1010101010101010101010101010",
    "0101010101010101010101010101",
    "1010101010101010101010101010",
    "0101010101010101010101010101",
    "1010101010101010101010101010",
    "0101010101010101010101010101",
    "1010101010101010101010101010",
    "0101010101010101010101010101",
    "1010101010101010101010101010",
    "0101010101010101010101010101",
    "1010101010101010101010101010",
    "0101010101010101010101010101",
]

maze = [list(row) for row in maze_layout]

ROWS = len(maze)
COLS = len(maze[0])

WIDTH, HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Random Pokémon Map")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def draw_maze():
    for y, row in enumerate(maze):
        for x, tile in enumerate(row):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if tile == '1':
                pygame.draw.rect(screen, BLACK, rect)
            elif tile == '0':
                pygame.draw.rect(screen, WHITE, rect)

running = True
while running:
    screen.fill(BLACK)
    draw_maze()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    clock.tick(60)

pygame.quit()
sys.exit()
