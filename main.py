import os
from pg_classes import *
from physics import *
import time
# GLOBALS
GAME_CAPTION = "Platformer"
UNSCALED_SIZE = (480, 272)
SCALED_SIZE = (1920//2, 1080//2)


CONTROLS = {'player': {'up': pg.K_w, 'down': pg.K_s, 'left': pg.K_a, 'right': pg.K_d}}


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 16, 32, "static/player/")
        self.moving = {key: False for key in ['left', 'right', 'up', 'down']}
        self.movement_speed = 2
        self.double = False
        self.double_waiting = False
        self.x_middle = UNSCALED_SIZE[0]//2
        self.y_middle = UNSCALED_SIZE[1]//2
        self.offset = [self.x - self.x_middle, self.y - self.y_middle]
        self.animation_dict = {key: len(value) for key, value in Entity.animations['player'].items()}

    def check_key_up(self, key):
        for d, k in zip(['up', 'down', 'left', 'right'],
                                [CONTROLS['player'][direction] for direction in ['up', 'down', 'left', 'right']]):
            if key == k:
                self.movement(d, False)

    def check_key_down(self, key):
        for d, k in zip(['up', 'down', 'left', 'right'],
                                [CONTROLS['player'][direction] for direction in ['up', 'down', 'left', 'right']]):
            if key == k:
                self.movement(d, True)

    def check_movement(self):
        if self.double_waiting and not self.moving['up']:
            self.double = True
        if self.moving['up']:
            if self.double:
                self.double_jump()
            else:
                self.jump()
        if self.moving['left']:
            self.v[0] = -self.movement_speed
            self.flipped = True
        elif self.moving['right']:
            self.v[0] = self.movement_speed
            self.flipped = False
        else:
            self.v[0] = 0
        self.animate()

    def animate(self):
        if True in [self.moving[x] for x in ['left', 'right']]:
            self.animation = 'walking'
            self.animation_timer += 1
            if self.animation_timer % 10 == 0:
                self.animation_index += 1
                if self.animation_index >= self.animation_dict[self.animation]:
                    self.animation_index = 0
        else:
            self.animation_timer = 0
            self.animation = 'idle'
            self.animation_index = 0

    def movement(self, key, boolean):
        self.moving[key] = boolean

    def jump(self):
        if self.colliding['down']:
            self.v[1] = - 3
            self.double_waiting = True

    def double_jump(self):
        self.v[1] = - 3
        self.double = False
        self.double_waiting = False


class _Screen:
    def __init__(self, parent):
        self.parent = parent

    def draw(self):
        pass

    def run(self):
        pass

    def reset(self):
        pass

    def check_event(self, event):
        pass


class MenuScreen(_Screen):
    def __init__(self, parent):
        _Screen.__init__(self, parent=parent)
        self.buttons = [
            create_button((150, 150), (300, 100), text="Play", font=FONTS['MEDIUM']),
            create_button((150, 400), (300, 100), text="Options", font=FONTS['MEDIUM']),
        ]
        self.switch_screen = ["game", "options"]

    def check_event(self, event):
        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                x, y = get_mouse()
                for button, command in zip(self.buttons, self.switch_screen):
                    if button[0][0].collidepoint(x, y):
                        self.parent.screen = SCREENS[command]

    def draw(self):
        window = self.parent.window
        window.fill((204, 255, 255))
        for button in self.buttons:
            window.fill(button[0][1], button[0][0])
            blit_text_object(window, button[1])


class OptionsScreen(_Screen):
    def __init__(self, parent):
        _Screen.__init__(self, parent)


class ControlsScreen(_Screen):
    def __init__(self, parent):
        _Screen.__init__(self, parent)


