import pygame
import generator
import random
import pygame_menu
import os
from pygame_menu import sound
from datetime import datetime
from datetime import timedelta
from pygame import *

#Initialize pygame mixer
if pygame.get_sdl_version()[0] == 2:
        pygame.mixer.pre_init(44100, 32, 2, 1024)
pygame.mixer.init()

#Main dir to load assets
main_dir = os.path.split(os.path.abspath(__file__))[0]

#Screen size
SCREEN_SIZE = pygame.Rect((0, 0, 800, 640))

#Global variables
TILE_SIZE = 32 
MAX_SHOTS = 3
shots = []
NUMBER_ENEMIES = 0
DEATH_STATUS = False
NEXT_LEVEL = False
GENERAL_LIFE = 0
SCORE = 0
PAUSE = False
SFX = True
CHOSE_COLOR = "#0000FF"

#Load sounds
def load_sound(file):
    if not pygame.mixer:
        return None
    file = os.path.join(main_dir, "data", file)
    try:
        sound = pygame.mixer.Sound(file)
        return sound
    except pygame.error:
        print("Warning, unable to load, %s" % file)

    return None

#Load sfx sounds
destroy_sound = load_sound("destroy.wav")
hit_sound = load_sound("hit.wav")
shot_sound = load_sound("shot.wav")
next_sound = load_sound("next.wav")

#Create camara which always follow the player
class CameraAwareLayeredUpdates(pygame.sprite.LayeredUpdates):
    def __init__(self, target, world_size):
        super().__init__()
        self.target = target
        self.cam = pygame.Vector2(0, 0)
        self.world_size = world_size
        if self.target:
            self.add(target)

    def update(self, *args):
        super().update(*args)
        if self.target:
            x = -self.target.rect.center[0] + SCREEN_SIZE.width/2
            y = -self.target.rect.center[1] + SCREEN_SIZE.height/2
            self.cam += (pygame.Vector2((x, y)) - self.cam) * 0.05
            self.cam.x = max(-(self.world_size.width-SCREEN_SIZE.width), min(0, self.cam.x))
            self.cam.y = max(-(self.world_size.height-SCREEN_SIZE.height), min(0, self.cam.y))

    def draw(self, surface):
        spritedict = self.spritedict
        surface_blit = surface.blit
        dirty = self.lostsprites
        self.lostsprites = []
        dirty_append = dirty.append
        init_rect = self._init_rect
        for spr in self.sprites():
            rec = spritedict[spr]
            newrect = surface_blit(spr.image, spr.rect.move(self.cam))
            if rec is init_rect:
                dirty_append(newrect)
            else:
                if newrect.colliderect(rec):
                    dirty_append(newrect.union(rec))
                else:
                    dirty_append(newrect)
                    dirty_append(rec)
            spritedict[spr] = newrect
        return dirty            

