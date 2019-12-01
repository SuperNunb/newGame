import pygame as pg
import random
import time
import levels
from settings import *
from sprites import *
from other import *
from os import path

class Game:
    def __init__(self):
        pg.init()
        pg.mixer.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT), depth=BIT_DEPTH)
        pg.display.set_caption(TITLE)
        #pg.display.set_icon()
        self.clock = pg.time.Clock()
        self.levelNum = 1
        self.load_data()
        self.running = True
        self.font1 = pg.font.match_font("system")
        self.hudVisible = False
        self.currentStageType = 0
        self.wantToQuit = False
        self.fog = pg.Surface((WIDTH, HEIGHT))
        self.fog.fill(FOG_COLOR)
        self.transitioning = False
        self.grappleLine = False
        setupControllers(self)
        self.freezeUpdate = None
        self.gmovr = False

    def load_data(self):
        self.main_folder = path.dirname(__file__)
        self.img_folder = path.join(self.main_folder, 'img')
        self.level_folder = path.join(self.main_folder, 'levels')
        self.audio_folder = path.join(self.main_folder, 'audio')
        self.mapList = [levels.level1, levels.level2, levels.level3, levels.level4, levels.level5, 
                        levels.level6, levels.level7, levels.level8, levels.level9, levels.level10]
        self.map = Map(self, self.mapList[self.levelNum - 1])
        self.defineImgs()
        pg.mixer.music.set_volume(0.25)

    def new(self):
        if self.wantToQuit:
            self.running = False
            self.playing = False
        else:
            self.setupGroups()
            self.setupMap()
            self.camera = Camera(self, self.map.pixelWidth, self.map.pixelHeight)
            for sprite in self.all_sprites:
                sprite.image.set_colorkey(YELLOW)
                sprite.image = sprite.image.convert(BIT_DEPTH)

    def run(self):
        self.playing = True
        self.hudVisible = True
        while self.playing:
            if self.wantToQuit:
                self.running = False
                self.playing = False
            else:
                self.dt = self.clock.tick(FPS) / 1000
                self.events()
                self.update()
                if self.gmovr: return
                #if self.transitioning: 
                 #   self.draw(noUpdate=True)
                  #  self.transitioning = False
            #    else: self.draw()
                self.draw()

    def events(self):
        def powerUpEvents():
            if "grapple" in self.avatar.inventory and len(self.grapplehook) == 0 and self.avatar.grappleCollCheck(): 
                Grapplehook(self, vec(self.avatar.pos.x + 10, self.avatar.pos.y))
            elif "stealth" in self.avatar.inventory:
                self.avatar.stealth = True
                self.avatar.last_stealth = pg.time.get_ticks() + POWERUP_TIMEOUT
        #UNHOLDABLE EVENTS
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.playing = False
                self.running = False    
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:   #AVATAR JUMPING
                    self.avatar.jump()
                if event.key == pg.K_UP or event.key == pg.K_w:
                    if self.avatar.nearElevator and not self.avatar.tryElevator: 
                        self.avatar.tryElevator = True
                if event.key == pg.K_DOWN or event.key == pg.K_s:
                    self.avatar.crouching = True
                if (event.key == pg.K_z or event.key == pg.K_e) and (self.avatar.jumping == False or self.avatar.para):                           #AVATAR SHOOTING
                    self.avatar.fireBullet()
                if event.key == pg.K_x or event.key == pg.K_f:
                    powerUpEvents()
                if event.key == pg.K_r:
                    self.restart()
                if event.key == pg.K_p or event.key == pg.K_ESCAPE:
                    self.pause()
            if event.type == pg.KEYUP:
                if event.key == pg.K_SPACE:
                    self.avatar.jumpCut()
                if event.key == pg.K_DOWN or event.key == pg.K_s:
                    self.avatar.crouching = False
            if event.type == pg.JOYBUTTONUP:
                if event.button == 0:
                    self.avatar.jumpCut()
                if event.button == 1:
                    self.avatar.crouching = False
            if event.type == pg.JOYBUTTONDOWN:
                if event.button == 0:
                    self.avatar.jump()
                if event.button == 2 and (self.avatar.jumping == False or self.avatar.para):
                    self.avatar.fireBullet()
                if event.button == 1:
                    self.avatar.crouching = True
                if event.button == 3:
                    if self.avatar.nearElevator: self.avatar.tryElevator = True
                    else: powerUpEvents()
 
        #HOLDABLE EVENTS
        self.avatar.acc.x = 0
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:            #AVATAR RUNNING
                self.avatar.acc.x = -AVATAR_ACC
                self.avatar.orientation = -1
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
                self.avatar.acc.x = AVATAR_ACC
                self.avatar.orientation = 1
        if pg.joystick.get_count() > 0:
            axes = self.joysticks[0].get_numaxes()
            for i in range(axes):
                axis = self.joysticks[0].get_axis(i)
                if axis > 0.5: 
                    self.avatar.acc.x = AVATAR_ACC
                    self.avatar.orientation = 1
                if axis < -0.5: 
                    self.avatar.acc.x = -AVATAR_ACC
                    self.avatar.orientation = -1

    def update(self):
        self.all_sprites.update()
        self.camera.update(self.avatar)
        if self.gmovr: return
        self.all_collisions()

    def draw(self, noUpdate=False):
        #self.screen.fill(LIGHTGREY)
        self.screen.blit(self.background, self.camera.apply(pg.Rect(0, 0, self.map.pixelWidth, self.map.pixelHeight), isRect=True))
        for sprite in self.floors:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.walls:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.powerUps:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.sensors:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.powerUps:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.depthStatics:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.decor:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.kinetics:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        self.drawTempLines()
        #self.drawVFX()
        #self.drawGrid()
        self.hud()
        if not noUpdate: 
            pg.display.flip()

    def drawGrid(self):
        for x in range(0, self.map.pixelWidth, TILESIZE):
            pg.draw.line(self.background, WHITE, (x, 0), (x, self.map.pixelHeight))
        for y in range(0, self.map.pixelHeight, TILESIZE):
            pg.draw.line(self.background, WHITE, (0, y), (self.map.pixelWidth, y))

    def drawVFX(self):
        tempSurf = pg.Surface((WIDTH, HEIGHT))
        for x in range(0, WIDTH, int(TILESIZE / 16)):
            pg.draw.line(self.screen, NAVY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, int(TILESIZE / 16)):
            pg.draw.line(self.screen, NAVY, (0, y), (WIDTH, y))
        tempSurf.set_alpha(32)
        self.screen.blit(tempSurf, (0,0))

    def connectBgSlices(self):
        bgSlice = pg.image.load(path.join(self.img_folder, 'backgroundSlice.png'))
        sliceNum = self.map.tileHeight / 6
        self.background = pg.Surface((bgSlice.get_width(), bgSlice.get_height() * sliceNum))
        i = 0
        while i <= sliceNum:
            self.background.blit(bgSlice, (0, i * bgSlice.get_height()))
            i += 1
        self.background = pg.transform.scale(self.background, (self.map.pixelWidth, self.map.pixelHeight))

    def defineImgs(self):
        self.connectBgSlices()
        self.background = self.background.convert(BIT_DEPTH)
        self.statics_sheet = Spritesheet(self, "statics.png")
        self.avatar_sheet = Spritesheet(self, "avatars.png")
        self.baddie_sheet = Spritesheet(self, "baddies.png")
        self.other_sheet = Spritesheet(self, "other.png")

        self.wall0Img = self.statics_sheet.getImage(0,0,12,12)
        self.wall1Img = self.statics_sheet.getImage(12,0,12,12)
        self.wall2Img= self.statics_sheet.getImage(24,0,12,12)
        
        self.floor0Img = self.statics_sheet.getImage(0,12,12,12)
        self.floor1Img = self.statics_sheet.getImage(12,12,12,12)
        
        self.doorFirstImg = self.statics_sheet.getImage(0,24,12,36,48,144)
        self.doorFinalImg = self.statics_sheet.getImage(24,24,12,36,48,144)
        
        self.windowImg = self.statics_sheet.getImage(36,24,12,36,48,144)
        self.windowGoneImg = self.statics_sheet.getImage(60,24,12,36,48,144)
        self.windowCrackedImg = self.statics_sheet.getImage(48,24,12,36,48,144)
        
        self.avatarIdle0Img = self.avatar_sheet.getImage(0,33,12,30,36,90)
        self.avatarIdle1Img = self.avatar_sheet.getImage(0,66,12,30,36,90)
        self.avatarRightJump0Img = self.avatar_sheet.getImage(14,33,16,27,48,81)
        self.avatarRightJump1Img = self.avatar_sheet.getImage(30,33,17,25,51,75)
        self.avatarRightJump2Img = self.avatar_sheet.getImage(47,33,17,25,51,75)
        self.avatarRightJump3Img = self.avatar_sheet.getImage(64,33,16,23,48,69)
        self.avatarRightRun0Img = self.avatar_sheet.getImage(14,66,16,30,48,90)
        self.avatarRightRun1Img = self.avatar_sheet.getImage(30,66,16,30,48,90)
        self.avatarRightRun2Img = self.avatar_sheet.getImage(46,66,16,30,48,90)
        self.avatarRightRun3Img = self.avatar_sheet.getImage(62,66,14,30,42,90)
        self.avatarRightCrouchImg = self.avatar_sheet.getImage(31,99,14,24,42,70)
        self.avatarRightShoot0Img = self.avatar_sheet.getImage(0,99,16,30,48,90)
        self.avatarRightGrappleImg = self.avatar_sheet.getImage(16,99,15,30,45,90)
        self.avatarLeftJump0Img = pg.transform.flip(self.avatarRightJump0Img, True, False)
        self.avatarLeftJump1Img = pg.transform.flip(self.avatarRightJump1Img, True, False)
        self.avatarLeftJump2Img = pg.transform.flip(self.avatarRightJump2Img, True, False)
        self.avatarLeftJump3Img = pg.transform.flip(self.avatarRightJump3Img, True, False)
        self.avatarLeftRun0Img = pg.transform.flip(self.avatarRightRun0Img, True, False)
        self.avatarLeftRun1Img = pg.transform.flip(self.avatarRightRun1Img, True, False)
        self.avatarLeftRun2Img = pg.transform.flip(self.avatarRightRun2Img, True, False)
        self.avatarLeftRun3Img = pg.transform.flip(self.avatarRightRun3Img, True, False)
        self.avatarLeftCrouchImg = pg.transform.flip(self.avatarRightCrouchImg, True, False)
        self.avatarLeftShoot0Img = pg.transform.flip(self.avatarRightShoot0Img, True, False)
        self.avatarLeftGrappleImg = pg.transform.flip(self.avatarRightGrappleImg, True, False)
        
        self.bigBaddLeft0Img = self.baddie_sheet.getImage(0,0,12,31,48,124)
        self.bigBaddRight0Img = pg.transform.flip(self.bigBaddLeft0Img, True, False)
        
        self.sniperBaddLeft0Img = self.baddie_sheet.getImage(0,0,12,31,48,124)
        self.sniperBaddRight0Img = pg.transform.flip(self.sniperBaddLeft0Img, True, False)
        
        self.groundBaddLeft0Img = self.baddie_sheet.getImage(12,0,24,11,96,44)
        self.groundBaddRight0Img = pg.transform.flip(self.groundBaddLeft0Img, True, False)
        
        self.grappleImg = self.other_sheet.getImage(18,0,16,8,64,32)
        self.grapplehookImg = pg.transform.rotate(self.other_sheet.getImage(18,0,7,7,28,28), 270)
        self.bulletImg = self.other_sheet.getImage(0,0,6,4,18,12)
        self.lifeImg = self.other_sheet.getImage(6,0,12,11,48,44)
        self.minigunImg = self.other_sheet.getImage(34,0,12,12)
        self.stealthImg = self.other_sheet.getImage(46,0,9,10,36,40)
        
        self.tableImg = self.statics_sheet.getImage(0,60,22,12,88,48)
        self.desktopImg = self.statics_sheet.getImage(22,60,22,19,88,76)
        self.stoolUpImg = self.statics_sheet.getImage(44,60,8,10,32,40)
        self.stoolDownImg = self.statics_sheet.getImage(52,60,8,10,40,32)
        self.fireExtinguisherImg = self.statics_sheet.getImage(44,70,9,17,28,68)

        self.depthWallImg = self.statics_sheet.getImage(48,12,12,12)
        self.depthFloorImg = self.statics_sheet.getImage(36,12,12,12)
        self.depthFloorCornerImg = self.statics_sheet.getImage(36,0,12,12)
        self.depthFloorCliffImg = self.statics_sheet.getImage(48,0,12,12)
        self.depthFloorSideImg = self.statics_sheet.getImage(60,0,12,12)
        self.depthFloorCoverImg = self.statics_sheet.getImage(60,12,12,12)
        self.depthFloorCoverEdgeImg = self.statics_sheet.getImage(72,0,12,12)
        self.depthFloorCoverCornerImg = self.statics_sheet.getImage(72,12,12,12)
        self.depthDoorImg = self.statics_sheet.getImage(12,24,12,36,48,144)
        self.depthWindowImg = self.statics_sheet.getImage(48,24,5,36,20,144)
        self.depthWindowTopImg = self.statics_sheet.getImage(53,24,5,12,20,48)

    def setupGroups(self):
        self.all_sprites = pg.sprite.Group()
        self.statics = pg.sprite.Group()
        self.kinetics = pg.sprite.Group()
        self.obstacles = pg.sprite.Group()
        self.sensors = pg.sprite.Group()
        self.characters = pg.sprite.Group()
        self.projectiles = pg.sprite.Group()
        self.floors = pg.sprite.Group()
        self.doors = pg.sprite.Group()
        self.bullets = pg.sprite.Group()
        self.grapplehook = pg.sprite.GroupSingle()
        self.baddies = pg.sprite.Group()
        self.bigBadds = pg.sprite.Group()
        self.sniperBadds = pg.sprite.Group()
        self.groundBadds = pg.sprite.Group()
        self.windows = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.depthStatics = pg.sprite.Group()
        self.elevators = pg.sprite.Group()
        self.powerUps = pg.sprite.Group()
        self.decor = pg.sprite.Group()

    def setupMap(self):
        for row in range(len(self.map.data)):
            for col in range(len(self.map.data[row])):   
                tile = self.map.data[row][col]

                def checkCollidable(elitRow, elitCol, value=0):
                    if self.map.data[elitRow][elitCol] == 1 or self.map.data[elitRow][elitCol] == 2:
                        return True
                    else: return False

                if tile == 2:   
                    Floor(self, col, row)
                    if checkCollidable(row - 1, col + 1) == False and checkCollidable(row - 1, col) == False and checkCollidable(row, col + 1) == False:
                        DepthStatic(self, col + 1, row - 1, self.depthFloorCliffImg)
                    if checkCollidable(row, col + 1) == False and checkCollidable(row + 1, col + 1) == False and checkCollidable(row + 1, col) == False: 
                        DepthStatic(self, col + 1, row, self.depthFloorSideImg)
                    if len(self.map.data[row]) > col + 1 and len(self.map.data) > row + 1:
                        if checkCollidable(row + 1, col) == True and checkCollidable(row, col + 1) == False and checkCollidable(row + 1, col + 1) == False:
                            DepthStatic(self, col + 1, row, self.depthWallImg)
                    if checkCollidable(row - 1, col) == False and self.map.data[row - 3][col - 1] != 5:
                        DepthStatic(self, col, row - 1, self.depthFloorImg)
                    if checkCollidable(row, col - 1) == False: 
                        DepthStatic(self, col - 1, row, self.depthFloorCoverImg)
                        if checkCollidable(row - 1, col - 1) == False:
                            DepthStatic(self, col - 1, row - 1, self.depthFloorCoverEdgeImg)
                    if checkCollidable(row - 1, col) == False and checkCollidable(row - 1, col + 1) == True and checkCollidable(row, col + 1) == True and self.map.data[row - 1][col + 1] == 2:
                        DepthStatic(self, col, row - 1, self.depthFloorCoverCornerImg)
                    if checkCollidable(row - 1, col) == False and checkCollidable(row,col) == True and checkCollidable(row - 1, col - 1) == True:
                        DepthStatic(self, col, row - 1, self.depthFloorCornerImg)
                if tile == 1:
                    Wall(self, col, row)
                    if len(self.map.data[row]) > col + 1 and len(self.map.data) > row + 1:
                        if checkCollidable(row, col + 1) == False and self.map.data[row + 1][col] != 4:
                            DepthStatic(self, col + 1, row, self.depthWallImg)
                if tile == 3:
                    self.avatar = Avatar(self, col, row)
                if tile == 4:
                    Window(self, col, row)
                    DepthStatic(self, col + 1, row + 2, self.depthFloorCliffImg)
                    DepthStatic(self, col + 1, row - 1, self.depthFloorSideImg)
                if tile == 5:
                    Door(self, col, row, col)
                    if len(self.map.data[row]) > col + 1:
                        DepthStatic(self, col + 1, row, self.depthDoorImg)
                if tile == 6:
                    Elevator(self, col,row, 0)
                if tile == 7:
                    Elevator(self, col,row, 1)
                if tile >= 8 and tile <= 11:
                    PowerUp(self, col,row, tile)
                if tile == 12:
                    BigBadd(self, col,row, -1)
                if tile == 13: 
                    SniperBadd(self, col,row, 1)
                if tile == 14: 
                    SniperBadd(self, col,row, -1)
                if tile == 15: 
                    GroundBadd(self, col,row, -1)
                if tile == 16: 
                    GroundBadd(self, col,row, 1)
                if 30 <= tile <= 33:
                    CollDecor(self, col,row, tile)
                if 34 <= tile <= 37:
                    GhostDecor(self, col,row, tile)
 
    def all_collisions(self):
        avatDoorHits = pg.sprite.spritecollide(self.avatar, self.doors, False)                      #AVATAR-DOORS
        if avatDoorHits:
            if self.avatar.vel.x > 0:
                self.levelUp()
            else:
                self.avatar.vel.x = 0
                self.avatar.acc.x = 0
                self.avatar.pos.x = avatDoorHits[0].rect.x + TILESIZE
        avatWindowHits = pg.sprite.spritecollide(self.avatar, self.windows, False)                  #AVATAR-WINDOWS
        if avatWindowHits:
            if not avatWindowHits[0].broken:
                self.avatar.lives -= 1
            if self.avatar.vel.x > 0:
                self.changeStageType(avatWindowHits[0])
            avatWindowHits[0].broken = False
            avatWindowHits[0].breaking = True
        pg.sprite.groupcollide(self.bullets, self.obstacles, True, False)                           #BULLETS-OBSTACLES
        pg.sprite.groupcollide(self.bullets, self.doors, True, False)                               #BULLETS-DOORS
        avatBaddieHits = pg.sprite.spritecollide(self.avatar, self.baddies, False)                  #AVATAR-BADDIES
        if avatBaddieHits:
            if avatBaddieHits[0] in self.groundBadds: return
            self.avatar.injury(1)
            self.avatar.pos.x -= 5 * avatBaddieHits[0].orientation
            #if avatBaddieHits[0] in self.bigBadds: self.avatar.injury(2)
            #if avatBaddieHits[0] in self.sniperBadds: self.avatar.injury(1)
        for baddie in self.baddies:                                                                 #BADDIES-BULLETS
            for bullet in self.bullets:
                if pg.sprite.collide_rect(bullet, baddie):
                    if bullet.source == "avatar" and self.freezeUpdate != baddie.source:
                        baddie.lives -= 1
                        baddie.damageEffects()
                        bullet.kill()
        avatBulletHits = pg.sprite.spritecollide(self.avatar, self.bullets, False)                  #AVATAR-BULLETS
        if avatBulletHits: 
            if self.currentStageType == 1 and self.avatar.para and avatBulletHits[0].source != "avatar": 
                self.avatar.paraTorn = True
                self.avatar.para = False
            elif avatBulletHits[0].source != "avatar":
                self.avatar.injury(1)
        for bullet in self.bullets:                                                                 #BULLETS-WINDOWS
            for window in self.windows:
                if pg.sprite.collide_rect(bullet, window) and not window.broken:
                    window.broken = True
                    window.breaking = True
        """for baddie1 in self.baddies:                                                             #BADDIE-BADDIE
            for baddie2 in self.baddies:
                if id(baddie1) != id(baddie2) and pg.sprite.collide_rect(baddie1, baddie2):
                    if baddie1.vel.x == baddie2.vel.x:
                         if baddie1.rect.x == baddie2.rect.x:
                              baddie2.kill()"""
        avatElevatorHits = pg.sprite.spritecollide(self.avatar, self.elevators, False)              #AVATAR-ELEVATORS
        if avatElevatorHits:
            elevator = avatElevatorHits[0].rect.centerx
            if self.avatar.rect.right > elevator and self.avatar.rect.left < elevator:
                if self.avatar.vel.y == 0:
                    self.avatar.nearElevator = True
            if self.avatar.tryElevator and self.avatar.rect.bottom == avatElevatorHits[0].rect.bottom and self.freezeUpdate != "avatar":
                self.freezeUpdate = "avatar"
                if avatElevatorHits[0].door == 0:
                    self.avatar.pos.y -= ELEVATOR_DISTANCE
                    self.avatar.rect.y -= ELEVATOR_DISTANCE
                if avatElevatorHits[0].door == 1:
                    self.avatar.pos.y += ELEVATOR_DISTANCE
                    self.avatar.rect.y += ELEVATOR_DISTANCE
                self.avatar.pos.x = avatElevatorHits[0].rect.x
                self.avatar.rect.x = avatElevatorHits[0].rect.x
                self.avatar.vel.y = 0
                self.avatar.vel.x = 0
                self.avatar.acc.x = 0
                self.avatar.tryElevator = False
                self.avatar.image.set_alpha(0)
                if avatElevatorHits[0].door == 0: goal = self.avatar.pos.y - ELEVATOR_DISTANCE
                #if avatElevatorHits[0].door == 1: goal = self.avatar.pos.y + ELEVATOR_DISTANCE
                else: goal = self.avatar.pos.y
                while self.avatar.rect.y > goal:
                    if avatElevatorHits[0].door == 0 and goal != self.avatar.pos.y: 
                        self.avatar.rect.y -= 9
                    #if avatElevatorHits[0].door == 1: self.avatar.rect.y += 9
                    self.camera.update(self.avatar)
                    self.events()
                    self.update()
                    self.draw()
                self.freezeUpdate = None
                self.avatar.pos.y = self.avatar.rect.y
        avatPowerUpHits = pg.sprite.spritecollide(self.avatar, self.powerUps, True)                 #AVATAR-POWERUPS
        if avatPowerUpHits:
            if avatPowerUpHits[0].type == "life": self.avatar.lives += 1
            elif not avatPowerUpHits[0].type in self.avatar.inventory:
                self.avatar.inventory.append(avatPowerUpHits[0].type)
                if avatPowerUpHits[0].type == "minigun":
                    self.avatar.lastMinigunInit = pg.time.get_ticks()                    
        if "grapple" in self.avatar.inventory:                                                      #GRAPPLEHOOK-FLOORS
            for grapplehook in self.grapplehook: 
                    grapplehookFloorHits = pg.sprite.spritecollide(grapplehook, self.floors, False)
                    if grapplehookFloorHits and self.freezeUpdate != "avatar": 
                        grapplehook.vel.y = 0
                        self.freezeUpdate = "avatar"
                        initAvatPos = vec(self.avatar.rect.x,self.avatar.rect.y)
                        grapplehook.pos.y = grapplehookFloorHits[0].rect.bottom
                        if self.avatar.orientation == 1: self.avatar.image = self.avatarRightGrappleImg
                        else: self.avatar.image = self.avatarLeftGrappleImg
                        self.avatar.image.set_colorkey(YELLOW)
                        while self.avatar.rect.top > grapplehook.rect.bottom:
                            if pg.sprite.spritecollide(self.avatar, self.obstacles, False): break
                            self.avatar.rect.y -= GRAPPLEHOOK_SPEED / 5
                            self.camera.update(self.avatar)
                            self.events()
                            self.update()
                            self.draw()
                        self.freezeUpdate = None
                        self.avatar.pos.y = self.avatar.rect.y
                        self.grappleLine = False
                        grapplehook.kill()

    def restart(self):
        self.currentStageType = 0
        self.all_sprites.empty()
        self.new()
        self.run()

    def resetLevel(self):
        self.levelNum = 1
        self.map = Map(self, self.mapList[self.levelNum - 1])

    def resetLoops(self):
        self.playing = False
        self.paused = False
        self.moribund = False
        self.options = False
        self.credits = False
        self.transitioning = True

    def hud(self):
        if self.hudVisible:
            i = 1
            while i <= self.avatar.lives:
                self.lifeImg.set_colorkey(YELLOW)
                self.screen.blit(self.lifeImg, pg.Rect(WIDTH / 16 + i * TILESIZE * 1.125, TILESIZE / 3, TILESIZE, TILESIZE))
                i += 1
            #drawText(self, "SCORE: " + str(), 42, WHITE, WIDTH / 4 * 3, TILESIZE / 2, self.font1)
            drawText(self, "LEVEL " + str(self.levelNum), 42, WHITE, WIDTH / 2, TILESIZE / 2, self.font1)

    def levelUp(self):
        self.levelNum += 1
        self.map = Map(self, self.mapList[self.levelNum - 1])
        #fadeOut(self, WIDTH, HEIGHT, BLACK)
        self.restart()
        self.draw(noUpdate=True)
        #fadeIn(self, WIDTH, HEIGHT, BLACK)
        self.transitioning = True

    def changeStageType(self, glass):
        self.currentStageType = 1
        if not self.avatar.para:
            self.avatar.pos.x = glass.rect.right

    def start_screen(self):
        def drawTitles():
            drawText(self, "NEW GAME", 72, GREY, WIDTH / 2, HEIGHT / 3, self.font1)
            drawText(self, "PRESS SPACE TO START", 52, GREY, WIDTH / 2, HEIGHT / 3 * 2, self.font1)
        self.screen.fill(BLACK)
        self.gmovr = False
        self.new()
        pg.mixer.music.load(path.join(self.audio_folder, "menu.wav"))
        pg.mixer.music.play(loops=-1)
        drawMenuBox(self, WIDTH / 6, HEIGHT / 6, WIDTH / 1.5, HEIGHT / 1.5, NAVY, GREY)
        drawTitles()
        pg.display.flip()
        time.sleep(1)
        self.intro = True
        pressed = False
        while self.intro:
            drawTitles()
            pg.display.flip()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.intro = False
                    self.wantToQuit = True
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    pressed = True
                if event.type == pg.KEYUP and pressed == True and event.key == pg.K_SPACE:
                    self.intro = False
                if event.type == pg.JOYBUTTONUP:
                    if event.button == 0: 
                        self.intro = False

    def game_over(self):
        self.resetLevel()
        self.draw()
        #animateSprite()             #DEATH ANIMATION
        time.sleep(1)
        self.moribund = True
        pressed = False
        self.gmovr = True
        while self.moribund:
            drawMenuBox(self, WIDTH / 3.25, HEIGHT / 3, WIDTH / 2.5, HEIGHT / 4, NAVY, GREY)
            drawText(self, "GAME OVER", 72, WHITE, WIDTH / 2, HEIGHT / 2.5, self.font1)
            pg.display.flip()
            for event in pg.event.get():
                if event.type == pg.QUIT: 
                    self.wantToQuit = True
                    self.resetLoops()
                if event.type == pg.KEYDOWN: 
                    self.resetLoops()
    #def game_over(self):
     #   self.resetLevel()
      #  self.resetLoops()

    def pause(self):
        self.paused = True
        spots = ["RESUME","OPTIONS","EXIT"]
        spot = "RESUME"
        i = 0
        pg.mixer.music.load(path.join(self.audio_folder, "menu.wav"))
        pg.mixer.music.play(loops=-1)
        while self.paused:
            drawMenuBox(self, WIDTH / 3, HEIGHT / 6, WIDTH / 3, HEIGHT / 1.5, NAVY, GREY, 10)
            drawText(self, "RESUME", 64, GREY, WIDTH / 2, HEIGHT / 9 * 2, self.font1)
            drawText(self, "OPTIONS", 64, GREY, WIDTH / 2, HEIGHT / 9 * 4, self.font1)
            drawText(self, "EXIT", 64, GREY, WIDTH / 2, HEIGHT / 3 * 2, self.font1)
            spot, i = scrollMenu(spots, i)
            if spot == "RESUME":
                drawText(self, "RESUME", 64, WHITE, WIDTH / 2, HEIGHT / 9 * 2, self.font1)
            if spot == "OPTIONS":
                drawText(self, "OPTIONS", 64, WHITE, WIDTH / 2, HEIGHT / 9 * 4, self.font1)
            if spot == "EXIT":
                drawText(self, "EXIT", 64, WHITE, WIDTH / 2, HEIGHT / 3 * 2, self.font1)
            pg.display.update()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.paused = False
                    self.wantToQuit = True
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE or event.key == pg.K_p:
                        self.paused = False
                    if event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                        if spot == "RESUME":
                            self.paused = False
                        if spot == "OPTIONS":
                            self.optionsMenu()
                        if spot == "EXIT":
                            self.resetLevel()
                            self.resetLoops()
        pg.mixer.music.load(path.join(self.audio_folder, "levels.wav"))
        pg.mixer.music.play()
    
    def optionsMenu(self):
        self.options = True
        spots = ["MUSIC","ENTER CODE", "CREDITS"]
        spot = "MUSIC"
        i = 0
        while self.options:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.options = False
                    self.paused = False
                    self.wantToQuit = True
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        self.options = False
                    if event.key == pg.K_p:
                        self.options = False
                        self.paused = False
                    if event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                        if spot == "MUSIC": 
                            if pg.mixer.music.get_volume() == 0:
                                pg.mixer.music.set_volume(0.25)
                            else: 
                                pg.mixer.music.set_volume(0)
                        if spot == "ENTER CODE": pass
                        if spot == "CREDITS": self.creditsMenu()

            drawMenuBox(self, WIDTH / 3, HEIGHT / 6, WIDTH / 3, HEIGHT / 1.5, NAVY, GREY, 10)
            drawText(self, "MUSIC", 64, GREY, WIDTH / 2, HEIGHT / 9 * 2, self.font1)
            drawText(self, "ENTER CODE", 64, GREY, WIDTH / 2, HEIGHT / 9 * 4, self.font1)
            drawText(self, "CREDITS", 64, GREY, WIDTH / 2, HEIGHT / 3 * 2, self.font1)
            spot, i = scrollMenu(spots, i)
            if spot == "MUSIC":
                drawText(self, "MUSIC", 64, WHITE, WIDTH / 2, HEIGHT / 9 * 2, self.font1)
            if spot == "ENTER CODE":
                drawText(self, "ENTER CODE", 64, WHITE, WIDTH / 2, HEIGHT / 9 * 4, self.font1)
            if spot == "CREDITS":
                drawText(self, "CREDITS", 64, WHITE, WIDTH / 2, HEIGHT / 3 * 2, self.font1)
            pg.display.update()
    
    def creditsMenu(self):
        self.credits = True
        pressed = False
        while self.credits:
            drawMenuBox(self, WIDTH / 4, HEIGHT / 6, WIDTH / 2, HEIGHT / 1.5, NAVY, GREY, 10)
            drawText(self, "PROGRAMMER: ", 28, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 3, self.font1)
            drawText(self, "ARTISTS:", 28, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 4, self.font1)
            drawText(self, "LEVEL DESIGNER: ", 28, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 7, self.font1)
            drawText(self, "COMPOSER: ", 28, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 8, self.font1)
         #   drawText(self, "SOUND DESIGNER: ", 28, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 8, self.font1)
            drawText(self, "CALEB BAYLES", 24, WHITE, WIDTH / 8 * 5, HEIGHT / 11 * 3, self.font1)
            drawText(self, "SAM WITT", 24, WHITE, WIDTH / 8 * 5, HEIGHT / 11 * 4, self.font1)
            drawText(self, "JOEY JONES", 24, WHITE, WIDTH / 8 * 5, HEIGHT / 11 * 5, self.font1)
           # drawText(self, "ZACH BALVANZ", 24, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 5, self.font1)
            drawText(self, "JORDAN MIZE", 24, WHITE, WIDTH / 8 * 5, HEIGHT / 11 * 6, self.font1)
            drawText(self, "ERIC TRICKEY", 24, WHITE, WIDTH / 8 * 5, HEIGHT / 11 * 7, self.font1)
            drawText(self, "EVAN BOSAW", 24, WHITE, WIDTH / 8 * 5, HEIGHT / 11 * 8, self.font1)
        #    drawText(self, "RYAN CHANCE", 24, WHITE, WIDTH / 8 * 5, HEIGHT / 11 * 8, self.font1)
            pg.display.flip()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.wantToQuit = True
                    self.credits = False
                    self.paused = False
                    self.options = False
                if event.type == pg.KEYDOWN:
                    pressed = True
                if event.type == pg.KEYUP and pressed:
                    self.draw()
                    self.credits = False

    def drawTempLines(self):
        if self.grappleLine:
            for grapplehook in self.grapplehook:
                pg.draw.line(self.screen, BLACK, self.camera.apply(self.avatar).midtop, self.camera.apply(grapplehook).center, 4)

g = Game()
while g.running:
    g.start_screen()
    g.new()
    pg.mixer.music.load(path.join(g.audio_folder, "levels.wav"))
    pg.mixer.music.play(loops=-1)
    g.run()