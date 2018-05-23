#!/usr/bin/python
"""Simple acceleration demo."""
import sys
import time
import sdl2
import sdl2.ext

BLACK = sdl2.ext.Color(0, 0, 0)
WHITE = sdl2.ext.Color(255, 255, 255)
INITIAL_VELOCITY = 0
USER_FORCE = -300 # Points in y-axis
INITIAL_GRAVITY = 9.82
WINDOW_SIZE = (800,600)
HEIGHT = 20.0
PPU = WINDOW_SIZE[1]/HEIGHT
WIDTH = WINDOW_SIZE[0]/PPU

# Instead of chopping away at a more C like invocation of SDL, we use a component based system.

class MovementSystem(sdl2.ext.Applicator):
    def __init__(self, minx, miny, maxx, maxy):
        super(MovementSystem, self).__init__()
        self.componenttypes = Position, Force, Acceleration, Velocity, sdl2.ext.Sprite
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.__oldtime = time.perf_counter()
        self.__newtime = time.perf_counter()
        self.__tstart = 0
        self.__gravity = INITIAL_GRAVITY

    def __deltaTime(self):
        '''Updates this instances time variable,
        and calculates the difference.'''
        self.__oldtime = self.__newtime
        self.__newtime = time.perf_counter()
        temp = self.__newtime - self.__oldtime
        self.__tstart += temp
        return temp

    def process(self, world, componentsets):
        print("PPU: " + str(PPU))
        print("HEIGHT: " + str(HEIGHT))
        print("WIDTH: " + str(WIDTH))
        delta = self.__deltaTime()
        for position, force, acceleration, velocity, sprite in componentsets:
            fx = sum(force.fx) + force.kfx
            fy = sum(force.fy) + force.kfy
            x = position.px
            y = position.py
            vx = velocity.vx
            vy = velocity.vy
            ax = acceleration.ax
            ay = acceleration.ay
            kax = acceleration.kax
            kay = acceleration.kay
            lx1 = self.minx
            ly1 = self.miny
            lx2 = self.maxx
            ly2 = self.maxy

            swidth, sheight = sprite.size
            
            lax = sum(ax) + kax + fx/force.mass
            lay = sum(ay) + kay + fy/force.mass

            #Scale to fit actual world size
            swidth = swidth/PPU
            sheight = sheight/PPU

            vx = vx+lax*delta
            vy = vy+lay*delta
            position.px = x+vx*delta
            position.py = y+vy*delta
            velocity.vx = vx
            velocity.vy = vy
            
            # Reset acceleration list
            acceleration.ax = []
            acceleration.ay = [INITIAL_GRAVITY]

            # Because of the acceleration parts, this no longer works.
            #position.px = max(self.minx, position.px)
            #position.py = max(self.miny, position.py)
            if position.px < self.minx:
                position.px = self.minx
                velocity.vx = 0
                # No constant acceleration in this axis
            if position.py < self.miny:
                position.py = self.miny
                velocity.vy = 0
            print("Position: " + str(position))


            pmaxx = position.px + swidth
            pmaxy = position.py + sheight
            if pmaxx > self.maxx:
                position.px = self.maxx - swidth
                velocity.vx = 0
            if pmaxy > self.maxy:
                position.py = self.maxy - sheight
                velocity.vy = 0
                acceleration.ay.append(-INITIAL_GRAVITY)

            # Reset forces and acceleration
            acceleration.ax = []
            acceleration.ay = [INITIAL_GRAVITY]
            force.fx = []
            force.fy = []

            sprite.x = int(round(position.px*PPU))
            sprite.y = int(round(position.py*PPU))
            print("Sprite: " + str(sprite.x) + ", " + str(sprite.y))

class SoftwareRenderSystem(sdl2.ext.SoftwareSpriteRenderSystem):
    def __init__(self, window):
        super(SoftwareRenderSystem, self).__init__(window)

    def render(self, components):
        sdl2.ext.fill(self.surface, BLACK)
        super(SoftwareRenderSystem, self).render(components)


class TextureRenderSystem(sdl2.ext.TextureSpriteRenderSystem):
    def __init__(self, renderer):
        super(TextureRenderSystem, self).__init__(renderer)
        self.renderer = renderer

    def render(self, components):
        tmp = self.renderer.color
        self.renderer.color = BLACK
        self.renderer.clear()
        self.renderer.color = tmp
        super(TextureRenderSystem, self).render(components)

class Position(object):
    def __init__(self):
        super(Position, self).__init__()
        self.px = 0.0
        self.py = 0.0
    def __str__(self):
        return "Position object, self.px: " + str(self.px) + ", self.py: " +  str(self.py) + " ."

class Velocity(object):
    def __init__(self):
        super(Velocity, self).__init__()
        self.vx = 0.0
        self.vy = 0.0

class Acceleration(object):
    def __init__(self):
        super(Acceleration, self).__init__()
        self.ax = []
        self.ay = []
        self.kax = 0
        self.kay = 0

class Force(object):
    def __init__(self,mass):
        super(Force, self).__init__()
        self.mass = mass # For force calculations.
        self.fx = []
        self.fy = []
        self.kfx = 0
        self.kfy = 0

class Ball(sdl2.ext.Entity):
    def __init__(self, world, sprite, posx=0, posy=0, mass=10):
        self.sprite = sprite
        self.sprite.position = posx, posy
        self.velocity = Velocity()
        self.acceleration = Acceleration()
        self.force = Force(mass)
        self.position = Position()


def run():
    sdl2.ext.init()
    window = sdl2.ext.Window("The Pong Game", WINDOW_SIZE)
    window.show()

    if "-hardware" in sys.argv:
        print("Using hardware acceleration")
        renderer = sdl2.ext.Renderer(window)
        factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)
    else:
        print("Using software rendering")
        factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)

    sp_ball = factory.from_color(WHITE, size=(20, 20))

    world = sdl2.ext.World()

    movement = MovementSystem(0, 0, WIDTH, HEIGHT)

    if factory.sprite_type == sdl2.ext.SOFTWARE:
        spriterenderer = SoftwareRenderSystem(window)
    else:
        spriterenderer = TextureRenderSystem(renderer)

    world.add_system(movement)
    world.add_system(spriterenderer)

    ball = Ball(world, sp_ball, 390, 290)
    ball.position.px = WIDTH/2
    ball.position.py = HEIGHT/2
    ball.velocity.vy = INITIAL_VELOCITY
    ball.acceleration.ay = ball.acceleration.ay + [INITIAL_GRAVITY]

    running = True
    while running:
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_UP:
                    ball.force.kfy = USER_FORCE
            elif event.type == sdl2.SDL_KEYUP:
                if event.key.keysym.sym == sdl2.SDLK_UP:
                    ball.force.kfy = 0
        sdl2.SDL_Delay(10)
        world.process()


if __name__ == "__main__":
    sys.exit(run())