#Main function, it receives the screen mode, general life's, sfx mode and the color choose by the player
def main(screen_mode, general_life, sfx, chose_color):
    #Initialize global variables
    global shots
    shots = []
    global NUMBER_ENEMIES
    NUMBER_ENEMIES = 0
    global DEATH_STATUS
    DEATH_STATUS = False 
    global GENERAL_LIFE
    GENERAL_LIFE = general_life
    global PAUSE
    PAUSE = False       
    global NEXT_LEVEL
    NEXT_LEVEL = False
    global SFX
    SFX = sfx
    global CHOSE_COLOR
    CHOSE_COLOR = chose_color

    #Get random seed using the date
    random.seed(datetime.now())

    #Initialize pygame
    pygame.init()

    #Initialize surface with the screen mode choose by the user
    screen = screen_mode
    pygame.display.set_caption("Rogue Cube")

    #Timer to set FPS
    timer = pygame.time.Clock()

    #Generate level
    gen = generator.Generator()
    gen.gen_level()

    #Get level in characters
    level = gen.gen_tiles_level()

    #Get rooms and corridors with their size and initial point
    rooms = gen.get_room_list()
    corridors = gen.get_corridor_list()

    #Initial player position
    initial_position = (rooms[0][0]*TILE_SIZE, rooms[0][1]*TILE_SIZE)

    #create sprite groups fro the plataforms, bullets and eenemies
    platforms = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    #Create player object
    player = Player(platforms, initial_position,enemies)

    #Get level width and height
    level_width  = len(level[0])*TILE_SIZE
    level_height = len(level)*TILE_SIZE

    #All the objects  in the game are entities (an object from the class Camera) with the player as his focus
    entities = CameraAwareLayeredUpdates(player, pygame.Rect(0, 0, level_width, level_height))
    
    #Create player's life text
    Life(player,"player", entities)

    #Build the level layout
    x = y = 0
    for row in level:
        for col in row:
            if col == "P":
                Platform((x, y), platforms, entities)
            if col == "B":
                Stone((x, y), platforms, entities)
            x += TILE_SIZE
        y += TILE_SIZE
        x = 0

    #Create and place the enemies with his life text
    for room in rooms[1:-1]:
        x = room[0]*TILE_SIZE + (room[2]*TILE_SIZE)//2
        y = room[1]*TILE_SIZE + (room[3]*TILE_SIZE)//2
        enemy_type = random.randrange(0, 7)
        colors = ["#ff0000","#ffa500","#ffff00","#008000","#0000ff", "#4b0082","#ee82ee"]
        enemy = Enemy((x,y), bullets, platforms, colors, enemy_type, enemies, entities)
        Life(enemy,"enemy", entities)
        NUMBER_ENEMIES = NUMBER_ENEMIES + 1
    
    #Create and place the exit door
    room = rooms[-1]
    x = room[0]*TILE_SIZE + (room[2]*TILE_SIZE)//2
    y = room[1]*TILE_SIZE + (room[3]*TILE_SIZE)//2
    exit = ExitBlock((x, y), platforms, entities)
    Life(exit,"exit", entities)

    #Main loop how update the sprites
    while 1:
        #Get pygames events
        for e in pygame.event.get():
            #If the player quits stop the loop and return to main
            if e.type == QUIT:
                DEATH_STATUS = True 
                return
            #IF the player use ESC pause the game and show pause menu
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                def exit():
                    pygame.event.post(pygame.event.Event(QUIT))
                sub_theme = pygame_menu.themes.THEME_DARK.copy()
                sub_theme.widget_font = pygame_menu.font.FONT_NEVIS
                sub_theme.title_font = pygame_menu.font.FONT_8BIT
                sub_theme.title_offset = (5, -2)
                sub_theme.widget_offset = (0, 0.14)

                sfx = os.path.join(main_dir, "data", "menu.wav")

                engine = sound.Sound()
                engine.set_sound(sound.SOUND_TYPE_CLICK_MOUSE, sfx)
                engine.set_sound(sound.SOUND_TYPE_KEY_ADDITION, sfx)

                menu = pygame_menu.Menu(screen.get_height(), screen.get_width(), 'Pause',theme=sub_theme,onclose=pygame_menu.events.RESET)
                
                if SFX:
                    menu.set_sound(engine, recursive=True)
                else:
                    menu.set_sound(None, recursive=True)
                menu.add_button('Return', pygame_menu.events.CLOSE)
                menu.add_button('Quit', exit)

                PAUSE = True
                while 1:
                    events = pygame.event.get()
                    for event in events:
                        if event.type == pygame.QUIT:
                            DEATH_STATUS = True
                            return
                    
                    if menu.is_enabled():
                        try:
                            menu.update(events)
                            menu.draw(screen)
                        except Exception as ex:
                            PAUSE = False
                            break
                  
                    pygame.display.update()
            #If the W key was pressed shot a new bullet to the top
            if e.type == KEYDOWN and e.key == ord('w'):
                if(len(shots) <= MAX_SHOTS):
                    if pygame.mixer and destroy_sound != None and SFX:
                        shot_sound.play()
                    Shot((player.getX(), player.getY()), platforms, "up", CHOSE_COLOR , bullets, entities)
                    shots.append(1)
            #If the A key was pressed shot a new bullet to the left
            if e.type == KEYDOWN and e.key == ord('a'):
                if(len(shots) <= MAX_SHOTS):
                    if pygame.mixer and destroy_sound != None and SFX:
                        shot_sound.play()
                    Shot((player.getX(), player.getY()), platforms, "left", CHOSE_COLOR, bullets, entities)
                    shots.append(1)
            #If the S key was pressed shot a new bullet to the bottom
            if e.type == KEYDOWN and e.key == ord('s'):
                if(len(shots) <= MAX_SHOTS):
                    if pygame.mixer and destroy_sound != None and SFX:
                        shot_sound.play()
                    Shot((player.getX(), player.getY()), platforms, "down", CHOSE_COLOR, bullets, entities)
                    shots.append(1)
            #If the D key was pressed shot a new bullet to the right
            if e.type == KEYDOWN and e.key == ord('d'):
                if(len(shots) <= MAX_SHOTS):
                    if pygame.mixer and destroy_sound != None and SFX:
                        shot_sound.play()
                    Shot((player.getX(), player.getY()), platforms, "right", CHOSE_COLOR, bullets, entities)
                    shots.append(1)
        #Update all entites each frame
        entities.update()

        #Background color
        screen.fill((46,139,87))
        #DDraw entities upon the background
        entities.draw(screen)
        #Update the display
        pygame.display.update()
        #Set frames 60 FPS
        timer.tick(60)

