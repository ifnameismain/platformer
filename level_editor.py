import os
import json
from pg_funcs import *

GAME_CAPTION = "Level Editor for Pygame"
UNSCALED_SIZE = (480, 272)
SCALED_SIZE = (960, 544)

MOUSE_LEFT = 1
MOUSE_RIGHT = 3
SCROLL_UP = 4
SCROLL_DOWN = 5
SCROLL_AMOUNT = 10
SX = SCALED_SIZE[0]/UNSCALED_SIZE[0]
SY = SCALED_SIZE[1]/UNSCALED_SIZE[1]


class Screen:
    def __init__(self):
        self.zoom = 10
        self.ui = pg.Surface((50*(SX/2), UNSCALED_SIZE[1]))
        self.window = pg.Surface(UNSCALED_SIZE)
        self.tile_size = 16
        self.tiles, self.tile_paths, self.tile_addons = load_tile_sequence("static/textures")
        self.tiles.extend(load_sprites('static/sprites'))
        self.map_offset = [-100, -20]
        self.scroll = 0
        self.map_move = 0
        self.expand_modifier = False
        self.placing_blocks = False
        self.selected_index = 0
        self.selected_tile = None
        self.prev_mouse_pos = pg.mouse.get_pos()
        self.mouse_pos = self.prev_mouse_pos
        self.map_path = "static/levels/first.json"
        with open(self.map_path, 'r') as f:
            self.map = json.load(f)

    def save_level(self):
        with open(self.map_path, 'w') as f:
            json.dump(self.map, f)
        print('saved map :)')

    def reset_level(self):
        self.map = [[-1 for x in range(len(self.map[0]))] for _ in range(len(self.map))]

    def expand_map(self, direction):
        if not self.expand_modifier:
            if direction == 'left':
                self.map = [[-1 if x == 0 else self.map[_][x-1] for x in range(len(self.map[0])+1)] for _ in range(len(self.map))]
            elif direction == 'right':
                self.map = [[-1 if x == len(self.map[0]) else self.map[_][x] for x in range(len(self.map[0])+1)] for _ in range(len(self.map))]
            elif direction == 'down':
                self.map = [[self.map[_][x] for x in range(len(self.map[0]))] if _ != len(self.map) else [-1]*len(self.map[0]) for _ in range(len(self.map)+1)]
            else:
                self.map = [[self.map[_-1][x] for x in range(len(self.map[0]))] if _ != 0 else [-1]*len(self.map[0]) for _ in range(len(self.map)+1)]
        else:
            if direction == 'left':
                self.map = [[self.map[_][x] for x in range(1, len(self.map[0]))] for _ in
                            range(len(self.map))]
            elif direction == 'right':
                self.map = [[self.map[_][x] for x in range(len(self.map[0])-1)] for _ in
                            range(len(self.map))]
            elif direction == 'down':
                self.map = self.map[:-1]
            else:
                self.map = self.map[1:]

    def outline_tile(self, index):
        if index == self.selected_index:
            self.selected_tile = None
            self.selected_index = -1
        else:
            self.selected_tile = pg.Rect(16, 30 * index + 19 + self.scroll, 18, 18)

    def blit_ui(self):
        if self.selected_tile is not None:
            pg.draw.rect(self.ui, (255, 255, 255), self.selected_tile)
        for index, image in enumerate(self.tiles):
            self.ui.blit(image.copy(), (17*(SX/2), (30 * index + 20 + self.scroll)*(SX/2)))

    def blit_map(self):
        for row_count, row in enumerate(self.map):
            for tile_count, tile in enumerate(row):
                if tile_count == 0:
                    text = centred_text(f"{row_count}", FONTS['SMALL'],
                                        (tile_count * self.tile_size - self.map_offset[0] - 8,
                                         row_count * self.tile_size - self.map_offset[1] + 8), (0, 0, 0))
                    blit_text_object(self.window, text)
                if row_count == 0:
                    text = centred_text(f"{tile_count}", FONTS['SMALL'],
                                        (tile_count * self.tile_size - self.map_offset[0] + 8,
                                         - self.map_offset[1] - 8), (0, 0, 0))
                    blit_text_object(self.window, text)
                if tile == -1:
                    r = pg.Rect(tile_count*self.tile_size - self.map_offset[0],
                                row_count*self.tile_size - self.map_offset[1],
                                self.tile_size, self.tile_size)
                    pg.draw.rect(self.window, (204, 255, 255), r, width=1)
                else:
                    self.window.blit(self.tiles[tile].copy(), (tile_count*self.tile_size - self.map_offset[0],
                                     row_count*self.tile_size - self.map_offset[1]))
                    if 0 <= tile <= len(self.tile_paths)-1:
                        if self.tile_paths[tile] in self.tile_addons.keys():
                            addons = self.tile_addons[self.tile_paths[tile]]
                            for t, x, y in zip([0,1,2,3], [0, 1, -1, 0], [-1, 0, 0, 1]):
                                if 0 <= tile_count + x < len(row):
                                    try:
                                        if self.map[row_count+y][tile_count+x] != 1:
                                            self.window.blit(addons[t].copy(), (tile_count * self.tile_size - self.map_offset[0],
                                                            row_count * self.tile_size - self.map_offset[1]))
                                    except:
                                        self.window.blit(addons[t].copy(),
                                                         (tile_count * self.tile_size - self.map_offset[0],
                                                          row_count * self.tile_size - self.map_offset[1]))

    def run(self):
        if self.scroll > 0:
            self.scroll = 0
        if self.placing_blocks:
            if - self.map_offset[0] < self.mouse_pos[0] < - self.map_offset[0] + self.tile_size * len(self.map[0]) and \
                    - self.map_offset[1] < self.mouse_pos[1] < - self.map_offset[1] + self.tile_size * len(self.map):
                self.map[int((self.mouse_pos[1] + self.map_offset[1]) // self.tile_size)][int(
                    (self.mouse_pos[0] + self.map_offset[0]) // self.tile_size)] = self.selected_index

        if self.map_move:
            for x in [0, 1]:
                self.map_offset[x] -= self.mouse_pos[x]-self.prev_mouse_pos[x]
        self.draw()
        self.prev_mouse_pos = self.mouse_pos
        if self.mouse_pos[0] > 50 and self.selected_tile is not None:
            if - self.map_offset[0] < self.mouse_pos[0] < - self.map_offset[0] + self.tile_size*len(self.map[0]) and \
                    - self.map_offset[1] < self.mouse_pos[1] < - self.map_offset[1] + self.tile_size*len(self.map):
                self.window.blit(self.tiles[self.selected_index].copy(),
                                 (self.tile_size*((self.mouse_pos[0] + self.map_offset[0])//self.tile_size) - self.map_offset[0],
                                  self.tile_size*((self.mouse_pos[1] + self.map_offset[1])//self.tile_size) - self.map_offset[1]))
            else:
                self.window.blit(self.tiles[self.selected_index].copy(), (self.mouse_pos[0]-8, self.mouse_pos[1]-8))

    def check_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == SCROLL_UP:
                if self.mouse_pos[0] < 50:
                    self.scroll += SCROLL_AMOUNT
                else:
                    self.zoom += 0.2
            elif event.button == SCROLL_DOWN:
                if self.mouse_pos[0] < 50:
                    if self.scroll + SCALED_SIZE[1] < 30 * len(self.tiles) + 20:
                        self.scroll -= SCROLL_AMOUNT
                else:
                    self.zoom -= 0.2
            elif event.button == MOUSE_RIGHT:
                if self.mouse_pos[0] > 50:
                    self.map_move = True
            elif event.button == MOUSE_LEFT:
                if self.selected_tile is not None:
                    self.placing_blocks = True
                else:
                    self.placing_blocks = True
                    self.selected_index = -1
        if event.type == pg.MOUSEBUTTONUP:
            if event.button == MOUSE_RIGHT:
                if self.mouse_pos[0] > 50:
                    self.map_move = False
            elif event.button == MOUSE_LEFT:
                self.placing_blocks = False
                if self.mouse_pos[0] < 50:
                    for y in range(len(self.tiles)):
                        if 17 < self.mouse_pos[0] < 33 and 30*y+20-self.scroll < self.mouse_pos[1] < 30*y+36-self.scroll:
                            self.outline_tile(y)
                            self.selected_index = y
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_LCTRL:
                self.expand_modifier = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.selected_tile = None
            elif event.key == pg.K_s:
                self.save_level()
            elif event.key == pg.K_r:
                self.reset_level()
            elif event.key == pg.K_LCTRL:
                self.expand_modifier = False
            elif event.key == pg.K_LEFT:
                self.expand_map('left')
            elif event.key == pg.K_RIGHT:
                self.expand_map('right')
            elif event.key == pg.K_DOWN:
                self.expand_map('down')
            elif event.key == pg.K_UP:
                self.expand_map('up')

    def draw(self):
        self.ui.fill((96, 96, 96))
        self.window.fill((224, 224, 224))
        self.blit_map()
        self.blit_ui()


class Controller:
    def __init__(self):
        self.display = pg.display.get_surface()
        self.game_running = True
        self.clock = pg.time.Clock()
        self.frame_rate = 60
        self.screen = Screen()

    def get_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.game_running = False
            else:
                self.screen.check_event(event)

    def main_loop(self):
        while self.game_running:
            self.clock.tick(self.frame_rate)
            x,y = pg.mouse.get_pos()
            self.screen.mouse_pos = (x/SX, y/SY)
            self.get_events()
            self.screen.run()
            self.display.blit(pg.transform.scale(self.screen.window, (SCALED_SIZE[0], SCALED_SIZE[1])), (0, 0))
            self.display.blit(pg.transform.scale(self.screen.ui, (int(100*SX//2), SCALED_SIZE[1])), (0, 0))
            pg.display.update()
        pg.quit()


if __name__ == '__main__':
    os.environ["SDL_VIDEO_CENTERED"] = "True"
    pg.display.init()
    pg.font.init()
    FONTS = {"BIG": pg.font.SysFont("arial", 100, True),
             "MEDIUM": pg.font.SysFont("arial", 50, True),
             "SMALL": pg.font.SysFont("arial", 10, True)}
    pg.display.set_caption(GAME_CAPTION)
    display_info = pg.display.Info()
    SCREEN_SIZE = (display_info.current_w, display_info.current_h)
    pg.display.set_mode(SCALED_SIZE)
    Controller().main_loop()


