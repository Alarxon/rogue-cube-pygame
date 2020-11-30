import pygame
import pygame_menu
import gameplay
import os
import shelve
from pygame_menu import sound

#Init pygame mixer
if pygame.get_sdl_version()[0] == 2:
        pygame.mixer.pre_init(44100, 32, 2, 1024)
#"About menu" information
ABOUT = ['Author: {0}'.format("Sergio Alarcon Rodriguez"),
         '',
         'Github: {0}'.format("alarxon"),
         '',
         'Version: {0}'.format("Alpha 1.0")]
#Initialize pygame        
pygame.init()

#Get main dir to load dependencies (music, sounds, etc)
main_dir = os.path.split(os.path.abspath(__file__))[0]

#Check if pygame mixer is Initialize, if not the mixer wont be use
if pygame.mixer and not pygame.mixer.get_init():
        print("Warning, no sound")
        pygame.mixer = None
#If the mixer is Initialize load the music
if pygame.mixer:
        music = os.path.join(main_dir, "data", "song.wav")
        pygame.mixer.music.load(music)
        pygame.mixer.music.play(-1)

#Create main surface (display)
SCREEN_SIZE = pygame.Rect((0, 0, 800, 640))
surface = pygame.display.set_mode(SCREEN_SIZE.size)
pygame.display.set_caption("Rogue Cube")

#Get monitor size to use fullscreen
monitor_size = [pygame.display.Info().current_w, pygame.display.Info().current_h]

#Global variables (screenmode, SFX mode and default player color)
fullscreen = False
SFX = True
chose_color = "#0000FF"

#Menu to show when the player lose or quit
def game_over(name):
    global surface
    #shelve is use to store scores.
    dictionary = shelve.open('score.txt')
    if str(name) in dictionary:
        if int(dictionary[name]) < gameplay.SCORE:
            dictionary[name] = gameplay.SCORE
    else:
        dictionary[name] = gameplay.SCORE           
    dictionary.close()

    #Remade the score menu to update scores
    global score_menu
    score_menu.clear()
    msg_list = high_scores()
    for msg in msg_list:
        score_menu.add_label(msg, margin=(0, 0))
        score_menu.add_label("", margin=(0, 0))
    score_menu.add_button('Return', pygame_menu.events.BACK)
    sfx = os.path.join(main_dir, "data", "menu.wav")
    engine = sound.Sound()
    engine.set_sound(sound.SOUND_TYPE_CLICK_MOUSE, sfx)
    engine.set_sound(sound.SOUND_TYPE_KEY_ADDITION, sfx)

    #Made and show game over menu
    menu = pygame_menu.Menu(surface.get_height(), surface.get_width(), 'Score',theme=sub_theme,onclose=pygame_menu.events.RESET)
    if SFX:
        menu.set_sound(engine, recursive=True)
    else:
        menu.set_sound(None, recursive=True)
    menu.add_label("SCORE: " + str(gameplay.SCORE), align=pygame_menu.locals.ALIGN_CENTER)
    menu.add_label(" ", align=pygame_menu.locals.ALIGN_CENTER)
    menu.add_button('Return', pygame_menu.events.CLOSE)
    menu.mainloop(surface)    

#Start the game
def start_the_game():
    global surface
    global name
    global total_levels
    global SFX
    global chose_color
    #Get number levels
    try:
        number_levels = int(total_levels.get_value().replace(" ",""))
    except:
        number_levels = 3
    #Initial information
    level = 1
    life = 50
    gameplay.SCORE = 0
    #Play number of levels the player choose
    while level <= number_levels:
        #Call the main function to initialize the game
        gameplay.main(surface, life, SFX, chose_color)
        #After each level the player and enemies have more life
        level = level + 1
        life = life + 5
        #If the player dies of quit break the loop
        if gameplay.DEATH_STATUS and gameplay.NEXT_LEVEL == False:
            game_over(name.get_value().replace(" ",""))
            break
#Get high scores from shelve score.txt
def high_scores():
    dictionary = shelve.open('score.txt')
    dictionary_copy = sorted(dictionary.items(), key=lambda x: x[1], reverse=True)
    msg_list = []
    if len(dictionary) > 0:
        for score in dictionary_copy:
            msg = score[0] + ": " + str(score[1])
            msg_list.append(msg)
    else:
        msg = "There is no scores yet!"
        msg_list.append(msg)
    dictionary.close()
    return msg_list