#Class entity how models the enemies and player sprites
#It receives the color, initial position and sprite groups
class Entity(pygame.sprite.Sprite):
    def __init__(self, color, pos, *groups):
        super().__init__(*groups)
        self.image = Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=pos)

#Class player
#It receives the platforms and enemies for collisions, initial position, and the player sprite  groups
class Player(Entity):
    def __init__(self, platforms, pos, enemies, *groups):
        global CHOSE_COLOR
        super().__init__(Color(CHOSE_COLOR), pos)
        global GENERAL_LIFE

        self.vel = pygame.Vector2((0, 0))
        self.platforms = platforms
        self.enemies = enemies
        self.speed = 8
        self.life = GENERAL_LIFE
        self.pos = pos

#Update is call every frame
    def update(self):
        #Get pygame events
        pressed = pygame.key.get_pressed()
        up = pressed[K_UP]
        down = pressed[K_DOWN]
        left = pressed[K_LEFT]
        right = pressed[K_RIGHT]
        running = pressed[K_SPACE]
        #Check what arrow key was pressed and the player moves in that direction
        if up:
            self.vel.y = -self.speed
        if down:
            self.vel.y = self.speed
        if left:
            self.vel.x = -self.speed
        if right:
            self.vel.x = self.speed
        if running:
            self.vel.x *= 1.5

        if not(left or right):
            self.vel.x = 0
        if not(up or down):
            self.vel.y = 0
        #increment in x direction
        self.rect.left += self.vel.x
        #check x collisions for plataforms and enemies
        self.collide(self.vel.x, 0, self.platforms)
        self.collide_enemies(self.vel.x, 0, self.enemies)
        #increment in y direction
        self.rect.top += self.vel.y
        #check y collisions for plataforms and enemies
        self.collide(0, self.vel.y, self.platforms)
        self.collide_enemies(0, self.vel.y, self.enemies)

    #Check collisions with plataforms
    def collide(self, xvel, yvel, platforms):
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                #If the player collides with the exit block and all the enemies are dead pass to the next level
                if isinstance(p, ExitBlock):
                    global NEXT_LEVEL
                    if NUMBER_ENEMIES == 0:
                        NEXT_LEVEL = True
                        if pygame.mixer and destroy_sound != None and SFX:
                            next_sound.play()
                        pygame.event.post(pygame.event.Event(QUIT))
                #Change direction of the player when colide with a plataform
                if xvel > 0:
                    self.rect.right = p.rect.left
                if xvel < 0:
                    self.rect.left = p.rect.right
                if yvel > 0:
                    self.rect.bottom = p.rect.top
                    self.yvel = 0
                if yvel < 0:
                    self.rect.top = p.rect.bottom

    #Check collisions with enemies (bullet and enemie sprite)
    def collide_enemies(self, xvel, yvel, enemies):
        for p in enemies:
            if pygame.sprite.collide_rect(self, p):
                #If player's life is 0 then kill the sprite and return to main
                if self.life == 0:
                    if pygame.mixer and destroy_sound != None and SFX:
                        destroy_sound.play()

                    global DEATH_STATUS
                    DEATH_STATUS = True
                    global NEXT_LEVEL
                    NEXT_LEVEL = False
                    self.kill()
                    pygame.event.post(pygame.event.Event(QUIT))
                #Change player's life minus 1
                else:
                    if pygame.mixer and destroy_sound != None and SFX:
                        hit_sound.play()
                    self.life = self.life - 1
    #Get X position
    def getX(self):
        return self.rect.left

    #Get Y position
    def getY(self):
        return self.rect.top

