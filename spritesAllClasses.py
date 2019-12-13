import pygame as pg
import random
from settings import *
from other import *
vec = pg.math.Vector2

class Static(pg.sprite.Sprite):
    def __init__(self, game, x,y, groups, img):
        pg.sprite.Sprite.__init__(self, groups)
        self.image = img
        self.game = game
        self.rect = self.image.get_rect()
        self.pos = vec(x * TILESIZE, y * TILESIZE)
        self.rect.topleft = self.pos
class Obstacle(Static):
    def __init__(self, game, x,y, groups, img):
        super().__init__(game, x,y, groups, img)
class Wall(Obstacle):
    def __init__(self, game, x,y):
        self.groups = game.all_sprites, game.statics, game.obstacles, game.walls
        if y % 6 == 0: self.image = game.wall2Img
        elif y % 2 == 0: self.image = game.wall1Img
        else: self.image = game.wall0Img
        super().__init__(game, x,y, self.groups, self.image)
class Floor(Obstacle):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.statics, game.obstacles, game.floors
        if y % 2 == 0: 
            self.image = game.floor0Img
        else: self.image = game.floor1Img
        super().__init__(game, x,y, self.groups, self.image)
class PowerUp(Static):
    def __init__(self, game, x, y, type):
        self.groups = game.all_sprites, game.statics, game.powerUps
        if type == 8: 
            self.type = "grapple"
            self.image = game.grappleImg
        if type == 9: 
            self.type = "life"
            self.image = game.lifeImg
        if type == 10: 
            self.type = "minigun"
            #self.image = game.minigunImg
            self.image = pg.Surface((TILESIZE, TILESIZE))
        if type == 11: 
            self.type = "stealth"
            #self.image = game.stealthImg
            self.image = pg.Surface((TILESIZE,TILESIZE))
        self.image.set_colorkey(YELLOW)
        super().__init__(game, x,y, self.groups, self.image)
class Sensor(Static):
    def __init__(self, game, x,y, groups, img):
        super().__init__(game, x,y, groups, img)
class Door(Sensor):
    def __init__(self, game, x,y, location):
        self.groups = game.all_sprites, game.statics, game.sensors, game.doors
        if location == 0: self.image = game.doorFirstImg
        else: self.image = game.doorFinalImg
        self.image.set_colorkey(YELLOW)
        super().__init__(game, x,y, self.groups, self.image)
class Window(Sensor):
    def __init__(self, game, x,y):
        self.groups = game.all_sprites, game.statics, game.sensors, game.windows
        self.image = game.windowImg
        self.image.set_colorkey(YELLOW)
        self.broken = False
        self.breakAnimateIndex = 0
        self.breaking = False
        super().__init__(game, x,y, self.groups, self.image)

    def update(self):
        if self.breaking: 
            self.image, self.breakAnimateIndex = animateSprite(self.breakAnimateIndex, [self.game.windowCrackedImg, self.game.windowGoneImg], 0.15)
            if self.breakAnimateIndex > 1:
                self.breaking = False
        self.image.set_colorkey(YELLOW)
class Elevator(Sensor):
    def __init__(self, game, x,y, door):
        self.groups = game.all_sprites, game.statics, game.elevators
        self.image = pg.Surface((TILESIZE, TILESIZE * 2))
        self.image.fill(BLUE)
        self.door = door
        super().__init__(game, x,y, self.groups, self.image)
class DepthStatic(Static):
    def __init__(self, game, x,y, image):
        self.groups = game.all_sprites, game.statics, game.depthStatics
        self.image = image
        self.image.set_colorkey(YELLOW)
        super().__init__(game, x,y, self.groups, self.image)

class Kinetic(pg.sprite.Sprite):
    def __init__(self, game, x,y, groups, img, vel, acc):
        pg.sprite.Sprite.__init__(self, groups)
        self.image = img
        self.game = game
        self.rect = self.image.get_rect()
        self.pos = vec(x * TILESIZE, y * TILESIZE)
        self.rect.topleft = self.pos
        self.vel = vel
        self.acc = acc

    def update(self):
        self.acc.x += self.vel.x * -FRICTION
        self.vel += self.acc
        self.pos.x += self.vel.x + 0.5 * self.acc.x# * self.game.dt
        self.pos.y += self.vel.y * self.game.dt
        self.rect.topleft = self.pos
