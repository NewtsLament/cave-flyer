#!/usr/bin/python
"""Simple acceleration demo."""
import sys
import time
import sdl2
import sdl2.ext

BLACK = sdl2.ext.Color(0, 0, 0)
WHITE = sdl2.ext.Color(255, 255, 255)
INITIAL_VELOCITY = 0
INITIAL_GRAVITY = 0.7


class MovementSystem(sdl2.ext.Applicator):
    def __init__(self, minx, miny, maxx, maxy):
        super(MovementSystem, self).__init__()
        self.componenttypes = Position, Acceleration, Velocity, sdl2.ext.Sprite
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.__oldtime = None
        self.__newtime = time.perf_counter()
        self.__gravity = INITIAL_GRAVITY

    def __deltaTime(self):
        '''Updates this instances time variable,
        and calculates the difference.'''
        self.__oldtime = self.__newtime
        self.__newtime = time.perf_counter()
        return self.__newtime - self.__oldtime

    def process(self, world, componentsets):
        for position, acceleration, velocity, sprite in componentsets:
            delta = self.__deltaTime()
            x = position.px
            y = position.py
            vx = velocity.vx
            vy = velocity.vy
            ax = acceleration.ax
            ay = acceleration.ay
            lx1 = self.minx
            ly1 = self.miny
            lx2 = self.maxx
            ly2 = self.maxy

            swidth, sheight = sprite.size
            
            lax = ax
            lay = ay
            velocity.vx = vx+lax*delta
            velocity.vy = vy+lay*delta
            position.px = x+vx*delta
            position.py = y+vy*delta
            
            
            position.px = max(self.minx, position.px)
            position.py = max(self.miny, position.py)

            pmaxx = position.px + swidth
            pmaxy = position.py + sheight
            if pmaxx > self.maxx:
                position.px = self.maxx - swidth
            if pmaxy > self.maxy:
                position.py = self.maxy - sheight

            sprite.x = int(round(position.px))
            sprite.y = int(round(position.py))


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

class Velocity(object):
    def __init__(self):
        super(Velocity, self).__init__()
        self.vx = 0.0
        self.vy = 0.0

class Acceleration(object):
    def __init__(self):
        super(Acceleration, self).__init__()
        self.ax = 0.0
        self.ay = 0.0

class Ball(sdl2.ext.Entity):
    def __init__(self, world, sprite, posx=0, posy=0):
        self.sprite = sprite
        self.sprite.position = posx, posy
        self.velocity = Velocity()
        self.acceleration = Acceleration()
        self.position = Position()


def run():
    sdl2.ext.init()
    window = sdl2.ext.Window("The Pong Game", size=(800, 600))
    window.show()

    if "-hardware" in sys.argv:
        print("Using hardware acceleration")
        renderer = sdl2.ext.Renderer(window)
        factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)
    else:
        print("Using software rendering")
        factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)

    # Create the paddles - we want white ones. To keep it easy enough for us,
    # we create a set of surfaces that can be used for Texture- and
    # Software-based sprites.
    sp_ball = factory.from_color(WHITE, size=(20, 20))

    world = sdl2.ext.World()

    movement = MovementSystem(0, 0, 800, 600)

    if factory.sprite_type == sdl2.ext.SOFTWARE:
        spriterenderer = SoftwareRenderSystem(window)
    else:
        spriterenderer = TextureRenderSystem(renderer)

    world.add_system(movement)
    world.add_system(spriterenderer)

    ball = Ball(world, sp_ball, 390, 290)
    ball.position.px = 390
    ball.position.py = 290
    ball.velocity.vy = INITIAL_VELOCITY
    ball.acceleration.ay = INITIAL_GRAVITY

    running = True
    while running:
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_UP:
                    player1.velocity.vy = -PADDLE_SPEED
                elif event.key.keysym.sym == sdl2.SDLK_DOWN:
                    player1.velocity.vy = PADDLE_SPEED
            elif event.type == sdl2.SDL_KEYUP:
                if event.key.keysym.sym in (sdl2.SDLK_UP, sdl2.SDLK_DOWN):
                    player1.velocity.vy = 0
        sdl2.SDL_Delay(10)
        world.process()


if __name__ == "__main__":
    sys.exit(run())