#Class how models the bullets
#It receives the platforms for collisions, initial position, direction, color and the bullet sprite groups
class Shot(pygame.sprite.Sprite):
    def __init__(self, pos, platforms, direc, color, *groups):
        super().__init__(*groups)
        self.image = Surface((TILE_SIZE//2, TILE_SIZE//2))
        self.image.fill(Color(color))
        self.rect = self.image.get_rect(topleft=pos)
        self.direct = direc

        self.vel = pygame.Vector2((0, 0))
        self.platforms = platforms
        self.speed = 8

#Update is call every frame
    def update(self):
        up = self.direct == "up"
        down = self.direct == "down"
        left = self.direct == "left"
        right = self.direct == "right"
        
        #Set the direction of the bullet
        if self.direct == "up":
            self.vel.y = -self.speed
        if self.direct == "down":
            self.vel.y = self.speed
        if self.direct == "left":
            self.vel.x = -self.speed
        if self.direct == "right":
            self.vel.x = self.speed


        if not(left or right):
            self.vel.x = 0
        if not(up or down):
            self.vel.y = 0
        #increment in x direction
        self.rect.left += self.vel.x
        #check x collisions
        self.collide(self.platforms)
        #increment in y direction
        self.rect.top += self.vel.y
        #check y collisions
        self.collide(self.platforms)

#Check collisions with plataforms
    def collide(self, platforms):
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                #To avoid to many shots at once
                if(len(shots) > 0):
                    shots.pop(0)
                #Destroy bullet sprite when collides
                self.kill()
#Enemy class
#It receives the platforms and bullets for collisions, initial position, color, enemy_type and the enemie sprite groups
class Enemy(Entity):
    def __init__(self, pos, bullets, platforms, color, enemy_type, *groups):
        super().__init__(Color(color[enemy_type]), pos, *groups)
        global GENERAL_LIFE
        self.bullets = bullets
        self.life = GENERAL_LIFE
        self.pos = pos

        self.directions = ["up","down","left","right"]

        self.last_bullet_shot_time  = None
        self.cont = 0

        self.color = color
        self.enemy_type = enemy_type

        self.platforms = platforms
        self.groups = groups

#Update is call every frame       
    def update(self):
        global PAUSE
        self.collide(self.bullets)
        #Dont shot on Pause
        if PAUSE == False:
            #Shot every 3 seconds to a random directon
            if self.last_bullet_shot_time is None or datetime.now() - self.last_bullet_shot_time > timedelta(seconds = 3):
                if pygame.mixer and destroy_sound != None and SFX:
                        shot_sound.play()
                Shot((self.pos[0],self.pos[1]), self.platforms, self.directions[self.cont], self.color[self.enemy_type], *self.groups)
                self.cont = random.randrange(0, 4)
                self.last_bullet_shot_time = datetime.now()

    #Check collitions with player's bullets
    def collide(self, bullets):
        for p in bullets:
            if pygame.sprite.collide_rect(self, p):
                #If the enemie's life is 0 then destroy the sprite
                if self.life == 0:
                    if pygame.mixer and destroy_sound != None and SFX:
                        destroy_sound.play()

                    self.life = self.life - 1
                    global NUMBER_ENEMIES
                    global SCORE
                    NUMBER_ENEMIES = NUMBER_ENEMIES - 1
                    SCORE = SCORE + 10
                    self.kill()
                #Change enemies's life minus 1
                else:
                    if pygame.mixer and destroy_sound != None and SFX:
                        hit_sound.play()
                    self.life = self.life - 1

#Class to show the objects life and information
#It receives object, obj_type, and the life sprite groups
class Life(pygame.sprite.Sprite):
    def __init__(self, obj, obj_type, *groups):
        super().__init__(*groups)
        self.font = font.Font(None, 20)
        self.font.set_bold(1)
        self.color = Color("white")
        self.laslife = -1
        self.obj = obj
        self.obj_type = obj_type
        self.update()
        self.rect = self.image.get_rect().move(obj.pos[0], obj.pos[1])

#Update is call every frame       
    def update(self):
        #If the object is the exit block show enemies left
        if self.obj_type == "exit":
            global NUMBER_ENEMIES
            msg = "Enemies left: %d" % NUMBER_ENEMIES
            self.image = self.font.render(msg, 0, self.color)
        #If else the object life is less than 0 destroy the life sprite
        elif self.obj.life < 0:
            self.kill()
        #If the object is an enemy then show enemie's life
        elif self.obj.life != self.laslife and self.obj_type == "enemy":
            self.laslife = self.obj.life
            msg = "Life: %d" % self.obj.life
            self.image = self.font.render(msg, 0, self.color)
        #if the object is the player show player's life and score
        elif self.obj_type == "player":
            global SCORE
            self.laslife = self.obj.life
            msg = "Life: %d" % self.obj.life
            msg = msg + " " + "SCORE: %d" % SCORE
            self.image = self.font.render(msg, 0, self.color)
            self.rect = self.image.get_rect().move(self.obj.rect.left, self.obj.rect.top)
        
#Class how call Entity and models the plataforms       
class Platform(Entity):
    def __init__(self, pos, *groups):
        super().__init__(Color("#20B2AA"), pos, *groups)

#Class how call Entity and models the stones     
class Stone(Entity):
    def __init__(self, pos, *groups):
        super().__init__(Color("#000000"), pos, *groups)

#Class how call Entity and models the exit block     
class ExitBlock(Entity):
    def __init__(self, pos, *groups):
        super().__init__(Color("#0033FF"), pos, *groups)
        self.pos = pos
        self.colors_flash  = None

#Update is call every frame           
    def update(self):
        #Change exit block's color every 3 seconds
        if self.colors_flash is None or datetime.now() - self.colors_flash > timedelta(seconds = 3):
            r = lambda: random.randint(0,255)
            color = '#%02X%02X%02X' % (r(),r(),r())
            self.image.fill(color)
            self.colors_flash = datetime.now()

if __name__ == "__main__":
    surface_test = pygame.display.set_mode(SCREEN_SIZE.size)
    main(surface_test,50, True)
