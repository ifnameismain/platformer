import pygame as pg
import math
import json
import random
from pg_funcs import *


class Physics2D:
    def __init__(self, x, y, w, h, g=1):
        self.x = x
        self.y = y
        self.h = h
        self.w = w
        self.v = [0, 0]
        self.g = g
        self.rect = pg.Rect(x, y, w, h)
        self.vert_collisions = []
        self.hori_collisions = []
        self.colliding = {key: False for key in ['up', 'down', 'left', 'right']}

    def move(self, objs, obj_types=None):
        if obj_types is None:
            obj_types = [1] * len(objs)
        self.x += self.v[0]
        self.y += self.v[1]
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        for key in ['up', 'down', 'left', 'right']:
            self.colliding[key] = False
        self.check_collisions(objs)
        for collide, collide_type in zip(self.hori_collisions, obj_types):
            if collide_type == 1:
                if self.rect.centerx < collide.centerx:
                    self.rect.right = collide.left
                    self.colliding['right'] = True
                else:
                    self.rect.left = collide.right
                    self.colliding['left'] = True
            elif collide_type == 2: # underwater etc
                pass
            elif collide_type == 0: # checking for collisions of non walls (like coins)
                pass
        for collide, collide_type in zip(self.vert_collisions, obj_types):
            if collide_type == 1:
                if self.v[1] < 0:
                    if self.rect.bottom >= collide.bottom:
                        self.rect.top = collide.bottom
                        self.colliding['up'] = True
                elif self.v[1] > 0:
                    self.rect.bottom = collide.top
                    self.colliding['down'] = True
            elif collide_type == 2: # underwater etc
                pass
            elif collide_type == 0: # checking for collisions of non walls (like coins)
                pass
        if True in [self.colliding[x] for x in ['left', 'right']]:
            self.x = self.rect.x
        if True in [self.colliding[x] for x in ['up', 'down']]:
            self.y = self.rect.y
        self.calculate_velocity()

    def check_collisions(self, objs):
        self.vert_collisions = []
        self.hori_collisions = []
        for obj in objs:
            if obj.collidepoint(self.rect.midbottom):
                self.vert_collisions.append(obj)
            elif obj.collidepoint(self.rect.midtop):
                self.vert_collisions.append(obj)
            elif obj.collidepoint(self.rect.midleft):
                self.hori_collisions.append(obj)
            elif obj.collidepoint(self.rect.midright):
                self.hori_collisions.append(obj)

    def calculate_velocity(self):
        if self.colliding['down']:
            self.v[1] = 0
        if self.v[1] > 6:
            self.v[1] = 6
        else:
            self.v[1] += 0.2*self.g