class GameScreen(_Screen):
    def __init__(self, parent):
        _Screen.__init__(self, parent)
        self.player = Player(200, 0)
        self.map = Map(UNSCALED_SIZE[0], UNSCALED_SIZE[1], 16)
        self.map_floor = len(self.map.map) * self.map.tile_size
        self.keys_down = []
        self.water = []
        self.group_water_tiles()
        # self.cloth = Cloth(100,100,60,80)

    def run(self):
        self.player.check_movement()
        collision_list = []
        collision_list.extend(self.map.get_map_collisions([self.player.x, self.player.y, self.player.w,
                                                           self.player.h]))
        self.player.move(collision_list)
        if self.player.y > self.map_floor:
            self.player.x = 200
            self.player.y = 0
        self.player.offset[1] = self.player.y - self.player.y_middle + 16
        self.player.offset[0] = self.player.x - self.player.x_middle + 8
        self.cloth.update()
        if self.water:
            for x in self.water:
                x.run([self.player.x, self.player.y, self.player.w, self.player.h], self.player.v[1], self.player.v[0])

    def group_water_tiles(self):
        index = 0
        water_list = []
        avoid_list = []
        for ind, x in enumerate(self.map.tile_paths):
            if 'water' in x:
                index = ind
                break
        for row_count, row in enumerate(self.map.map):
            start = -1
            for tile_count, tile in enumerate(row[:-1]):
                if tile == index and (row_count - 1, tile_count) not in avoid_list:
                    avoid_list.append((row_count, tile_count))
                    if start == -1:
                        start = tile_count
                    if row[tile_count + 1] != index:
                        water_list.append((start, tile_count, row_count))
                        for x in range(start, tile_count+1):
                            row[x] = -1

                        start = -1
        self.water = [Water((x[0]*self.map.tile_size, x[2]*self.map.tile_size + self.map.tile_size/2),
                            (x[1]*self.map.tile_size + self.map.tile_size,
                             x[2]*self.map.tile_size + self.map.tile_size/2)) for x in water_list]

    def check_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.parent.game_running = False
            elif event.key in CONTROLS['player'].values():
                self.player.check_key_down(event.key)
        elif event.type == pg.KEYUP:
            if event.key in CONTROLS['player'].values():
                self.player.check_key_up(event.key)

    def draw(self):
        self.parent.window.fill((204, 255, 255))
        self.player.draw_centre(self.parent.window)
        self.map.blit_map(self.parent.window, self.player.offset)
        if self.water:
            for x in self.water:
                x.draw(self.parent.window, self.player.offset)
        self.cloth.draw(self.parent.window)


class Controller:
    def __init__(self):
        self.display = pg.display.get_surface()
        self.window = pg.Surface(UNSCALED_SIZE)
        self.game_running = True
        self.clock = pg.time.Clock()
        self.frame_rate = 60
        self.screen = None

    def get_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.game_running = False
            else:
                self.screen.check_event(event)

    def main_loop(self):
        self.screen = SCREENS['game']
        while self.game_running:
            self.clock.tick(self.frame_rate)
            self.get_events()
            self.screen.run()
            self.screen.draw()
            self.display.blit(pg.transform.scale(self.window, SCALED_SIZE), (0, 0))
            pg.display.update()
        pg.quit()


if __name__ == '__main__':
    os.environ["SDL_VIDEO_CENTERED"] = "True"
    pg.display.init()
    pg.font.init()
    FONTS = {"BIG": pg.font.SysFont("arial", 100, True),
             "MEDIUM": pg.font.SysFont("arial", 50, True),
              "SMALL": pg.font.SysFont("arial", 30, True)}
    pg.display.set_caption(GAME_CAPTION)
    display_info = pg.display.Info()
    SCREEN_SIZE = (display_info.current_w, display_info.current_h)
    pg.display.set_mode(SCALED_SIZE)
    controller = Controller()
    SCREENS = {'menu': MenuScreen(controller), 'options': OptionsScreen(controller),
               'controls': ControlsScreen(controller), 'game': GameScreen(controller)}
    controller.main_loop()

