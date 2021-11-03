import math
import random
import pygame as pg


class Water:
    def __init__(self, p1, p2):
        self.p1 = p1[0]
        self.surface_height = p1[1] - 8
        self.target_height = 8
        self.p2 = p2[0]
        self.divider_amount = 2
        self.length = (self.p2-self.p1)//self.divider_amount + 1
        self.points = [(self.divider_amount*x, self.target_height) for x in range(self.length+1)]
        self.springs = [self.target_height for _ in range(self.length)]
        self.distances = [0]*len(self.springs)
        self.speeds = [0]*len(self.springs)
        self.heights = [self.target_height]*len(self.springs)
        self.lDeltas = [0]*len(self.springs)
        self.rDeltas = [0]*len(self.springs)

        self.number_of_loops = 1
        self.tension = 0.035
        self.dampening = 0.020
        self.spread = 0.25
        self.timer = 0

        self.last_vh = 0
        self.started = False

    def spring_set(self):
        for i in range(self.length):
            self.distances[i] = self.target_height - self.heights[i]
            self.speeds[i] += self.tension*self.distances[i] - self.speeds[i]*self.dampening
            self.heights[i] += self.speeds[i]

    def delta_calculation(self):
        for j in range(self.number_of_loops):
            for i in range(self.length):
                if i > 0:
                    self.lDeltas[i] = self.spread*(self.heights[i] - self.heights[i-1])
                    self.springs[i-1] += self.lDeltas[i]
                if i < self.length - 1:
                    self.rDeltas[i] = self.spread * (self.heights[i] - self.heights[i + 1])
                    self.springs[i + 1] += self.rDeltas[i]
            self.terminate_delta()

    def terminate_delta(self):
        for i in range(self.length):
            if i > 0:
                self.heights[i - 1] += self.lDeltas[i]
            if i < self.length - 1:
                self.heights[i + 1] += self.rDeltas[i]

    def run(self, entity, vh, vx):
        ex, ey, ew, eh = entity
        i = int(ex + (ew/2))
        if 0 < vh < self.last_vh:
            self.started = False
        elif 0 > self.last_vh and vh >= 0:
            self.started = False
        if self.points[0][0] < ex - self.p1 and self.points[-1][0] > ex + ew - self.p1:
            if ey - self.surface_height < self.points[0][1] < ey + eh - self.surface_height:
                if vh not in [0, 0.2] and not self.started:
                    self.speeds[(i-self.p1)//self.divider_amount] = 5 *(vh/abs(vh))
                    self.started = True
                    self.timer = 0
                elif vx != 0:
                    if -2 < self.speeds[(i + 6 - self.p1) // self.divider_amount] < 2:
                        self.speeds[(i + 6*int((vx / abs(vx))) - self.p1) // self.divider_amount] = -0.4
                        self.timer = 0
        self.last_vh = vh
        self.spring_set()
        self.delta_calculation()
        self.timer += 1
        if self.timer > 180:
            self.test_end_water_waves()

    def test_end_water_waves(self):
        """Check if the waves are still alive"""

        count = 0

        for i in range(self.length):
            if not int(self.speeds[i]) and not int(self.distances[i]):
                count += 1

        if count == self.length:
            self.stop_water_motion()

    def stop_water_motion(self):
        """Stop the motion of the water"""

        for i in range(self.length):
            self.speeds[i] = 0
            self.heights[i] = self.target_height
            self.distances[i] = 0

    def draw(self, surface, offset):
        s = pg.Surface((self.p2-self.p1, 16))
        points = [(self.points[x][0], self.heights[x]) for x in range(self.length)]
        points.append((self.length*self.divider_amount, 16))
        points.insert(0, (0, 16))
        pg.draw.polygon(s, (35, 150, 230), points)
        pg.draw.lines(s, (255, 255, 255), False, points[1:-1])
        s.set_colorkey((0, 0, 0))
        s.set_alpha(100)
        surface.blit(s, (self.p1-offset[0], self.surface_height - offset[1]))


class Cloth:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.max_points = 10
        self.h = h
        self.cloth = []
        self.vel = []
        self.resting_distance = [1,1]
        self.generate_cloth()
        self.previous_cloth = self.cloth
        self.timer = 0
        self.max_timer = 360
        self.mag = 0
        self.dt = 0.2
        self.acc = (0,2)
        self.calculate_precision = 5

    def generate_cloth(self):
        self.resting_distance = [1 if self.w < 11 else self.w/10, 1 if self.h < 11 else self.h/10]
        self.cloth = [[[self.x+self.resting_distance[0]*x, self.y+self.resting_distance[1]*y] for x in range(
            self.max_points if self.w > 10 else self.w)] for y in range(self.max_points if self.h > 10 else self.h)]
        self.vel = [[[0,0]]*len(self.cloth[0])]*len(self.cloth)

    def update(self):
        temp_cloth = self.cloth
        self.wind_blow()
        self.verlet_integration()
        for _ in range(self.calculate_precision):
            self.linked_calculation()
        self.cloth[0] = [[self.x+self.resting_distance[0]*x, self.y] for x in range(
            self.max_points if self.w > 10 else self.w)]
        self.previous_cloth = temp_cloth

    def wind_blow(self):
        if self.timer == self.max_timer:
            self.mag = random.randint(-6,6)
            self.timer = 0
        for row_count, row in enumerate(self.cloth):
            for count, point in enumerate(row):
                point[0] += row_count*row_count*self.mag/500
        self.timer += 1

    def verlet_integration(self):
        for row, vr, pr in zip(self.cloth[1:], self.vel[1:], self.previous_cloth[1:]):
            for point, v, prev in zip(row, vr, pr):
                for i in [0, 1]:
                    v[i] = point[i] - prev[i]
                    point[i] += v[i] + self.acc[i]*self.dt

    def linked_calculation(self):
        self.cloth[0] = [[self.x+self.resting_distance[0]*x, self.y] for x in range(
            self.max_points if self.w > 10 else self.w)]
        for row_count, row in enumerate(self.cloth):
            for count, point in enumerate(row):
                if row_count != 0:
                    point, self.cloth[row_count-1][count] = self.link_constraint(point, self.cloth[row_count-1][count])
                if count != 0 and row_count != 0:
                    point, row[count-1] = self.link_constraint(point, row[count-1])

    def link_constraint(self, p1, p2):
        d = [0, 0]
        translate = [0, 0]
        for i in [0, 1]:
            d[i] = p1[i] - p2[i]
        sd = math.sqrt(d[0]*d[0]+d[1]*d[1])
        diff = []
        for i in [0,1]:
            diff.append((self.resting_distance[i]-sd)/sd)
        for i in [0, 1]:
            translate[i] = d[i]*0.5*diff[i]
            p1[i] += translate[i]
            p2[i] -= translate[i]
        return p1, p2

    def draw(self, surface):
        points = []
        ly = len(self.cloth)
        lx = len(self.cloth[0])
        for i in [lx-1, 0]:
            points.append(self.cloth[0][i])
        for i in range(1, ly):
            points.append(self.cloth[i][0])
        for i in range(1, lx-1):
            points.append(self.cloth[ly-1][i])
        x = []
        for i in range(1, ly):
            x.append(self.cloth[i][lx-1])
        x.reverse()
        points.extend(x)
        pg.draw.polygon(surface, (125, 255, 125), points)
