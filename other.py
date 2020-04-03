import pygame as pg
from settings import *
from os import path
import time

class Map:
    def __init__(self, game, lev):
        self.game = game
        self.data = lev
        self.tileWidth = len(self.data[0])      #MAP WIDTH IN TILES
        self.tileHeight = len(self.data)      #MAP HEIGHT IN TILES
        self.pixelWidth = self.tileWidth * TILESIZE      #MAP WIDTH IN PIXELS
        self.pixelHeight = self.tileHeight * TILESIZE      #MAP HEIGHT IN PIXELS

class Spritesheet:
    def __init__(self, game, filename):
        self.game = game
        self.spritesheet = pg.image.load(path.join(self.game.img_folder, filename)).convert()
    def getImage(self, x, y, w, h, diffWidth=TILESIZE, diffHeight=TILESIZE):
        prospectWidth = diffWidth
        prospectHeight = diffHeight
        image = pg.Surface((w,h))
        image.blit(self.spritesheet, (0,0), (x,y,w,h))
        image = pg.transform.scale(image, (prospectWidth, prospectHeight))
        return image

class Camera:
    def __init__(self, game, w,h):
        self.camera = pg.Rect((0,0,w,h))
        self.game = game
        self.width = w
        self.height = h

    def apply(self, entity, isRect=False):        #APPLIES CAMERA OFFSET TO SPRITE WHEN BLITTING TO SCREEN
        if not isRect: return entity.rect.move(self.camera.topleft)
        if isRect: return entity.move(self.camera.topleft)

    def update(self, target, updateX=True, updateY=True):       #MOVES CAMERA TO TARGET SPRITE
        if updateX:
            x = -target.rect.x + int(WIDTH / 2)
            x = min(0, x)
            x = max(-(self.width - WIDTH), x)
            self.camera.x = x
        if updateY:
            y = -target.rect.y + int(WIDTH / 3)
            y = min(0, y)
            y = max(-(self.height - HEIGHT), y)
            self.camera.y = y        

def drawText(self, msg, size, color, x, y, foonti=FONT_1, screen=None):
    font = pg.font.Font(foonti, size)
    text_surface = font.render(msg, False, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x,y)
    if screen == None: screen = self.screen
    screen.blit(text_surface, text_rect)
    return text_surface

def fadeIn(self, width, height, color):
    cover = pg.Surface((width, height))
    cover.fill(color)
    alpha = 255                      #threshold
    while alpha >= 16:
        cover.set_alpha(alpha)
        self.draw(noUpdate=True)
        self.screen.blit(cover, (0,0))
        pg.display.update()
        alpha = alpha ** (1/1.025)     #fadeSpeed

def fadeOut(self, width, height, color):
    cover = pg.Surface((width, height))
    cover.fill(color)
    alpha = 16                       #threshold
    while alpha <= 255:
        cover.set_alpha(alpha)
        self.draw(noUpdate=True)
        self.screen.blit(cover, (0,0))
        pg.display.update()
        alpha = alpha ** 1.025       #fadeSpeed

def fadeFull(self, width, height, color, sleepTime):
    fadeOut(self, width, height, color)
    time.sleep(1)
    fadeIn(self, width, height, color)

def scrollMenu(spots, index, speed=0.1):
    spot = spots[int(index)]
    keys = pg.key.get_pressed()
    if keys[pg.K_DOWN] or keys[pg.K_s]:
        index += speed
        if index >= len(spots): index = 0
        spot = spots[int(index)]
    elif keys[pg.K_UP] or keys[pg.K_w]:
        index -= speed
        if index < 0: index = len(spots) - 1
        spot = spots[int(index)]
    return index

def setupControllers(self):
    self.joysticks = []
    for i in range(0, pg.joystick.get_count()):
        self.joysticks.append(pg.joystick.Joystick(i))
        self.joysticks[-1].init()
        print("Detected joystick '" + self.joysticks[-1].get_name() + "'")

def drawMenuBox(self, x, y, width, height, boxColor, borderColor, borderSize=10):
    pg.draw.rect(self.screen, borderColor, (x - borderSize, y - borderSize, width + borderSize * 2, height + borderSize * 2))
    pg.draw.rect(self.screen, boxColor, (x, y, width, height))

def animateSprite(index, imageArray, delayTime=DEFAULT_ANIMATION_DELAY, suspend=False, joe=False):
    arrLen = len(imageArray)
    index += delayTime
    if joe: print(index)
    if index >= arrLen: 
        if suspend: index = arrLen - 1
        else: index = 0
    return imageArray[int(index)], index

def damageEffects(target, game, freezeUpdate, speed=0.5):
    tempImg1 = target.image.copy()
    tempImg2 = target.image.copy()
    tempImg3 = target.image.copy()
    tempImg1.set_alpha(64)
    tempImg2.set_alpha(122)
    tempImg3.set_alpha(32)
    if game.freezeUpdate != freezeUpdate and not game.moribund and not game.victorious:
        animationIndex = 0
        game.freezeUpdate = freezeUpdate
        while animationIndex < 3:
            if game.haste: break
            animationIndex += speed
            if 1 <= animationIndex < 2:
                target.image = tempImg1
            if 2 <= animationIndex < 3:
                target.image = tempImg2
            else: target.image = tempImg3
            target.image.set_colorkey(YELLOW)
            game.events()
            game.update()
            game.draw()
        game.freezeUpdate = None

def wait(time, function_one=None):
    now = pg.time.get_ticks()
    last_wait = pg.time.get_ticks()
    while now < time + last_wait: 
        if function_one == None: 
            for event in pg.event.get(): pass
        else: 
            function_one()
        now = pg.time.get_ticks()