class Character(Kinetic):
    def __init__(self, game, x,y, groups, img, vel, acc, lives, orientation, source):
        super().__init__(game, x,y, groups, img, vel, acc)
        self.lives = lives
        self.source = source
        self.orientation = orientation

    def update(self):
        if self.game.freezeUpdate == self.source: return
        Kinetic.update(self)

    """ def collide_with_obstacles(self, direction):
        obstacleHits = pg.sprite.spritecollide(self, self.game.obstacles, False)
        if obstacleHits:
            if direction == 'x':
                if self.vel.x > 0:
                    self.pos.x = (obstacleHits[0].rect.left - self.rect.width)
                if self.vel.x < 0:
                    self.pos.x = (obstacleHits[0].rect.right)
                self.vel.x = 0
                #self.rect.x = self.pos.x
            if direction == 'y':
                if self.vel.y > 0:
                    self.pos.y = (obstacleHits[0].rect.top - self.rect.height)
                if self.vel.y < 0:
                    self.pos.y = (obstacleHits[0].rect.bottom)
                self.vel.y = 0
                #self.rect.y = self.pos.y
                self.jumping = False"""
    def damageEffects(self):
        tempImg1 = self.image.copy()
        tempImg2 = self.image.copy()
        tempImg3 = self.image.copy()
        tempImg1.set_alpha(64)
        tempImg2.set_alpha(122)
        tempImg3.set_alpha(32)

        if self.game.freezeUpdate != self.source:
            animationIndex = 0
            self.game.freezeUpdate = self.source
            
            while animationIndex < 3:
                animationIndex += 0.5
                if 1 <= animationIndex < 2:
                    self.image = tempImg1
                if 2 <= animationIndex < 3:
                    self.image = tempImg2
                else: self.image = tempImg3
                self.game.events()
                self.game.update()
                self.game.draw()
            self.game.freezeUpdate = None
