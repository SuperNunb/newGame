import pygame as pg
import random, time, sys
import levels
from settings import *
from sprites import *
from other import *
from os import path

class Game:
    def __init__(self):
        pg.init()
        #pg.mixer.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT), depth=BIT_DEPTH)
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.levelNum = 1
        self.musicOn = 1
        self.textOn = 1
        self.load_data()
        self.running = True
        self.hudVisible = False
        self.currentStageType = 0
        self.wantToQuit = False
        self.fog = pg.Surface((WIDTH, HEIGHT))
        self.fog.fill(FOG_COLOR)
        self.transitioning = False
        self.grappleLine = False
        setupControllers(self)
        self.freezeUpdate = None
        self.grappleColor = BLACK
        self.treePowers = False
        self.bulletSpeed = BULLET_SPEED
        self.friction = FRICTION
        self.moribund = False
        self.victorious = False
        self.haste = False
        self.blinky = False
        self.restarting = False
        self.firstElevator = None
        self.secondElevator = None

    def load_data(self):
        if getattr(sys, 'frozen', False):
            self.main_folder = path.dirname(sys.executable)
            self.img_folder = self.main_folder
            self.audio_folder = self.main_folder
        else:
            self.main_folder = path.dirname(__file__)
            self.img_folder = path.join(self.main_folder, 'img')
            self.audio_folder = path.join(self.main_folder, 'audio')
        self.mapList = [levels.level1, levels.level2, levels.level3, levels.level4, levels.level5, 
                        levels.level6, levels.level7, levels.level8, levels.level9, levels.level10, levels.level11]
        self.map = Map(self, self.mapList[self.levelNum - 1])
        self.defineImgs()

        """self.effectsChannel = pg.mixer.Channel(0)
        self.windChannel = pg.mixer.Channel(1)
        self.effectsChannel.set_volume(0.5)
        self.windChannel.set_volume(0.75,1)
        self.grappleSound = pg.mixer.Sound(path.join(self.audio_folder, 'grapple.wav'))
        self.jumpSound = pg.mixer.Sound(path.join(self.audio_folder, 'jump.wav'))
        self.powerupSound = pg.mixer.Sound(path.join(self.audio_folder, 'powerup.wav'))
        self.gunSound = pg.mixer.Sound(path.join(self.audio_folder, 'gun.wav'))
        self.damageSound = pg.mixer.Sound(path.join(self.audio_folder, 'damage.wav'))
        self.parachuteSound = pg.mixer.Sound(path.join(self.audio_folder, 'parachute.wav'))
        self.glassSound = pg.mixer.Sound(path.join(self.audio_folder, 'glass.wav'))
        self.windSound = pg.mixer.Sound(path.join(self.audio_folder, 'wind.wav'))
        self.musicOn = self.readUserInfo(1)
        self.textOn = self.readUserInfo(2)
        if self.musicOn: pg.mixer.music.set_volume(0.15)
        else: pg.mixer.music.set_volume(0)"""

    def new(self):
        if self.wantToQuit:
            self.resetLoops()
        else:
            self.restarting = False
            self.setupGroups()
            self.setupMap()
            if self.blinky: self.avatar.wakka = True
            self.camera = Camera(self, self.map.pixelWidth, self.map.pixelHeight)
            self.connectBgSlices()
            self.background = self.background.convert(8)
            for sprite in self.all_sprites:
                if hasattr(sprite, 'colorkey'): 
                    #if sprite.colorkey == None: sprite.image.set_colorkey(YELLOW)
                    sprite.image.set_colorkey(sprite.colorkey)
                else: sprite.image.set_colorkey(YELLOW)
                sprite.image = sprite.image.convert(BIT_DEPTH)
            self.drawBackgroundText()
            if self.levelNum > 10:
                #pg.mixer.music.load(path.join(self.audio_folder, "boss.wav"))
                #pg.mixer.music.play(loops=-1)
            self.camera.update(self.avatar)

    def run(self):
        self.playing = True
        self.hudVisible = True
        while self.playing:
            if self.wantToQuit:
                self.resetLoops()
            else:
                self.dt = self.clock.tick(FPS) / 1000
                if self.haste: break
                self.events()
                if self.haste: break
                self.update()
                if self.haste: break
                #if self.transitioning: 
                 #   self.draw(noUpdate=True)
                  #  self.transitioning = False
            #    else: self.draw()
                self.draw()

    def events(self):
        def powerUpEvents():
            if "grapple" in self.avatar.inventory and len(self.grapplehook) == 0 and self.avatar.grappleCollCheck() and not self.avatar.stealth and self.avatar.grapplehookCount > 0: 
                Grapplehook(self, vec(self.avatar.pos.x + 8, self.avatar.pos.y + 1))
                self.avatar.grapplehookCount -= 1
            elif "stealth" in self.avatar.inventory:
                if self.avatar.stealth: self.avatar.stealth = False
                elif len(self.grapplehook) == 0:
                    self.avatar.stealth = True
                    self.avatar.last_stealth = pg.time.get_ticks() + POWERUP_TIMEOUT
        #UNHOLDABLE EVENTS
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                quit()
                #self.wantToQuit = True
                #self.resetLoops()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:   #AVATAR JUMPING
                    self.avatar.jump()
                if event.key == pg.K_UP or event.key == pg.K_w:
                    if self.avatar.nearElevator and not self.avatar.tryElevator: 
                        self.avatar.tryElevator = True
                if event.key == pg.K_DOWN or event.key == pg.K_s:
                    self.avatar.crouching = True
                if (event.key == pg.K_z or event.key == pg.K_k) and (self.avatar.jumping == False or self.avatar.para):                           #AVATAR SHOOTING
                    self.avatar.fireBullet()
                if event.key == pg.K_x or event.key == pg.K_l:
                    powerUpEvents()
                if event.key == pg.K_r:
                    self.restart()
                if event.key == pg.K_p or event.key == pg.K_ESCAPE:
                    self.pause()
                if event.key == pg.K_v: self.victory()
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
        if self.avatar.crouching: self.camera.update(self.avatar, updateY=False)
        else: self.camera.update(self.avatar)
        self.all_collisions()
        if self.avatar.elevatingIndex != 0: 
            self.elevation()

    def draw(self, noUpdate=False):
        #self.screen.fill(LIGHTGREY)
        self.screen.blit(self.background, self.camera.apply(pg.Rect(0, 0, self.map.pixelWidth, self.map.pixelHeight), isRect=True))
        for sprite in self.floors:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.walls:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.powerUps:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.powerUps:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.depthStatics:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.fallFloorDepthStatics:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.sensors:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.decor:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.laserEnds:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.kinetics:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        self.drawTempLines()
        self.hud()
        if not (noUpdate or self.restarting): 
            pg.display.flip()

    def drawGrid(self):
        for x in range(0, self.map.pixelWidth, TILESIZE):
            pg.draw.line(self.background, BLACK, (x, 0), (x, self.map.pixelHeight))
        for y in range(0, self.map.pixelHeight, TILESIZE):
            pg.draw.line(self.background, BLACK, (0, y), (self.map.pixelWidth, y))

    def connectBgSlices(self):
        bgSlice = pg.image.load(path.join(self.img_folder, 'backgroundSlice.png'))
        sliceNum = self.map.tileHeight / 6
        self.background = pg.Surface((bgSlice.get_width(), bgSlice.get_height() * sliceNum))
        i = 0
        while i <= sliceNum:
            self.background.blit(bgSlice, (0, i * bgSlice.get_height()))
            i += 1
        self.background = pg.transform.scale(self.background, (self.background.get_width() * 4, self.map.pixelHeight))

    def defineImgs(self):
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
        self.fallFloorImg = self.statics_sheet.getImage(24,12,12,12)

        self.avatarIdle0Img = self.avatar_sheet.getImage(0,33,12,30,36,90)
        self.avatarIdle1Img = self.avatar_sheet.getImage(0,66,12,30,36,90)
        self.avatarRightJump0Img = self.avatar_sheet.getImage(14,33,16,27,48,81)
        self.avatarRightJump1Img = self.avatar_sheet.getImage(30,33,17,25,51,75)
        self.avatarRightJump2Img = self.avatar_sheet.getImage(47,33,17,25,51,75)
        self.avatarRightJump3Img = self.avatar_sheet.getImage(64,33,16,23,48,69)
        self.avatarRightRun0Img = self.avatar_sheet.getImage(14,66,16,30,48,90)
        self.avatarRightRun1Img = self.avatar_sheet.getImage(30,66,16,30,48,90)
        self.avatarRightRun2Img = self.avatar_sheet.getImage(46,66,16,30,48,90)
        self.avatarRightRun3Img = self.avatar_sheet.getImage(62,66,13,30,39,90)
        self.avatarRightPara0Img = self.avatar_sheet.getImage(84,15,16,45,48,135)
        self.avatarRightPara1Img = self.avatar_sheet.getImage(100,14,17,44,51,132)
        self.avatarRightPara2Img = self.avatar_sheet.getImage(117,14,17,44,51,132)
        self.avatarRightPara3Img = self.avatar_sheet.getImage(134,14,16,42,48,126)
        self.avatarRightCrouchImg = self.avatar_sheet.getImage(96,99,14,24,42,70)
        self.avatarRightShoot0Img = self.avatar_sheet.getImage(0,99,16,30,48,90)
        self.avatarRightShoot1Img = self.avatar_sheet.getImage(16,99,16,30,48,90)
        self.avatarRightShoot2Img = self.avatar_sheet.getImage(32,99,17,30,51,90)
        self.avatarRightShoot3Img = self.avatar_sheet.getImage(49,99,16,30,48,90)
        self.avatarRightShoot4Img = self.avatar_sheet.getImage(65,99,16,30,48,90)
        self.avatarRightGrappleImg = self.avatar_sheet.getImage(81,99,15,30,45,90)
        self.avatarRightDeath0Img = self.avatar_sheet.getImage(75,66,18,28,54,84)
        self.avatarRightDeath1Img = self.avatar_sheet.getImage(93,66,18,27,54,81)
        self.avatarRightDeath2Img = self.avatar_sheet.getImage(111,66,27,30,81,90)
        self.avatarRightDeath3Img = self.avatar_sheet.getImage(138,66,27,30,81,90)
        self.avatarRightDeath4Img = self.avatar_sheet.getImage(111,96,27,30,81,90)
        self.avatarRightDeath5Img = self.avatar_sheet.getImage(138,96,27,30,81,90)

        self.avatarLeftJump0Img = pg.transform.flip(self.avatarRightJump0Img, True, False)
        self.avatarLeftJump1Img = pg.transform.flip(self.avatarRightJump1Img, True, False)
        self.avatarLeftJump2Img = pg.transform.flip(self.avatarRightJump2Img, True, False)
        self.avatarLeftJump3Img = pg.transform.flip(self.avatarRightJump3Img, True, False)
        self.avatarLeftRun0Img = pg.transform.flip(self.avatarRightRun0Img, True, False)
        self.avatarLeftRun1Img = pg.transform.flip(self.avatarRightRun1Img, True, False)
        self.avatarLeftRun2Img = pg.transform.flip(self.avatarRightRun2Img, True, False)
        self.avatarLeftRun3Img = pg.transform.flip(self.avatarRightRun3Img, True, False)
        self.avatarLeftPara0Img = pg.transform.flip(self.avatarRightPara0Img, True, False)
        self.avatarLeftPara1Img = pg.transform.flip(self.avatarRightPara1Img, True, False)
        self.avatarLeftPara2Img = pg.transform.flip(self.avatarRightPara2Img, True, False)
        self.avatarLeftPara3Img = pg.transform.flip(self.avatarRightPara3Img, True, False)
        self.avatarLeftCrouchImg = pg.transform.flip(self.avatarRightCrouchImg, True, False)
        self.avatarLeftShoot0Img = pg.transform.flip(self.avatarRightShoot0Img, True, False)
        self.avatarLeftShoot1Img = pg.transform.flip(self.avatarRightShoot1Img, True, False)
        self.avatarLeftShoot2Img = pg.transform.flip(self.avatarRightShoot2Img, True, False)
        self.avatarLeftShoot3Img = pg.transform.flip(self.avatarRightShoot3Img, True, False)
        self.avatarLeftShoot4Img = pg.transform.flip(self.avatarRightShoot4Img, True, False)
        self.avatarLeftGrappleImg = pg.transform.flip(self.avatarRightGrappleImg, True, False)
        self.avatarLeftDeath0Img = pg.transform.flip(self.avatarRightDeath0Img, True, False)
        self.avatarLeftDeath1Img = pg.transform.flip(self.avatarRightDeath1Img, True, False)
        self.avatarLeftDeath2Img = pg.transform.flip(self.avatarRightDeath2Img, True, False)
        self.avatarLeftDeath3Img = pg.transform.flip(self.avatarRightDeath3Img, True, False)
        self.avatarLeftDeath4Img = pg.transform.flip(self.avatarRightDeath4Img, True, False)
        self.avatarLeftDeath5Img = pg.transform.flip(self.avatarRightDeath5Img, True, False)
        
        self.bigBaddLeft0Img = self.baddie_sheet.getImage(0,0,12,31,48,124)
        self.bigBaddRight0Img = pg.transform.flip(self.bigBaddLeft0Img, True, False)
        self.sniperBaddLeft0Img = self.baddie_sheet.getImage(0,62,26,38,78,114)
        self.sniperBaddLeft1Img = self.baddie_sheet.getImage(26,62,28,40,84,120)
        self.sniperBaddRight0Img = pg.transform.flip(self.sniperBaddLeft0Img, True, False) 
        self.sniperBaddRight1Img = pg.transform.flip(self.sniperBaddLeft1Img, True, False)        
        self.quickBaddLeft0Img = self.baddie_sheet.getImage(0,31,13,31,52,124)
        self.quickBaddRight0Img = pg.transform.flip(self.quickBaddLeft0Img, True, False)
        self.bossLeft0Img = self.baddie_sheet.getImage(0,0,12,31,48,124)
        self.bossRight0Img = pg.transform.flip(self.bossLeft0Img, True, False)

        self.grappleImg = self.other_sheet.getImage(18,0,16,8,64,32)
        self.grapplehookImg = pg.transform.rotate(self.other_sheet.getImage(18,0,7,7,28,28), 270)
        self.bulletImg = self.other_sheet.getImage(0,0,6,4,18,12)
        self.bloodBulletImg = self.other_sheet.getImage(0,4,6,4,18,12)
        self.lifeImg = self.other_sheet.getImage(6,0,12,11,48,44)
        self.minigunImg = self.other_sheet.getImage(34,0,12,12)
        self.stealthImg = self.other_sheet.getImage(46,0,9,10,36,40)
        self.laserBeamHImg = self.statics_sheet.getImage(96,3,12,6,48,24)
        self.laserBeamVImg = self.statics_sheet.getImage(111,0,6,12,24,48)
        self.laserEndHBottomLeftImg = self.statics_sheet.getImage(97,14,11,10,44,40)
        self.laserEndHBottomRightImg = self.statics_sheet.getImage(108,14,11,10,44,40)
        self.laserEndHTopLeftImg = pg.transform.flip(self.laserEndHBottomLeftImg, False, True)
        self.laserEndHTopRightImg = pg.transform.flip(self.laserEndHBottomRightImg, False, True)
        self.laserEndVTopImg = self.statics_sheet.getImage(84,0,12,12)
        self.laserEndVBottomImg = self.statics_sheet.getImage(84,12,12,12)
        self.elevator0Img = self.statics_sheet.getImage(72,24,24,36,72,108)
        self.elevator1Img = self.statics_sheet.getImage(96,24,24,36,72,108)
        self.elevator2Img = self.statics_sheet.getImage(120,24,24,36,72,108)
        self.elevator3Img = self.statics_sheet.getImage(144,24,24,36,72,108)
        self.elevator4Img = self.statics_sheet.getImage(168,24,24,36,72,108)
        self.fireDoorImg = self.statics_sheet.getImage(96,60,24,36,72,108)
        
        self.brightTableImg = self.statics_sheet.getImage(0,60,22,12,88,48)
        self.darkTableImg = self.statics_sheet.getImage(53,68,16,12,64,48)
        self.darkChairImg = self.statics_sheet.getImage(62,60,7,8,28,32)
        self.desktopImg = self.statics_sheet.getImage(22,60,22,16,88,64)
        self.stoolUpImg = self.statics_sheet.getImage(44,60,8,10,32,40)
        self.stoolDownImg = self.statics_sheet.getImage(52,60,10,8,40,32)
        self.fireExtinguisherImg = self.statics_sheet.getImage(44,70,9,17,28,68)
        self.flaskImg = self.statics_sheet.getImage(69,60,13,12,52,48)
        self.testTubesImg = self.statics_sheet.getImage(82,60,13,16,52,64)
        self.treeImg = self.statics_sheet.getImage(0,72,11,21,44,84)
        self.televisionImg = self.statics_sheet.getImage(53,80,12,12)

        self.depthWallImg = self.statics_sheet.getImage(48,12,12,12)
        self.depthFloorImg = self.statics_sheet.getImage(36,12,12,12)
        self.depthFloorCornerImg = self.statics_sheet.getImage(36,0,12,12)
        self.depthFloorCliffImg = self.statics_sheet.getImage(48,0,12,12)
        self.depthFloorSideImg = self.statics_sheet.getImage(60,0,12,12)
        self.depthFloorCoverImg = self.statics_sheet.getImage(67,12,5,12,20,48)
        self.depthFloorCoverEdgeImg = self.statics_sheet.getImage(72,0,12,12)
        self.depthFloorCoverCornerImg = self.statics_sheet.getImage(72,12,12,12)
        self.depthDoorImg = self.statics_sheet.getImage(12,24,12,36,48,144)
        self.depthWindowImg = self.statics_sheet.getImage(48,24,5,36,20,144)
        self.depthWindowTopImg = self.statics_sheet.getImage(53,24,5,12,20,48)
        self.depthFallFloorImg = self.statics_sheet.getImage(72,24,12,12)
        self.depthFallFloorCliffImg = self.statics_sheet.getImage(84,24,12,12)
        self.hiddenBoxImg = pg.Surface((TILESIZE / 4, TILESIZE))
        self.hiddenBoxImg.set_alpha(0)

        self.pacRight0Img = self.other_sheet.getImage(12,12,12,13,48,52)
        self.pacRight1Img = self.other_sheet.getImage(24,12,9,13,36,52)
        self.pacLeft0Img = pg.transform.flip(self.pacRight0Img, True, False)
        self.pacLeft1Img = pg.transform.flip(self.pacRight1Img, True, False)
        self.cherryImg = self.other_sheet.getImage(36,12,12,12)

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
        self.quickBadds = pg.sprite.Group()
        self.sniperBadds = pg.sprite.Group()
        self.laserBeams = pg.sprite.Group()
        self.laserEnds = pg.sprite.Group()
        self.windows = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.depthStatics = pg.sprite.Group()
        self.fallFloorDepthStatics = pg.sprite.Group()
        self.elevators = pg.sprite.Group()
        self.fallFloors = pg.sprite.Group()
        self.powerUps = pg.sprite.Group()
        self.decor = pg.sprite.Group()

    def setupMap(self):
        for row in range(len(self.map.data)):
            for col in range(len(self.map.data[row])):   
                tile = self.map.data[row][col]
                #print((col,row))

                def checkCollidable(elitRow, elitCol, value=0):
                    if self.map.data[elitRow][elitCol] == 1 or self.map.data[elitRow][elitCol] == 2:
                        return True
                    else: return False

                if tile == 2:
                    if not checkCollidable(row, col + 1): Floor(self, col, row, img=self.floor1Img)
                    else: Floor(self, col, row)

                    if checkCollidable(row - 1, col + 1) == False and checkCollidable(row - 1, col) == False and checkCollidable(row, col + 1) == False:
                        DepthStatic(self, col + 1, row - 1, self.depthFloorCliffImg)
                    if len(self.map.data[row]) > col + 1 and len(self.map.data) > row + 1:
                        if checkCollidable(row, col + 1) == False and checkCollidable(row + 1, col + 1) == False and checkCollidable(row + 1, col) == False: 
                            DepthStatic(self, col + 1, row, self.depthFloorSideImg)
                    if len(self.map.data[row]) > col + 1 and len(self.map.data) > row + 1:
                        if checkCollidable(row + 1, col) == True and checkCollidable(row, col + 1) == False and checkCollidable(row + 1, col + 1) == False:
                            DepthStatic(self, col + 1, row, self.depthWallImg)
                    if checkCollidable(row - 1, col) == False and self.map.data[row - 3][col - 1] != 5 and self.map.data[row - 3][col - 1] != 5.5:
                        DepthStatic(self, col, row - 1, self.depthFloorImg)
                    if checkCollidable(row, col - 1) == False: 
                        DepthStatic(self, col - 1, row, self.depthFloorCoverImg, coll=True)
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
                    Door(self, col, row)
                    if len(self.map.data[row]) > col + 1:
                        DepthStatic(self, col + 1, row, self.depthDoorImg)
                    else: 
                        DepthStatic(self, col - 1/4 - 28/TILESIZE, row - 1, self.hiddenBoxImg, coll=True)
                if tile == 5.5:
                    Door(self, col, row, midLevel=True)
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
                    QuickBadd(self, col,row, 1)
                if tile == 16: 
                    if (self.map.data[row - 1][col] != tile):
                        LaserEnd(self, col,row, self.laserEndVTopImg, 0,0)
                    elif (self.map.data[row + 1][col] != tile):
                        LaserEnd(self, col,row, self.laserEndVBottomImg, 0,0)
                    else: 
                        LaserBeam(self, col,row, self.laserBeamVImg, 3,0)
                if tile == 17: 
                    if (self.map.data[row][col - 1] != tile):
                        LaserEnd(self, col,row, self.laserEndHBottomLeftImg, 1,0)
                    elif (self.map.data[row][col + 1] != tile):
                        LaserEnd(self, col,row, self.laserEndHBottomRightImg, 0,0)
                    else: 
                        LaserBeam(self, col,row, self.laserBeamHImg, 0,1)
                if tile == 18: 
                    if (self.map.data[row][col - 1] != tile):
                        LaserEnd(self, col,row, self.laserEndHTopLeftImg, 1,0)
                    elif (self.map.data[row][col + 1] != tile):
                        LaserEnd(self, col,row, self.laserEndHTopRightImg, 0,0)
                    else: 
                        LaserBeam(self, col,row, self.laserBeamHImg, 0,3)
                if tile == 19:
                    FallFloor(self, col, row)
                    DepthStatic(self, col, row - 1, self.depthFloorImg, fallFloor=True)
                if 28 <= tile <= 33:
                    CollDecor(self, col,row, tile)
                if 34 <= tile <= 37:
                    GhostDecor(self, col,row, tile)
                if tile == 42:
                    self.boss = Boss(self, col, row)

    def all_collisions(self):
        avatDoorHits = pg.sprite.spritecollide(self.avatar, self.doors, False)                      #AVATAR-DOORS
        if avatDoorHits:
            if self.avatar.vel.x > 0:
                if avatDoorHits[0].midLevel: self.currentStageType = 1
                else: self.levelUp()
            else:
                self.avatar.vel.x = 0
                self.avatar.acc.x = 0
                self.avatar.pos.x = avatDoorHits[0].rect.x + TILESIZE
        avatWindowHits = pg.sprite.spritecollide(self.avatar, self.windows, False)                  #AVATAR-WINDOWS
        if avatWindowHits:
            if not avatWindowHits[0].broken:
                self.avatar.injury(1)
                #self.effectsChannel.play(self.glassSound)
            if self.avatar.vel.x > 0:
                self.changeStageType(avatWindowHits[0])
            avatWindowHits[0].broken = False
            avatWindowHits[0].breaking = True         
        for decor in self.decor:                                                                    #DECOR-BULLETS
            decorBulletHits = pg.sprite.spritecollide(decor, self.bullets, False)
            if decorBulletHits and decor.destroy and decorBulletHits[0].source == "avatar": 
                #self.effectsChannel.play(self.damageSound)
                damageEffects(decor, self, "decor", 0.25)
                decor.dying = True
        pg.sprite.groupcollide(self.bullets, self.obstacles, True, False)                           #BULLETS-OBSTACLES
        pg.sprite.groupcollide(self.bullets, self.doors, True, False)                               #BULLETS-DOORS
        avatBaddieHits = pg.sprite.spritecollide(self.avatar, self.baddies, False)                  #AVATAR-BADDIES
        if avatBaddieHits:
            self.avatar.injury(1)
            #self.avatar.pos.x -= 5 * avatBaddieHits[0].orientation
        for baddie in self.baddies:                                                                 #BADDIES-BULLETS
            for bullet in self.bullets:
                if pg.sprite.collide_rect(bullet, baddie):
                    if bullet.source == "avatar" and self.freezeUpdate != baddie.source: 
                        baddie.lives -= 1
                        bullet.kill()
                        damageEffects(baddie, self, baddie.source)
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
                    #self.effectsChannel.play(self.glassSound)
        avatElevatorHits = pg.sprite.spritecollide(self.avatar, self.elevators, False)              #AVATAR-ELEVATORS
        if avatElevatorHits:
            for elevator in self.elevators:
                firstElevator = avatElevatorHits[0]
                self.secondElevator = firstElevator
                #print(firstElevator.rect.y - ELEVATOR_DISTANCE / TILESIZE + 6 == elevator.rect.y)
                if ((firstElevator.door == 0 and elevator.rect.y == firstElevator.rect.y - ELEVATOR_DISTANCE / TILESIZE + 6) or 
                (firstElevator.door == 1 and elevator.rect.y == firstElevator.rect.y + ELEVATOR_DISTANCE / TILESIZE + 6)):
                    self.secondElevator = elevator
                #print(secondElevator.rect.y - firstElevator.rect.y)
            if self.avatar.rect.left >= firstElevator.rect.left and self.avatar.rect.right <= firstElevator.rect.right and 1 > self.avatar.vel.x > -1: 
                if self.avatar.vel.y == 0: self.avatar.nearElevator = True
            if self.avatar.tryElevator and self.freezeUpdate != "avatar" and self.avatar.elevatingIndex == 0:
                self.avatar.elevatingIndex = 1
                self.firstElevator = firstElevator
                #self.secondElevator = secondElevator             
        avatPowerUpHits = pg.sprite.spritecollide(self.avatar, self.powerUps, True)                 #AVATAR-POWERUPS
        if avatPowerUpHits:
            if avatPowerUpHits[0].type == "life": self.avatar.lives += 1
            elif not avatPowerUpHits[0].type in self.avatar.inventory:
                self.avatar.inventory.append(avatPowerUpHits[0].type)
                if avatPowerUpHits[0].type == "minigun":
                    self.avatar.lastMinigunInit = pg.time.get_ticks()
                if avatPowerUpHits[0].type == "grapple": 
                    self.avatar.grapplehookCount = 3
            #self.effectsChannel.play(self.powerupSound)
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
                    #self.effectsChannel.play(self.grappleSound)
                    while self.avatar.rect.top > grapplehook.rect.bottom:
                        if self.avatar.lives <= 0: 
                            break
                            return
                        if pg.sprite.spritecollide(self.avatar, self.obstacles, False): break
                        self.avatar.rect.y -= GRAPPLEHOOK_SPEED / 5
                        self.camera.update(self.avatar)
                        self.events()
                        if self.avatar.lives > 0: self.update()
                        self.draw()
                    self.freezeUpdate = None
                    self.avatar.pos.y = self.avatar.rect.y
                    self.grappleLine = False
                    grapplehook.kill()
        avatLaserBeamHits = pg.sprite.spritecollide(self.avatar, self.laserBeams, False)            #AVAT-LASER_BEAMS
        if avatLaserBeamHits and avatLaserBeamHits[0].state == 1: self.avatar.injury(1)
        avatFallFloorHits = pg.sprite.spritecollide(self.avatar, self.fallFloors, False)            #AVAT-FALL_FLOORS
        avatFallFloorDepthHits = pg.sprite.spritecollide(self.avatar, self.fallFloorDepthStatics, False)
        if avatFallFloorHits and avatFallFloorHits[0].rect.bottom >= self.avatar.rect.bottom: 
            avatFallFloorHits[0].acc.y = GRAVITY                                                    #AVAT-FALL_FLOOR_DEPTHS
            if avatFallFloorDepthHits: avatFallFloorDepthHits[0].kill()
        for fallFloor in self.fallFloors:                                                           #FALL_FLOORS-FLOORS
            fallFloorFloorHits = pg.sprite.spritecollide(fallFloor, self.floors, False)
            if fallFloorFloorHits: fallFloor.kill()

    def restart(self, run=True):
        self.restarting = True
        self.currentStageType = 0
        oldLives = self.avatar.lives - 1
        self.all_sprites.empty()
        self.new()
        self.avatar.lives = oldLives
        if run: self.run()

    def resetLevel(self):
        self.levelNum = 1
        self.map = Map(self, self.mapList[self.levelNum - 1])

    def resetLoops(self):
        if self.wantToQuit: self.running = False
        self.playing = False
        self.paused = False
        self.moribund = False
        self.options = False
        self.prelude = False
        self.enterCode = False
        self.credits = False
        self.intro = False
        self.victorious = False
        self.transitioning = True

    def hud(self):
        if self.hudVisible:
            i = 1
            j = 1
            while i <= self.avatar.lives:
                self.lifeImg.set_colorkey(YELLOW)
                self.screen.blit(self.lifeImg, pg.Rect(WIDTH / 16 + i * TILESIZE * 1.125, TILESIZE / 3, TILESIZE, TILESIZE))
                i += 1
            while j <= self.avatar.grapplehookCount:
                self.grapplehookImg.set_colorkey(YELLOW)
                self.screen.blit(self.grapplehookImg, pg.Rect(WIDTH - WIDTH / 16 - j * TILESIZE * 1.125, TILESIZE / 3, TILESIZE, TILESIZE))
                j += 1
            drawText(self, "LEVEL " + str(self.levelNum), 42, WHITE, WIDTH / 2, TILESIZE / 2)

    def levelUp(self):
        self.transitioning = True
        x = -WIDTH
        self.levelNum += 1
        mover = pg.Surface((WIDTH, HEIGHT))
        mover.fill(random.choice([DOWNTONE_BLUE, RUSTED_BLUE, CHARCOAL_GREY]))
        drawText(self, "LEVEL " + str(self.levelNum), 72, WHITE, WIDTH / 2, HEIGHT / 2 - 36, screen=mover)
        self.map = Map(self, self.mapList[self.levelNum - 1])
        #self.windChannel.stop()

        while x <= 0:
            self.draw(noUpdate=True)
            self.screen.blit(mover, pg.Rect(x, 0, WIDTH, HEIGHT))
            pg.display.flip()
            for event in pg.event.get(): pass
            x += 12
        self.new()
        self.camera.update(self.avatar)
        wait(2000, None)
        while x <= WIDTH:
            self.draw(noUpdate=True)
            self.screen.blit(mover, pg.Rect(x, 0, WIDTH, HEIGHT))
            pg.display.flip()
            for event in pg.event.get(): pass
            x += 12

    def changeStageType(self, glass):
        self.currentStageType = 1
        if not self.avatar.para:
            self.avatar.para = True
            self.avatar.pos.x = glass.rect.right
            self.avatar.pos.y = glass.rect.top
            #self.effectsChannel.play(self.parachuteSound)
            3self.windChannel.play(self.windSound, loops=3)

    def start_screen(self):
        def drawTitles():
            drawText(self, "NEW GAME", 72, WHITE, WIDTH / 2, HEIGHT / 3)
            drawText(self, "PRESS SPACE TO START", 52, WHITE, WIDTH / 2, HEIGHT / 3 * 2)
        self.screen.fill(BLACK)
        self.new()
        #pg.mixer.music.load(path.join(self.audio_folder, "menu.wav"))
        #pg.mixer.music.play(loops=-1)
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
                    pg.quit()
                    quit()
                    #self.wantToQuit = True
                    #self.resetLoops()
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    pressed = True
                if event.type == pg.KEYUP and pressed == True and event.key == pg.K_SPACE:
                    self.intro = False
                if event.type == pg.JOYBUTTONUP:
                    if event.button == 0: 
                        self.intro = False

    def prelude_screen(self):
        def allowDrag():
            for event in pg.event.get(): pass
        self.screen.fill(BLACK)
        drawText(self, "AGENCY NAME REDACTED was alerted", 42, GREY, WIDTH / 2, HEIGHT / 11 * 2)
        drawText(self, "of dangerous operations going", 42, GREY, WIDTH / 2, HEIGHT / 11 * 3)
        drawText(self, "on inside Dr. Vomir's lab.", 42, GREY, WIDTH / 2, HEIGHT / 11 * 4)
        pg.display.flip()
        wait(3000, allowDrag)
        drawText(self, "So they called the best.", 42, GREY, WIDTH / 2, HEIGHT / 11 * 5.5)
        pg.display.flip()
        wait(3000, allowDrag)
        drawText(self, "The best was busy.", 42, GREY, WIDTH / 2, HEIGHT / 11 * 6.5)
        pg.display.flip()
        wait(3000, allowDrag)
        drawText(self, "So they called you.", 42, GREY, WIDTH / 2, HEIGHT / 11 * 7.5)
        pg.display.flip()
        wait(3000, allowDrag)

    def game_over(self):
        def gravedigger(pressed):
            for event in pg.event.get():
                if event.type == pg.QUIT: 
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN: pressed = True
                if event.type == pg.KEYUP and pressed: 
                    pg.quit()
                    quit()
                    #self.resetLoops()
                    #self.resetLevel()
            return pressed
        
        pressed = False
        self.avatar.invulnerable = True
        self.draw()
        self.moribund = True
        now = pg.time.get_ticks()
        last_wait = pg.time.get_ticks()
        while now < last_wait + 3000 and not self.restarting:
            if self.avatar.orientation > 1: self.avatar.image, self.avatar.dyingAnimateIndex = animateSprite(self.avatar.dyingAnimateIndex, [self.avatarRightDeath0Img, self.avatarRightDeath1Img, self.avatarRightDeath2Img, self.avatarRightDeath3Img, self.avatarRightDeath4Img, self.avatarRightDeath5Img], delayTime=0.05, suspend=True)
            else: self.avatar.image, self.avatar.dyingAnimateIndex = animateSprite(self.avatar.dyingAnimateIndex, [self.avatarLeftDeath0Img, self.avatarLeftDeath1Img, self.avatarLeftDeath2Img, self.avatarLeftDeath3Img, self.avatarLeftDeath4Img, self.avatarLeftDeath5Img], delayTime=0.05, suspend=True)
            self.avatar.image.set_colorkey(YELLOW)
            self.events()
            self.draw()
            now = pg.time.get_ticks()
        self.resetLevel()
        while self.moribund:
            drawMenuBox(self, WIDTH / 3.25, HEIGHT / 3, WIDTH / 2.5, HEIGHT / 4, NAVY, GREY)
            drawText(self, "GAME OVER", 72, WHITE, WIDTH / 2, HEIGHT / 2.5)
            for event in pg.event.get():
                if event.type == pg.QUIT: 
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN: pressed = True
                if event.type == pg.KEYUP and pressed: 
                    pg.quit()
                    quit()
                    #self.haste = True
                    #self.resetLoops()
            pg.display.flip()
        self.restarting = False

    def pause(self):
        self.paused = True
        spots = ["RESUME","OPTIONS","EXIT"]
        i = 0
        yPos = 0
        #pg.mixer.music.load(path.join(self.audio_folder, "menu.wav"))
        #pg.mixer.music.play(loops=-1)
        drawMenuBox(self, WIDTH / 3, HEIGHT / 6, WIDTH / 3, HEIGHT / 1.5, NAVY, GREY, 10)
        for index in range(len(spots)):
            drawText(self, spots[index], 64, GREY, WIDTH / 2, HEIGHT / 9 * (2 + yPos))
            yPos += 2
        yPos = 0
        while self.paused:
            i = scrollMenu(spots, i)
            for index in range(len(spots)):
                if index == int(i): drawText(self, spots[index], 64, WHITE, WIDTH / 2, HEIGHT / 9 * (2 + yPos))
                else: drawText(self, spots[index], 64, GREY, WIDTH / 2, HEIGHT / 9 * (2 + yPos))
                yPos += 2
            yPos = 0
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                    #self.wantToQuit = True
                    #self.resetLoops()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE or event.key == pg.K_p: self.paused = False
                    elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                        if int(i) == 0:
                            self.paused = False
                        elif int(i) == 1:
                            self.optionsMenu()
                        elif int(i) == 2:
                            self.resetLevel()
                            self.resetLoops()
            pg.display.flip()
        #pg.mixer.music.load(path.join(self.audio_folder, "levels.wav"))
        #pg.mixer.music.play()

    def optionsMenu(self):
        self.options = True
        spots = ["MUSIC","ENTER CODE","CREDITS"]
        i = 0
        yPos = 0
        drawMenuBox(self, WIDTH / 3, HEIGHT / 6, WIDTH / 3, HEIGHT / 1.5, NAVY, GREY, 10)
        self.escapeDialog()
        for index in range(len(spots)):
            drawText(self, spots[index], 64, GREY, WIDTH / 2, HEIGHT / 9 * (2 + yPos))
            yPos += 2
        yPos = 0
        while self.options:
            i = scrollMenu(spots, i)
            for index in range(len(spots)):
                if index == int(i): drawText(self, spots[index], 64, WHITE, WIDTH / 2, HEIGHT / 9 * (2 + yPos))
                else: drawText(self, spots[index], 64, GREY, WIDTH / 2, HEIGHT / 9 * (2 + yPos))
                yPos += 2
            yPos = 0
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                    #self.wantToQuit = True
                    #self.resetLoops()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        self.options = False
                    elif event.key == pg.K_p:
                        self.options = False
                        self.paused = False
                    elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                        """if int(i) == 0: 
                            if pg.mixer.music.get_volume() == 0:
                                pg.mixer.music.set_volume(0.15)
                                self.musicOn = 1
                            else: 
                                pg.mixer.music.set_volume(0)
                                self.musicOn = 0
                            self.writeUserInfo()"""
                        if int(i) == 1: self.codeScreen()
                        if int(i) == 2: self.creditsMenu()
            pg.display.update()
        self.draw()
        drawMenuBox(self, WIDTH / 3, HEIGHT / 6, WIDTH / 3, HEIGHT / 1.5, NAVY, GREY, 10)

    def creditsMenu(self):
        self.credits = True
        pressed = False
        drawMenuBox(self, WIDTH / 4, HEIGHT / 6.15, WIDTH / 2, HEIGHT / 1.35, NAVY, GREY, 10)
        self.escapeDialog()
        while self.credits:
            drawText(self, "DIRECTOR: ", 28, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 2)
            drawText(self, "ARTISTS:", 28, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 3.25)
            drawText(self, "LEVEL DESIGNER: ", 28, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 7.5)
            drawText(self, "COMPOSER: ", 28, WHITE, WIDTH / 8 * 3, HEIGHT / 11 * 8.75)
            drawText(self, "CALEB BAYLES", 24, GREY, WIDTH / 8 * 5, HEIGHT / 11 * 2)
            drawText(self, "SAM WITT", 24, GREY, WIDTH / 8 * 5, HEIGHT / 11 * 3.25)
            drawText(self, "JORDAN MIZE", 24, GREY, WIDTH / 8 * 5, HEIGHT / 11 * 4.25)
            drawText(self, "ZACH BALVANZ", 24, GREY, WIDTH / 8 * 5, HEIGHT / 11 * 5.25)
            drawText(self, "JOEY JONES", 24, GREY, WIDTH / 8 * 5, HEIGHT / 11 * 6.25)
            drawText(self, "ERIC TRICKEY", 24, GREY, WIDTH / 8 * 5, HEIGHT / 11 * 7.5)
            drawText(self, "EVAN BOSAW", 24, GREY, WIDTH / 8 * 5, HEIGHT / 11 * 8.75)
            pg.display.flip()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                    #self.wantToQuit = True
                    #self.resetLoops()
                if event.type == pg.KEYDOWN:
                    pressed = True
                if event.type == pg.KEYUP and pressed:
                    self.credits = False
        self.draw()
        drawMenuBox(self, WIDTH / 3, HEIGHT / 6, WIDTH / 3, HEIGHT / 1.5, NAVY, GREY, 10)
        self.escapeDialog()

    def codeScreen(self):
        self.enterCode = True
        pressed = False
        self.draw()
        codes = ["tree", "7599", "zoom", "neon", "mtrx", "a113", "link", "gonk", "bibc", "nunb", "keys"]
        codeBox = ["_", "_", "_", "_"]
        j = 0
        joe = False
        entering = False
        while self.enterCode:
            i = 0
            drawMenuBox(self, WIDTH / 4, HEIGHT / 6.15, WIDTH / 2, HEIGHT / 1.5, NAVY, GREY, 10)
            self.escapeDialog()
            drawText(self, "ENTER CODE:", 64, WHITE, WIDTH / 2, HEIGHT / 11 * 3)
            while i < len(codeBox): 
                if i == j: codeColor = WHITE
                else: codeColor = GREY
                drawText(self, codeBox[i], 68, codeColor, WIDTH / 11 * (i + 4), HEIGHT / 11 * 5)
                i += 1
            for event in pg.event.get():
                if event.type == pg.QUIT: 
                    pg.quit()
                    quit()
                    #self.wantToQuit = True
                    #self.resetLoops()
                if event.type == pg.KEYDOWN:
                    joe = (pg.key.get_mods() or 
                        (event.key == pg.K_BACKSPACE or event.key == pg.K_SPACE or event.key == pg.K_UP or event.key == pg.K_DOWN) or
                        (event.key == pg.K_TAB or event.key == pg.K_CAPSLOCK or event.key == pg.K_BREAK or event.key == pg.K_CLEAR) or
                        (event.key == pg.K_INSERT or event.key == pg.K_DELETE or event.key == pg.K_END or event.key == pg.K_FIRST) or
                        (event.key == pg.K_HELP or event.key == pg.K_HOME or event.key == pg.K_LAST or event.key == pg.K_PRINT) or 
                        (event.key == pg.K_F1 or event.key == pg.K_F2 or event.key == pg.K_F3 or event.key == pg.K_F4) or 
                        (event.key == pg.K_F5 or event.key == pg.K_F6 or event.key == pg.K_F7 or event.key == pg.K_F8) or 
                        (event.key == pg.K_F9 or event.key == pg.K_F10 or event.key == pg.K_F11 or event.key == pg.K_F12))
                    if event.key == pg.K_ESCAPE:
                        pressed = True
                    elif event.key == pg.K_RETURN: 
                        entering = True
                        last_enter = pg.time.get_ticks()
                    elif event.key == pg.K_LEFT: j -= 1
                    elif event.key == pg.K_RIGHT: j += 1
                    elif not joe: 
                        codeBox[j] = chr(event.key)
                        j += 1
                    if j >= len(codeBox): j = 0
                    if j < 0: j = len(codeBox) - 1
                if event.type == pg.KEYUP and pressed:
                    self.draw()
                    self.enterCode = False
            inpCode = "".join(codeBox)
            drawText(self, "Press \"Enter\"", 48, GREY, WIDTH / 2, HEIGHT / 5 * 3)
            drawText(self, "to submit a code", 48, GREY, WIDTH / 2, HEIGHT / 5 * 3 + HEIGHT / 11)
            if inpCode in codes and entering: 
                if inpCode == "link": pass
                elif inpCode == "a113": pass
                elif inpCode == "7599": pass
                elif inpCode == "nunb": pass
                elif inpCode == "tree": self.treePowers = True
                elif inpCode == "zoom": self.friction = 0.10
                elif inpCode == "neon": self.grappleColor = WHITE
                elif inpCode == "mtrx": self.bulletSpeed = 10
                elif inpCode == "gonk": pass
                elif inpCode == "bibc": pass
                elif inpCode == "keys": 
                    self.blinky = True
                    self.avatar.pac()
                now = pg.time.get_ticks()
                if now < 2000 + last_enter: 
                    self.screen.fill(NAVY, rect=pg.Rect(WIDTH / 4, HEIGHT / 5 * 3, WIDTH / 2, HEIGHT / 11 * 2))
                    drawText(self, "ACCEPTED!", 54, GREEN, WIDTH / 2, HEIGHT / 5 * 3 + HEIGHT / 11 * 0.5)
                else: entering = False
            pg.display.flip()
        self.draw()
        drawMenuBox(self, WIDTH / 3, HEIGHT / 6, WIDTH / 3, HEIGHT / 1.5, NAVY, GREY, 10)
        self.escapeDialog()

    def escapeDialog(self):
        drawMenuBox(self, WIDTH / 11, HEIGHT / 5, WIDTH / 6, HEIGHT / 11 * 2, NAVY, GREY, 10)
        drawText(self, "ESC TO", 48, GREY, WIDTH / 6, HEIGHT / 11 * 2.2)
        drawText(self, "GO BACK", 48, GREY, WIDTH / 6, HEIGHT / 11 * 3.2)

    def drawTempLines(self):
        if self.grappleLine:
            for grapplehook in self.grapplehook:
                if self.avatar.orientation > 0:
                    pg.draw.line(self.screen, self.grappleColor, (self.camera.apply(self.avatar).left + 12, self.camera.apply(self.avatar).top), self.camera.apply(grapplehook).center, 4)
                else:
                    pg.draw.line(self.screen, self.grappleColor, (self.camera.apply(self.avatar).right - 12, self.camera.apply(self.avatar).top), self.camera.apply(grapplehook).center, 4)

    def drawBackgroundText(self):
        if self.textOn == 0: return
        elif self.levelNum == 1: 
            drawText(self, "A OR LEFT TO MOVE LEFT", 36, BLACK, 6 * TILESIZE, 26 * TILESIZE, screen=self.background)
            drawText(self, "D OR RIGHT TO MOVE RIGHT", 36, BLACK, 6 * TILESIZE, 27 * TILESIZE, screen=self.background)
            drawText(self, "W OR UP TO USE ELEVATORS", 36, BLACK, 25 * TILESIZE, 26 * TILESIZE, screen=self.background)
            drawText(self, "K OR Z TO SHOOT", 36, BLACK, 26 * TILESIZE, 20 * TILESIZE, screen=self.background)
            drawText(self, "SPACEBAR TO JUMP", 36, BLACK, 25 * TILESIZE, 14 * TILESIZE, screen=self.background)
            drawText(self, "L OR X TO USE POWER-UPS", 36, BLACK, 36 * TILESIZE, 14 * TILESIZE, screen=self.background)
            drawText(self, "YOU HAVE 3 GRAPPLING HOOKS", 36, BLACK, 36 * TILESIZE, 15 * TILESIZE, screen=self.background)
            drawText(self, "R TO RESTART", 36, BLACK, 10 * TILESIZE, 14 * TILESIZE, screen=self.background)
            drawText(self, "YOU'LL LOSE A LIFE", 36, BLACK, 10 * TILESIZE, 15 * TILESIZE, screen=self.background)
        elif self.levelNum == 2:
            drawText(self, "S OR DOWN TO DUCK UNDER BULLETS", 36, BLACK, 35 * TILESIZE, 20 * TILESIZE, screen=self.background)

    def writeUserInfo(self):
        with open(path.join(self.main_folder, 'userPrefs'), 'w') as file:
            file.write(str(self.musicOn) + "\n")
            file.write(str(self.textOn) + "\n")

    def readUserInfo(self, line):
        with open(path.join(self.main_folder, 'userPrefs'), 'r') as file:
            museLine = file.readline()
            textLine = file.readline()
            if line == 1: return int(museLine)
            elif line == 2: return int(textLine)

    def victory(self):
        self.victorious = True
        pressed = False
        now = pg.time.get_ticks()
        last_wait = now
        while now < last_wait + 1500:
            self.events()
            self.draw()
            now = pg.time.get_ticks()
        while self.victorious:
            drawMenuBox(self, WIDTH / 5, HEIGHT / 3, WIDTH / 1.625, HEIGHT / 2.5, NAVY, GREY)
            drawText(self, "You foiled Dr. Vomir's", 48, WHITE, WIDTH / 2, HEIGHT / 11 * 5)
            drawText(self, "sinister plans! Good work!", 48, WHITE, WIDTH / 2, HEIGHT / 11 * 6)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                if event.type == pg.KEYDOWN: pressed = True
                if event.type == pg.KEYUP and pressed:
                    self.haste = True
                    self.resetLevel()
                    self.screen.fill(BLACK)
                    self.creditsMenu()
                    self.resetLoops()
            pg.display.flip()

    def elevation(self):
        def elevateAvatar():
            if self.firstElevator.door == 0:
                while self.avatar.rect.y > self.avatar.pos.y - ELEVATOR_DISTANCE:
                    self.avatar.rect.y -= 6
                    self.camera.update(self.avatar)
                    for sprite in self.all_sprites:
                        if id(sprite) != id(self.avatar): sprite.update()
                    self.draw()
            elif self.firstElevator.door == 1: 
                while self.avatar.rect.y < self.avatar.pos.y + ELEVATOR_DISTANCE:
                    self.avatar.rect.y += 6
                    self.camera.update(self.avatar)
                    for sprite in self.all_sprites:
                        if id(sprite) != id(self.avatar): sprite.update()
                    self.draw()
                    self.draw()
            self.avatar.elevatingIndex += 1
        def openElevator(door):
            door.elevateForAnimation = 1
            self.avatar.elevatingIndex += 1
        def closeElevator(door):
            door.elevateForAnimation = 2
            if self.avatar.elevatingIndex >= 7: self.avatar.elevatingIndex = 0
            else: self.avatar.elevatingIndex += 1
            if door.animateIndex >= 5: door.animateIndex = 0
        def prepAvatar():
            self.avatar.invulnerable = True
            self.freezeUpdate = "avatar"
            self.avatar.rect.centerx = self.firstElevator.rect.centerx
            self.avatar.vel.y = 0
            self.avatar.vel.x = 0
            self.avatar.acc.x = 0
            self.avatar.tryElevator = False
            self.avatar.image.set_alpha(0)
            self.avatar.elevatingIndex += 1
        def restoreAvatar():
            self.avatar.invulnerable = False
            self.avatar.rect.centerx = self.secondElevator.rect.centerx
            #self.avatar.vel.y = 0
            #self.avatar.vel.x = 0
            #self.avatar.acc.x = 0
            self.avatar.tryElevator = False
            self.avatar.image.set_alpha(255)
            self.freezeUpdate = None
            self.avatar.pos.y = self.avatar.rect.y
            self.avatar.elevatingIndex += 1

        e = self.avatar.elevatingIndex
        if e == 1: openElevator(self.firstElevator)
        elif e == 2 and self.firstElevator.animateIndex >= 5: prepAvatar()
        elif e == 3: closeElevator(self.firstElevator)
        elif e == 4: elevateAvatar()
        elif e == 5: openElevator(self.secondElevator)
        elif e == 6 and self.secondElevator.animateIndex >= 5: restoreAvatar()
        elif e == 7: closeElevator(self.secondElevator)

g = Game()
g.prelude_screen()
while g.running:
    g.haste = False
    g.start_screen()
    g.new()
    #pg.mixer.music.load(path.join(g.audio_folder, "levels.wav"))
    #pg.mixer.music.play(loops=-1)
    g.run()
pg.quit()
quit()