class Entity(Physics2D):
    animations = {}

    def __init__(self, x, y, w, h, animation_path):
        super().__init__(x, y, w, h)
        self.animate_index = None
        self.animate_list = None
        self.angle = 0  # degrees not radians
        self.animation_type = animation_path.split('\\')[-1].replace('static/', '')[:-1]
        if self.animation_type not in Entity.animations.keys():
            Entity.animations[self.animation_type] = load_entity_animations(animation_path)[self.animation_type]
        self.animation = 'idle'
        self.flipped = False
        self.animation_timer = 0
        self.x_middle = 0
        self.y_middle = 0
        self.animation_index = 0

    def set_pos(self, x, y):
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

    def draw(self, surface):
        if self.flipped:
            surface.blit(flip_image(Entity.animations[self.animation_type][self.animation][self.animation_index].copy()), (self.x, self.y))
        else:
            surface.blit(Entity.animations[self.animation_type][self.animation][self.animation_index].copy(), (self.x, self.y))

    def draw_centre(self, surface):
        if self.flipped:
            surface.blit(
                flip_image(Entity.animations[self.animation_type][self.animation][self.animation_index].copy()),
                (self.x_middle - self.w//2, self.y_middle - self.h//2))
        else:
            surface.blit(Entity.animations[self.animation_type][self.animation][self.animation_index].copy(),
                         (self.x_middle - self.w//2, self.y_middle - self.h//2))


class Map:
    def __init__(self, x_size, y_size, tile_size):
        self.tiles, self.tile_paths, self.tile_addons = load_tile_sequence('static/textures')
        self.tiles.extend(load_sprites('static/sprites'))
        self.chunks = {}
        self.x_size = x_size
        self.y_size = y_size
        self.tile_size = tile_size
        self.map = None
        self.load_map()

    def load_map(self):
        with open('static/levels/first.json', 'r') as f:
            self.map = json.load(f)

    def blit_map(self, surface, offset):
        x, y = surface.get_size()
        for row_count, row in enumerate(self.map):
            for tile_count, tile in enumerate(row):
                x_pos = tile_count * self.tile_size - offset[0]
                y_pos = row_count * self.tile_size - offset[1]
                r = pg.Rect(x_pos, y_pos, self.tile_size, self.tile_size)
                if 0 < r.x < x or x > r.x + r.w > 0:
                    if tile != -1:
                        surface.blit(self.tiles[tile].copy(), (x_pos, y_pos))
                        if 0 <= tile <= len(self.tile_paths) - 1:
                            if self.tile_paths[tile] in self.tile_addons.keys():
                                addons = self.tile_addons[self.tile_paths[tile]]
                                for t, xx, yy in zip([0, 1, 2, 3], [0, 1, -1, 0], [-1, 0, 0, 1]):
                                    try:
                                        if self.map[row_count + yy][tile_count + xx] != 1:
                                            surface.blit(addons[t].copy(), (x_pos, y_pos))
                                    except:
                                        surface.blit(addons[t].copy(), (x_pos, y_pos))
                    else:
                        pass
                else:
                    pass

    def get_map_collisions(self, entity):
        collisions = []
        e_x, e_y, e_w,e_h = entity
        for row_index, row in enumerate(self.map):
            y_size = row_index * self.tile_size
            if e_y > y_size + self.tile_size:
                continue
            elif e_y+e_h < y_size:
                break
            for tile_index, tile in enumerate(row):
                x_size = tile_index*self.tile_size
                if tile == 1:
                    if e_x > x_size + self.tile_size:
                        continue
                    elif e_x + e_w < x_size:
                        break
                    collisions.append(pg.Rect(x_size,
                                              y_size,
                                              self.tile_size, self.tile_size))
        return collisions

    def initial_chunk(self):
        self.chunks["0:0"] = [
            [0 if line < 0.7*self.y_size//self.tile_size else 1]*int(self.x_size//self.tile_size) for line in
            range(self.y_size//self.tile_size)]

    def generate_chunk(self, x, y, noise_function=None):
        self.chunks[f"{x}:{y}"] = [
            [0 if line < 0.6*self.y_size//self.tile_size else 1]*int(self.x_size//self.tile_size)
            for line in range(self.y_size//self.tile_size)]

    def get_chunk_collisions(self, x, y, entity):
        collisions = []
        if f"{int(x)}:{int(y)}" not in self.chunks.keys():
            self.generate_chunk(x, int(y))
        if entity is not None:
            e_x, e_y, e_w,e_h = entity
            for row_index, row in enumerate(self.chunks[f"{int(x)}:{int(y)}"]):
                y_size = y * self.y_size + row_index * self.tile_size
                if e_y > y_size + self.tile_size:
                    continue
                elif e_y+e_h < y_size:
                    break
                for tile_index, tile in enumerate(row):
                    x_size = x*self.x_size + tile_index*self.tile_size
                    if tile == 1:
                        if e_x > x_size + self.tile_size:
                            continue
                        elif e_x + e_w < x_size:
                            break
                        collisions.append(pg.Rect(x_size,
                                                  y_size,
                                                  self.tile_size, self.tile_size))
        else:
            for row_index, row in enumerate(self.chunks[f"{int(x)}:{int(y)}"]):
                y_size = y * self.y_size + row_index * self.tile_size
                for tile_index, tile in enumerate(row):
                    x_size = x*self.x_size + tile_index*self.tile_size
                    if tile == 1:
                        collisions.append(pg.Rect(x_size,
                                                  y_size,
                                                  self.tile_size, self.tile_size))
        return collisions

    def blit_chunk(self, surface, x_index, y_index, offset=(0, 0)):
        x, y = surface.get_size()
        for xx in range(-1, 2):
            if f"{int(x_index+xx)}:{int(y_index)}" not in self.chunks.keys():
                self.generate_chunk(x_index+xx, int(y_index))
            chunk = self.chunks[f"{int(x_index+xx)}:{int(y_index)}"]
            for row_index, row in enumerate(chunk):
                for tile_index, tile in enumerate(row):
                    x_pos = (x_index+xx)*self.x_size + tile_index*self.tile_size + offset[0]
                    y_pos = y_index*self.y_size + row_index*self.tile_size + offset[1]
                    r = pg.Rect(x_pos, y_pos, self.tile_size, self.tile_size)
                    if 0 < r.x < x or x > r.x + r.w > 0:
                        if tile == 1:
                            if chunk[row_index-1][tile_index] != 1:
                                surface.blit(self.textures[1], (x_pos, y_pos))
                            else:
                                surface.blit(self.textures[0], (x_pos, y_pos))
                        else:
                            pg.draw.rect(surface, (204, 255, 255), r)
                    elif r.x > x:
                        break