class Avatar(Character):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.kinetics, game.characters
        super().__init__(game, x,y, self.groups, game.avatarIdle0Img, vec(0,0), vec(0, GRAVITY), 3, 1, "avatar")
        self.height = TILESIZE / 1.6
        self.jumping = False
        self.para = False
        self.paraTorn = False
        self.nearLadder = False
        self.invulnerable = False
        self.tryElevator = False
        self.nearElevator = False
        self.stealth = False
        self.crouching = False
        self.shootingForAnimation = False
        self.inventory = []
        self.last_shot = 0
        self.last_stealth = 0
        self.last_injury = 0
        self.lastMinigunInit = 0
        self.grapplehook = None
        self.jumpAnimateIndex = 0
        self.idleAnimateIndex = 0
        self.runAnimateIndex = 0
        self.crouchAnimateIndex = 0
        self.shootAnimateIndex = 0

    def update(self):
        if self.vel.x < 0:
            self.image, self.runAnimateIndex = animateSprite(self.runAnimateIndex, [self.game.avatarLeftRun0Img, self.game.avatarLeftRun1Img, self.game.avatarLeftRun2Img, self.game.avatarLeftRun3Img], 0.25)
        elif self.vel.x > 0:
            self.image, self.runAnimateIndex = animateSprite(self.runAnimateIndex, [self.game.avatarRightRun0Img, self.game.avatarRightRun1Img, self.game.avatarRightRun2Img, self.game.avatarRightRun3Img], 0.25)
        else:
            self.image = self.game.avatarIdle0Img
        if 1 > self.vel.x > -1: 
            if self.vel.x < 0: self.image, self.idleAnimateIndex = animateSprite(self.idleAnimateIndex, [pg.transform.flip(self.game.avatarIdle0Img, True, False), pg.transform.flip(self.game.avatarIdle0Img, True, False), pg.transform.flip(self.game.avatarIdle1Img, True, False)], 0.25)
            else: self.image, self.idleAnimateIndex = animateSprite(self.idleAnimateIndex, [self.game.avatarIdle0Img, self.game.avatarIdle0Img, self.game.avatarIdle1Img], 0.25)
        if self.shootingForAnimation: 
            if self.vel.x < 0: self.image = self.game.avatarLeftShoot0Img
            else: self.image = self.game.avatarRightShoot0Img
            now = pg.time.get_ticks()
            if now - self.last_shot > AVAT_BULLET_DELAY / 2:
                self.shootingForAnimation = False
                self.image = self.game.avatarIdle0Img
        self.image.set_alpha(255)
        super().update()
        self.rect = pg.Rect((self.pos.x, self.pos.y, TILESIZE, self.height))
        #if self.crouching: self.pos.x += (self.vel.x + 0.5 * self.acc.x * self.game.dt) / 2
        #else: self.pos.x += self.vel.x + 0.5 * self.acc.x * self.game.dt
        self.rect.x = self.pos.x
        self.collide_with_obstacles('x')
        #Kinetic.update(self)
        self.rect.y = self.pos.y
        yColl = self.collide_with_obstacles('y')
        """if yColl: 
            self.jumping = False
            if self.vel.y > 0:
                if self.vel.y > 895:
                    self.lives -= 3
                if self.para:
                    self.paraTorn = True
                    self.para = False"""
        if self.pos.x < 0 or self.pos.x > self.game.map.pixelWidth or self.pos.y > self.game.map.pixelHeight:
            self.lives -= 1
            self.game.restart()
        if self.crouching and self.height != TILESIZE:
            self.rect.y += 1
            hits = pg.sprite.spritecollide(self, self.game.obstacles, False)
            self.rect.y -= 1
            if hits:
                if self.vel.x < 0: self.image = pg.transform.flip(self.game.avatarRightCrouchImg, True, False)
                else: self.image = self.game.avatarRightCrouchImg
                self.rect = self.image.get_rect()
                self.rect.y = self.pos.y + TILESIZE
                self.rect.x = self.pos.x
                self.vel.x = 0
        if self.lives <= 0:
            self.game.game_over()
        if self.lives > 3:
            self.lives = 3
        if not self.para:
            self.height = TILESIZE * 2
            self.acc.y = GRAVITY
        if self.para:
            self.height = TILESIZE * 3 - 10
            self.acc.y = 0
            self.vel.y = 64
            self.rect.y = self.pos.y
        if self.game.currentStageType == 1 and self.paraTorn == False:
            self.para = True
        if self.game.currentStageType == 0:
            self.para = False
        if self.jumping or self.vel.y > GRAVITY:
            if self.vel.x < 0: self.image, self.jumpAnimateIndex = animateSprite(self.jumpAnimateIndex, [self.game.avatarLeftJump0Img, self.game.avatarLeftJump1Img, self.game.avatarLeftJump2Img, self.game.avatarLeftJump3Img], 0.25)
            else: self.image, self.jumpAnimateIndex = animateSprite(self.jumpAnimateIndex, [self.game.avatarRightJump0Img, self.game.avatarRightJump1Img, self.game.avatarRightJump2Img, self.game.avatarRightJump3Img], 0.25)
            if self.stealth: self.image.set_alpha(122)
        if self.stealth:
            now = pg.time.get_ticks()
            if now - self.last_stealth > POWERUP_TIMEOUT:
                self.image.set_alpha(255)
                self.stealth = False
                self.inventory.remove("stealth")
                self.last_stealth = 0
            else:
                self.image.set_alpha(122)
        
        self.image.set_colorkey(YELLOW)

    def collide_with_obstacles(self, direction):
        obstacleHits = pg.sprite.spritecollide(self, self.game.obstacles, False)
        if obstacleHits:
            if direction == 'x':
                if self.vel.x > 0:
                    self.pos.x = (obstacleHits[0].rect.left - self.rect.width)
                if self.vel.x < 0:
                    self.pos.x = (obstacleHits[0].rect.right)
                self.rect.x = self.pos.x
            if direction == 'y':
                if self.vel.y > 0:
                    self.pos.y = (obstacleHits[0].rect.top - self.rect.height)
                    if self.vel.y > 895:
                        self.lives -= 3
                    if self.para:
                        self.paraTorn = True
                        self.para = False
                if self.vel.y < 0:
                    self.pos.y = (obstacleHits[0].rect.bottom)
                self.vel.y = 0
                self.rect.y = self.pos.y
                self.jumping = False

    def jump(self):
        self.rect.y += 1
        hits = pg.sprite.spritecollide(self, self.game.obstacles, False)
        self.rect.y -= 1
        if hits and not self.jumping and not self.para:
            self.jumping = True
            self.acc.y = -AVATAR_JUMP

    def jumpCut(self):
        if self.jumping and self.vel.y < -2 * AVATAR_JUMP:
            self.vel.y = -2 * AVATAR_JUMP

    def fireBullet(self):
        now = pg.time.get_ticks()
        if self.game.grappleLine:
            return
        if self.vel.x < 0: spawn = self.rect.left
        else: spawn = self.rect.right
        if now - self.last_shot > AVAT_MINIGUN_DELAY and "minigun" in self.inventory and now < POWERUP_TIMEOUT + self.lastMinigunInit:
            self.last_shot = now
            Bullet(self.game, vec(spawn, self.rect.top + TILESIZE / 2), vec(self.orientation * BULLET_SPEED, 0), "avatar")
        elif now - self.last_shot > AVAT_BULLET_DELAY:
            self.last_shot = now
            Bullet(self.game, vec(spawn, self.rect.top + TILESIZE / 11 * 5), vec(self.orientation * BULLET_SPEED, 0), "avatar")
        self.shootingForAnimation = True

    def injury(self, damage):
        self.invulnerable = True
        now = pg.time.get_ticks()
        if now - self.last_injury > INVULNERABLE_TIME:
            self.last_injury = now
            self.invulnerable = False
        if not self.invulnerable:
            self.lives -= damage
            self.damageEffects()