#Set the music on and off
def set_music(value, mode):
    if mode == 2:
        pygame.mixer.music.stop()
    elif mode == 1:
        pygame.mixer.music.play(-1)

#Set sfx on and off
def set_sfx(value, mode):
    global SFX
    global menu
    global engine

    if mode == 2:
        menu.set_sound(None, recursive=True)
        SFX = False
    elif mode == 1:
        menu.set_sound(engine, recursive=True)
        SFX = True

#Get hex color the player choose
def print_color(color):
    global chose_color
    chose_color = '#%02x%02x%02x' % color
    if chose_color == "#-1-1-1":
        chose_color = "#0000FF"

#Set screen resolution to fullscreen or window screen
def set_screen_resolution():
    global fullscreen
    global menu
    global surface
    global name
    global total_levels
    fullscreen = not fullscreen
    #Remade main menu to fullscreen
    if fullscreen:
        menu.disable()
        pygame.display.quit()
        pygame.display.init()

        surface = pygame.display.set_mode(monitor_size, pygame.FULLSCREEN)
        
        menu = pygame_menu.Menu(monitor_size[1], monitor_size[0], 'Rogue Cube',theme=sub_theme)
        menu.set_sound(engine, recursive=True)
        name = menu.add_text_input('Name : ', default='Cube')
        total_levels = menu.add_text_input('Total Levels : ', default=3)
        menu.add_button('Play', start_the_game)
        menu.add_label("", margin=(0, 0))
        menu.add_button('How to play', how_to_menu)
        menu.add_button('Select Player Color', menu_color)
        menu.add_label("", margin=(0, 0))
        menu.add_button('Fullscreen', set_screen_resolution)
        menu.add_selector('Music :', [('On', 1), ('Off', 2)], onchange=set_music)
        menu.add_selector('Game SFX :', [('On', 1), ('Off', 2)], onchange=set_sfx)
        menu.add_label("", margin=(0, 0))
        menu.add_button("High Scores", score_menu)
        menu.add_button("About", about_menu)
        menu.add_button('Quit', pygame_menu.events.EXIT)
        menu.enable()
    #Remade main menu to window screen
    else:
        menu.disable()
        pygame.display.quit()
        pygame.display.init()

        surface = pygame.display.set_mode(SCREEN_SIZE.size)
        
        menu = pygame_menu.Menu(640, 800, 'Rogue Cube',theme=sub_theme)
        menu.set_sound(engine, recursive=True)
        name = menu.add_text_input('Name : ', default='Cube')
        total_levels = menu.add_text_input('Total Levels : ', default=3)
        menu.add_button('Play', start_the_game)
        menu.add_label("", margin=(0, 0))
        menu.add_button('How to play', how_to_menu)
        menu.add_button('Select Player Color', menu_color)
        menu.add_label("", margin=(0, 0))
        menu.add_button('Fullscreen', set_screen_resolution)
        menu.add_selector('Music :', [('On', 1), ('Off', 2)], onchange=set_music)
        menu.add_selector('Game SFX :', [('On', 1), ('Off', 2)], onchange=set_sfx)
        menu.add_label("", margin=(0, 0))
        menu.add_button("High Scores", score_menu)
        menu.add_button("About", about_menu)
        menu.add_button('Quit', pygame_menu.events.EXIT)
        menu.enable()

#Set sfx sound for the menus
sfx = os.path.join(main_dir, "data", "menu.wav")
engine = sound.Sound()
engine.set_sound(sound.SOUND_TYPE_CLICK_MOUSE, sfx)
engine.set_sound(sound.SOUND_TYPE_KEY_ADDITION, sfx)

#Create theme for the menus
sub_theme = pygame_menu.themes.THEME_DARK.copy()
sub_theme.widget_font = pygame_menu.font.FONT_NEVIS
sub_theme.title_font = pygame_menu.font.FONT_8BIT
sub_theme.title_offset = (5, -2)
sub_theme.widget_offset = (0, 0.14)

#Create about menu
about_menu = pygame_menu.Menu(640, 800,mouse_visible=False,onclose=pygame_menu.events.DISABLE_CLOSE,  theme=sub_theme, title='About')
for m in ABOUT:
    about_menu.add_label(m, margin=(0, 0))
about_menu.add_label('')
about_menu.add_button('Return to Menu', pygame_menu.events.BACK)