class Baddie(Character):
    def __init__(self, game, groups, x, y, orientation, lives, vel, bulletDelay, imgPair, source):
        self.image = imgPair[0]
        self.pos = vec(x * TILESIZE, y * TILESIZE + TILESIZE)
        super().__init__(game, x,y, groups, self.image, vec(random.choice([vel, -vel]), 0), vec(0, GRAVITY), lives, orientation, source)
        self.last_shot = 0
        self.bulletDelay = bulletDelay
        self.rect.topleft = self.pos
        self.animationIndex = 0
        self.imgPair = imgPair
    
    def update(self):
        super().update()
        self.rect.x = self.pos.x
        xColl = self.collide_with_obstacles('x')
        self.rect.x = self.pos.y
        yColl = self.collide_with_obstacles('y')
        
        if (not yColl) and self.vel.y > GRAVITY: 
            if xColl: self.rect.bottom = xColl[0].top
            if self.vel.x != 0: self.vel.x *= -1
        if self.vel.x > 0: 
            self.orientation = 1
            self.image = self.imgPair[0]
        if self.vel.x < 0: 
            self.orientation = -1
            self.image = self.imgPair[1]

        if self.lives <= 0: self.kill()
        self.image.set_colorkey(YELLOW)
        self.fireBullet()
        self.image.set_alpha(255)

    def fireBullet(self):
        if (self.rect.bottom <= self.game.avatar.rect.bottom + TILESIZE and self.rect.top + TILESIZE * 5 >= self.game.avatar.rect.top) and not self.game.avatar.stealth: 
            now = pg.time.get_ticks()
            if now - self.last_shot > self.bulletDelay:
                self.last_shot = now
                Bullet(self.game, vec(self.rect.centerx, self.rect.centery - 16), vec(self.orientation * BULLET_SPEED, 0), source=self.source)

    def collide_with_obstacles(self, direction):
        obstacleHits = pg.sprite.spritecollide(self, self.game.obstacles, False)
        if obstacleHits:
            if direction == 'x':
                if self.vel.x > 0:
                    self.pos.x = (obstacleHits[0].rect.left - self.rect.width)
                if self.vel.x < 0:
                    self.pos.x = obstacleHits[0].rect.right
                self.vel.x *= -1
                self.rect.x = self.pos.x
            if direction == 'y':
                if self.vel.y > 0:
                    self.pos.y = obstacleHits[0].rect.top# - 1
                    if self.game.currentStageType == 1 and self.vel.y > 20:
                        self.kill()
                if self.vel.y < 0:
                    self.pos.y = obstacleHits[0].rect.bottom + self.rect.height + 1
                self.vel.y = 0
                self.rect.bottom = self.pos.y
class BigBadd(Baddie):
    def __init__(self, game, x, y, orientation):
        self.groups = game.all_sprites, game.kinetics, game.baddies, game.bigBadds
        super().__init__(game, self.groups, x, y, orientation, 2, BIG_BADD_SPEED, BIG_BADD_BULLET_DELAY, (game.bigBaddRight0Img, game.bigBaddLeft0Img), "bigBadd")

    def update(self):
        super().update()
        if self.vel.y == 0 and self.vel.x == 0: self.vel.x = random.choice([BIG_BADD_SPEED, -BIG_BADD_SPEED])
        if self.game.camera.apply(self.rect, isRect=True).right < 0 or self.game.camera.apply(self.rect, isRect=True).left > WIDTH:
            if self.game.avatar.rect.bottom <= self.rect.bottom and self.rect.top - TILESIZE * 3 <= self.game.avatar.rect.top:
                if self.game.avatar.rect.right < self.rect.left: 
                    self.vel.x = -BIG_BADD_SPEED
                if self.game.avatar.rect.left < self.rect.right: 
                    self.vel.x = BIG_BADD_SPEED
class SniperBadd(Baddie):
    def __init__(self, game, x,y, orientation):
        self.groups = game.all_sprites, game.kinetics, game.baddies, game.sniperBadds
        super().__init__(game, self.groups, x, y, orientation, 1, 0, SNIPER_BADD_BULLET_DELAY, (game.sniperBaddRight0Img, game.sniperBaddLeft0Img), "sniperBadd")

    def update(self):
        super().update()

    def fireBullet(self):
        if (self.rect.bottom <= self.game.avatar.rect.bottom + TILESIZE and self.rect.top + TILESIZE * 5 >= self.game.avatar.rect.top) and not self.game.avatar.stealth: 
            now = pg.time.get_ticks()
            if now - self.last_shot > SNIPER_BADD_BULLET_DELAY:
                self.last_shot = now
                bullet = Bullet(self.game, vec(self.rect.centerx, self.rect.centery - 16), vec(self.orientation * BULLET_SPEED / 2, -BULLET_SPEED / 2), source="sniperBadd")
                if bullet.vel.x < 0: bullet.image = pg.transform.rotate(bullet.image, -45)
                if bullet.vel.x > 0: bullet.image = pg.transform.rotate(bullet.image, 45)
class Projectile(Kinetic):
    pass
class Bullet(pg.sprite.Sprite):
    def __init__(self, game, pos, direction, source):
        self.groups = game.all_sprites, game.bullets, game.kinetics
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = game.bulletImg
        self.image.set_colorkey(YELLOW)
        self.rect = self.image.get_rect()
        self.pos = vec(pos.x, pos.y)
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y
        self.vel = direction * BULLET_SPEED
        self.spawn_time = pg.time.get_ticks()
        if direction.x < 0: self.image = pg.transform.flip(self.image, True, False)
        self.source = source

    def update(self):
        self.rect.topleft += self.vel * self.game.dt
        if self.game.camera.apply(self.rect, isRect=True).right < 0 or self.game.camera.apply(self.rect, isRect=True).left > WIDTH: 
            self.kill()
class Grapplehook(pg.sprite.Sprite):
    def __init__(self, game, pos):
        self.groups = game.all_sprites, game.grapplehook, game.kinetics
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.grapplehookImg
        self.image.set_colorkey(YELLOW)
        self.rect = self.image.get_rect()
        self.pos = vec(pos.x, pos.y)
        self.rect.topleft = self.pos
        self.vel = vec(0, GRAPPLEHOOK_SPEED)

    def update(self):
        self.rect.topleft -= self.vel
        self.game.grappleLine = True
        if self.rect.bottom < 0:
            self.kill()