#Create main menu and set sfx
menu = pygame_menu.Menu(640, 800, 'Rogue Cube',theme=sub_theme)
menu.set_sound(engine, recursive=True)

#Load assets to use in the how to play menu
text_player = os.path.join(main_dir, "data", "text0.png")
image_player = os.path.join(main_dir, "data", "obj0.png")
text_enemy = os.path.join(main_dir, "data", "text1.png")
image_enemy = os.path.join(main_dir, "data", "obj1.png")
text_door = os.path.join(main_dir, "data", "text3.png")
image_door = os.path.join(main_dir, "data", "obj3.png")

#Create how to play menu
how_to_menu = pygame_menu.Menu(640, 800, 'How to play',theme=sub_theme)
how_to_menu.add_label("Every level is random", margin=(0, 0))
how_to_menu.add_label("Is impossible to have exactly the same level twice", margin=(0, 0))
how_to_menu.add_label("", margin=(0, 0))

how_to_menu.add_label("In the main menu you can choose the number of", margin=(0, 0))
how_to_menu.add_label("levels you want to play", margin=(0, 0))
how_to_menu.add_label("", margin=(0, 0))

how_to_menu.add_label("The player:", margin=(0, 0))
how_to_menu.add_image(text_player)
how_to_menu.add_image(image_player)
how_to_menu.add_label("Move: using the arrow keys", margin=(0, 0))
how_to_menu.add_label("Shot: using W A S D", margin=(0, 0))
how_to_menu.add_label("Pause: using ESC", margin=(0, 0))
how_to_menu.add_label("", margin=(0, 0))

how_to_menu.add_label("The enemy:", margin=(0, 0))
how_to_menu.add_image(text_enemy)
how_to_menu.add_image(image_enemy)
how_to_menu.add_label("You have to shoot the enemy to kill it", margin=(0, 0))
how_to_menu.add_label("Enemies can be of different colors", margin=(0, 0))
how_to_menu.add_label("", margin=(0, 0))

how_to_menu.add_label("The door:", margin=(0, 0))
how_to_menu.add_image(text_door)
how_to_menu.add_image(image_door)
how_to_menu.add_label("You have to kill all enemies to pass through the door", margin=(0, 0))
how_to_menu.add_label("The door changes color every 3 seconds", margin=(0, 0))
how_to_menu.add_label("", margin=(0, 0))

how_to_menu.add_button('Return', pygame_menu.events.BACK)

#Create hgih score menu
score_menu = pygame_menu.Menu(640, 800, "High Scores",theme=sub_theme)
msg_list = high_scores()
for msg in msg_list:
    score_menu.add_label(msg, margin=(0, 0))
    score_menu.add_label("", margin=(0, 0))
score_menu.add_button('Return', pygame_menu.events.BACK)

#Create menu to choose your player color
menu_color = pygame_menu.Menu(640, 800,mouse_visible=False,onclose=pygame_menu.events.DISABLE_CLOSE,  theme=sub_theme, title='Chose color')
menu_color.add_color_input('Color in Hex (press Enter): ', color_type='hex', onreturn=print_color, default="#0000FF")
menu_color.add_vertical_margin(25)
menu_color.add_button('Return', pygame_menu.events.BACK, align=pygame_menu.locals.ALIGN_CENTER) 

#Add all the menus to the main menu
name = menu.add_text_input('Name : ', default='Cube')
total_levels = menu.add_text_input('Total Levels : ', default=3)
menu.add_button('Play', start_the_game)
menu.add_label("", margin=(0, 0))
menu.add_button('How to play', how_to_menu)
menu.add_button('Select Player Color', menu_color)
menu.add_label("", margin=(0, 0))
menu.add_button('Fullscreen', set_screen_resolution)
menu.add_selector('Music :', [('On', 1), ('Off', 2)], onchange=set_music)
menu.add_selector('Game SFX :', [('On', 1), ('Off', 2)], onchange=set_sfx)
menu.add_label("", margin=(0, 0))
menu.add_button("High Scores", score_menu)
menu.add_button("About", about_menu)
menu.add_button('Quit', pygame_menu.events.EXIT)

#Make the main menu to handle pygame events and draw the menu
while 1:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            exit()

    if menu.is_enabled():
        menu.update(events)
        menu.draw(surface)

    pygame.display.update()
