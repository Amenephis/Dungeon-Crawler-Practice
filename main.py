import pygame
from pygame import mixer
from random import randint as rng
import csv
import asyncio
import constants
from weapon import Weapon
from items import Item
from world import World
from button import Button

pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.init()

screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
pygame.display.set_caption("Dungeon Crawler")

#create clock for maintaining frame rate
clock = pygame.time.Clock()

#define game variables
level = 1
start_game = False
pause_game = False
inventory_screen = False
start_intro = False
screen_scroll = [0, 0]
p_d = True

#define player movement variables
moving_left = False
moving_right = False
moving_up = False
moving_down = False

#define font
font = pygame.font.Font("assets/fonts/AtariClassic.ttf", 20)

#helper function to scale image
def scale_img(image, scale):
  w = image.get_width()
  h = image.get_height()
  return pygame.transform.scale(image, (w * scale, h * scale))

#load music and sounds
pygame.mixer.music.load("assets/audio/music.wav")
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)
shot_fx = pygame.mixer.Sound("assets/audio/arrow_shot.wav")
shot_fx.set_volume(0.5)
hit_fx = pygame.mixer.Sound("assets/audio/arrow_hit.wav")
hit_fx.set_volume(0.5)
coin_fx = pygame.mixer.Sound("assets/audio/coin.wav")
coin_fx.set_volume(0.5)
heal_fx = pygame.mixer.Sound("assets/audio/heal.wav")
heal_fx.set_volume(0.5)
death_fx = pygame.mixer.Sound("assets/audio/scream1.wav")
death_fx.set_volume(0.5)
player_hurt_fx = pygame.mixer.Sound("assets/audio/hurt.wav")
player_hurt_fx.set_volume(0.3)
player_death_fx = pygame.mixer.Sound("assets/audio/player_death.wav")
player_death_fx.set_volume(0.3)

#load button images
start_img = scale_img(pygame.image.load("assets/images/buttons/button_start.png").convert_alpha(), constants.BUTTON_SCALE)
exit_img = scale_img(pygame.image.load("assets/images/buttons/button_exit.png").convert_alpha(), constants.BUTTON_SCALE)
restart_img = scale_img(pygame.image.load("assets/images/buttons/button_restart.png").convert_alpha(), constants.BUTTON_SCALE)
resume_img = scale_img(pygame.image.load("assets/images/buttons/button_resume.png").convert_alpha(), constants.BUTTON_SCALE)
inventory_resume_button = scale_img(pygame.image.load("assets/images/buttons/button_resume.png").convert_alpha(), constants.INVENTORY_BUTTON_SCALE)

#load sub-menu screens
inventory_screen_fill = scale_img(pygame.image.load("assets/images/screens/inventory_screen.png").convert_alpha(), constants.MENU_SCALE)

#load heart images
heart_empty = scale_img(pygame.image.load("assets/images/items/heart_empty.png").convert_alpha(), constants.ITEM_SCALE)
heart_half = scale_img(pygame.image.load("assets/images/items/heart_half.png").convert_alpha(), constants.ITEM_SCALE)
heart_full = scale_img(pygame.image.load("assets/images/items/heart_full.png").convert_alpha(), constants.ITEM_SCALE)

#load coin images
coin_images = []
for x in range(4):
  img = scale_img(pygame.image.load(f"assets/images/items/coin_f{x}.png").convert_alpha(), constants.ITEM_SCALE)
  coin_images.append(img)

#load potion image
red_potion = scale_img(pygame.image.load("assets/images/items/potion_red.png").convert_alpha(), constants.POTION_SCALE)

item_images = []
item_images.append(coin_images)
item_images.append(red_potion)

#load weapon images
bow_image = scale_img(pygame.image.load("assets/images/weapons/bow.png").convert_alpha(), constants.WEAPON_SCALE)
arrow_image = scale_img(pygame.image.load("assets/images/weapons/arrow.png").convert_alpha(), constants.WEAPON_SCALE)
fireball_image = scale_img(pygame.image.load("assets/images/weapons/fireball.png").convert_alpha(), constants.FIREBALL_SCALE)

#load tilemap images
tile_list = []
for x in range(constants.TILE_TYPES):
  tile_image = pygame.image.load(f"assets/images/tiles/{x}.png").convert_alpha()
  tile_image = pygame.transform.scale(tile_image, (constants.TILE_SIZE, constants.TILE_SIZE))
  tile_list.append(tile_image)

#load decals
def splatter_gen():
  splatter_num = rng(1,4)
  splatter_image = scale_img(pygame.image.load(f"assets/images/tiles/blood{splatter_num}.png").convert_alpha(), constants.BLOOD_SCALE)
  return splatter_image

#load character images
mob_animations = []
mob_types = ["elf", "imp", "skeleton", "goblin", "muddy", "tiny_zombie", "big_demon"]

animation_types = ["idle", "run"]
for mob in mob_types:
  #load images
  animation_list = []
  for animation in animation_types:
    #reset temporary list of images
    temp_list = []
    for i in range(4):
      img = pygame.image.load(f"assets/images/characters/{mob}/{animation}/{i}.png").convert_alpha()
      img = scale_img(img, constants.SCALE)
      temp_list.append(img)
    animation_list.append(temp_list)
  mob_animations.append(animation_list)


#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
  img = font.render(text, True, text_col)
  screen.blit(img, (x, y))

#function for displaying game info
def draw_info():
  pygame.draw.rect(screen, constants.PANEL, (0, 0, constants.SCREEN_WIDTH, 50))
  pygame.draw.line(screen, constants.WHITE, (0, 50), (constants.SCREEN_WIDTH, 50))
  #draw lives
  half_heart_drawn = False
  for i in range(5):
    if player.health >= ((i + 1) * 20):
      screen.blit(heart_full, (10 + i * 50, 0))
    elif (player.health % 20 > 0) and half_heart_drawn == False:
      screen.blit(heart_half, (10 + i * 50, 0))
      half_heart_drawn = True
    else:
      screen.blit(heart_empty, (10 + i * 50, 0))

  #level
  draw_text("LEVEL: " + str(level), font, constants.WHITE, constants.SCREEN_WIDTH / 2, 15)
  #show score
  draw_text(f"X{player.score}", font, constants.WHITE, constants.SCREEN_WIDTH - 100, 15)

#function to reset level
def reset_level():
  damage_text_group.empty()
  arrow_group.empty()
  item_group.empty()
  fireball_group.empty()
  splatter_group.empty()

  #create empty tile list
  data = []
  for row in range(constants.ROWS):
    r = [-1] * constants.COLS
    data.append(r)

  return data

#function to resume the game from a menu screen
def resume():
  inventory_screen = False
  pause_game = False
  return inventory_screen, pause_game

#damage text class
class DamageText(pygame.sprite.Sprite):
  def __init__(self, x, y, damage, color):
    pygame.sprite.Sprite.__init__(self)
    self.image = font.render(damage, True, color)
    self.rect = self.image.get_rect()
    self.rect.center = (x, y)
    self.counter = 0

  def update(self):
    #reposition based on screen scroll
    self.rect.x += screen_scroll[0]
    self.rect.y += screen_scroll[1]

    #move damage text up
    self.rect.y -= 1
    #delete the counter after a few seconds
    self.counter += 1
    if self.counter > 30:
      self.kill()

#class for handling screen fade
class ScreenFade():
  def __init__(self, direction, colour, speed):
    self.direction = direction
    self.colour = colour
    self.speed = speed
    self.fade_counter = 0

  def fade(self):
    fade_complete = False
    self.fade_counter += self.speed
    if self.direction == 1:#whole screen fade
      pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT))
      pygame.draw.rect(screen, self.colour, (constants.SCREEN_WIDTH // 2 + self.fade_counter, 0, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
      pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT // 2))
      pygame.draw.rect(screen, self.colour, (0, constants.SCREEN_HEIGHT // 2 + self.fade_counter, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    elif self.direction == 2:#vertical screen fade down
      pygame.draw.rect(screen, self.colour, (0, 0, constants.SCREEN_WIDTH, 0 + self.fade_counter))

    if self.fade_counter >= constants.SCREEN_WIDTH:
      fade_complete = True

    return fade_complete

#blood splatter
class Splatter(pygame.sprite.Sprite):
  def __init__(self, image, x, y):
    pygame.sprite.Sprite.__init__(self)
    self.image = image
    self.rect = self.image.get_rect()
    self.rect.center = (x, y)
    
  def update(self, screen_scroll):
    #reposition based on screen scroll
    self.rect.x += screen_scroll[0]
    self.rect.y += screen_scroll[1]

#create empty tile list
world_data = []
for row in range(constants.ROWS):
  r = [-1] * constants.COLS
  world_data.append(r)
#load in level data and create world
with open(f"levels/level{level}_data.csv", newline="") as csvfile:
  reader = csv.reader(csvfile, delimiter = ",")
  for x, row in enumerate(reader):
    for y, tile in enumerate(row):
      world_data[x][y] = int(tile)

world = World()
world.process_data(world_data, tile_list, item_images, mob_animations)

#create player
player = world.player
#create player's weapon
bow = Weapon(bow_image, arrow_image)

#extract enemies from world data
enemy_list = world.character_list

#create sprite groups
damage_text_group = pygame.sprite.Group()
arrow_group = pygame.sprite.Group()
item_group = pygame.sprite.Group()
fireball_group = pygame.sprite.Group()
splatter_group = pygame.sprite.Group()

score_coin = Item(constants.SCREEN_WIDTH - 115, 23, 0, coin_images, True)
item_group.add(score_coin)
#add the items from the level data
for item in world.item_list:
  item_group.add(item)

#create screen fades
intro_fade = ScreenFade(1, constants.BLACK, 4)
death_fade = ScreenFade(2, constants.PINK, 4)

#create button
start_button = Button(constants.SCREEN_WIDTH // 2 - 145, constants.SCREEN_HEIGHT // 2 - 150, start_img)
exit_button = Button(constants.SCREEN_WIDTH // 2 - 110, constants.SCREEN_HEIGHT // 2 + 50, exit_img)
restart_button = Button(constants.SCREEN_WIDTH // 2 - 175, constants.SCREEN_HEIGHT // 2 - 50, restart_img)
resume_button = Button(constants.SCREEN_WIDTH // 2 - 175, constants.SCREEN_HEIGHT // 2 - 150, resume_img)
inventory_resume_button = Button(constants.SCREEN_WIDTH // 2 + 90, constants.SCREEN_HEIGHT // 2 + 200, inventory_resume_button)

#main game loop
async def main(level, start_game, pause_game, inventory_screen, start_intro, screen_scroll, p_d, player, moving_down, moving_left, moving_right, moving_up, world, enemy_list, item_group, score_coin):
  run = True
  while run:

    #control frame rate
    clock.tick(constants.FPS)

    if start_game == False:
      screen.fill(constants.MENU_BG)
      if start_button.draw(screen):
        start_game = True
        start_intro = True
        inventory_screen, pause_game = resume()
      if exit_button.draw(screen):
        run = False
    else:
      if pause_game == True:
        screen.fill(constants.MENU_BG)
        if resume_button.draw(screen):
          inventory_screen, pause_game = resume()
        if exit_button.draw(screen):
          run = False
      elif inventory_screen == True:
        screen.blit(inventory_screen_fill, (0,0))
        if inventory_resume_button.draw(screen):
          inventory_screen, pause_game = resume()
      else:
        screen.fill(constants.BG)

        if player.alive:
          #calculate player movement
          dx = 0
          dy = 0
          if moving_right == True:
            dx = constants.SPEED
          if moving_left == True:
            dx = -constants.SPEED
          if moving_up == True:
            dy = -constants.SPEED
          if moving_down == True:
            dy = constants.SPEED

          #move player
          screen_scroll, level_complete = player.move(dx, dy, world.obstacle_tiles, world.exit_tile)

          #update all objects
          world.update(screen_scroll)
          for enemy in enemy_list:
            fireball, player_hit_sfx = enemy.ai(player, world.obstacle_tiles, screen_scroll, fireball_image)
            if player_hit_sfx:
              player_hurt_fx.play()
            if fireball:
              fireball_group.add(fireball)
            if enemy.alive:
              enemy.update()
            else:
              splatter_image = splatter_gen()
              splatter = Splatter(splatter_image, enemy.rect.x, enemy.rect.y)
              splatter_group.add(splatter)
              enemy_list, item_group = enemy.enemy_death(enemy_list, item_images, item_group)
              death_fx.play()
          player.update()
          arrow = bow.update(player)
          if arrow:
            arrow_group.add(arrow)
            shot_fx.play()
          for arrow in arrow_group:
            damage, damage_pos = arrow.update(screen_scroll, world.obstacle_tiles, enemy_list)
            if damage:
              damage_text = DamageText(damage_pos.centerx, damage_pos.y, str(damage), constants.RED)
              damage_text_group.add(damage_text)
              hit_fx.play()
          damage_text_group.update()
          fireball_group.update(screen_scroll, player)
          item_group.update(screen_scroll, player, coin_fx, heal_fx)
          splatter_group.update(screen_scroll)

        #draw player on screen
        world.draw(screen)
        splatter_group.draw(screen)
        #create a line of sight from the enemy to the player
        for enemy in enemy_list:
        #check if line of sight passes through an obstacle tile
          clipped_line = ()
          line_of_sight = ((enemy.rect.centerx, enemy.rect.centery), (player.rect.centerx, player.rect.centery))
          for obstacle in world.obstacle_tiles:
            if obstacle[1].clipline(line_of_sight):
              clipped_line = obstacle[1].clipline(line_of_sight)
          if not clipped_line:
            enemy.draw(screen)
            if enemy.boss == 1:
              pygame.draw.rect(screen, "black", (enemy.rect.left, enemy.rect.top, 131, 16))
              pygame.draw.rect(screen, "red", (enemy.rect.left + 3, enemy.rect.top + 3, (enemy.health // 2), 10))
            else:
              pygame.draw.rect(screen, "black", (enemy.rect.left, enemy.rect.top, 56, 16))
              pygame.draw.rect(screen, "red", (enemy.rect.left + 3, enemy.rect.top + 3, (enemy.health // 2), 10))
        player.draw(screen)
        bow.draw(screen)
        for arrow in arrow_group:
          arrow.draw(screen)
        for fireball in fireball_group:
          fireball.draw(screen)
        damage_text_group.draw(screen)
        item_group.draw(screen)
        draw_info()
        score_coin.draw(screen)

        #check level complete
        if level_complete == True:
          start_intro = True
          level += 1
          world_data = reset_level()
          #load in level data and create world
          with open(f"levels/level{level}_data.csv", newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter = ",")
            for x, row in enumerate(reader):
              for y, tile in enumerate(row):
                world_data[x][y] = int(tile)
          world = World()
          world.process_data(world_data, tile_list, item_images, mob_animations)
          temp_hp = player.health
          temp_score = player.score
          player = world.player
          player.health = temp_hp
          player.score = temp_score
          enemy_list = world.character_list
          score_coin = Item(constants.SCREEN_WIDTH - 115, 23, 0, coin_images, True)
          item_group.add(score_coin)
          #add the items from the level data
          for item in world.item_list:
            item_group.add(item)


        #show intro
        if start_intro == True:
          if intro_fade.fade():
            start_intro = False
            intro_fade.fade_counter = 0

        #show death screen
        if player.alive == False:
          while p_d:
            player_death_fx.play()
            p_d = False
          if death_fade.fade():
            if restart_button.draw(screen):
              death_fade.fade_counter = 0
              start_intro = True
              world_data = reset_level()
              #load in level data and create world
              with open(f"levels/level{level}_data.csv", newline="") as csvfile:
                reader = csv.reader(csvfile, delimiter = ",")
                for x, row in enumerate(reader):
                  for y, tile in enumerate(row):
                    world_data[x][y] = int(tile)
              world = World()
              world.process_data(world_data, tile_list, item_images, mob_animations)
              temp_score = player.score
              player = world.player
              p_d = True
              player.score = temp_score
              enemy_list = world.character_list
              score_coin = Item(constants.SCREEN_WIDTH - 115, 23, 0, coin_images, True)
              item_group.add(score_coin)
              #add the items from the level data
              for item in world.item_list:
                item_group.add(item)

    #event handler
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
      #take keyboard presses
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_a:
          moving_left = True
        if event.key == pygame.K_d:
          moving_right = True
        if event.key == pygame.K_w:
          moving_up = True
        if event.key == pygame.K_s:
          moving_down = True
        if event.key == pygame.K_ESCAPE:
          pause_game = True
        if event.key == pygame.K_c:
          inventory_screen = True
        if event.key == pygame.K_b:
          inventory_screen = True
        if event.key == pygame.K_i:
          inventory_screen = True
        if event.key == pygame.K_p:
          inventory_screen = True


      #keyboard button released
      if event.type == pygame.KEYUP:
        if event.key == pygame.K_a:
          moving_left = False
        if event.key == pygame.K_d:
          moving_right = False
        if event.key == pygame.K_w:
          moving_up = False
        if event.key == pygame.K_s:
          moving_down = False

    pygame.display.update()
    await asyncio.sleep(0)

asyncio.run(main(level, start_game, pause_game, inventory_screen, start_intro, screen_scroll, p_d, player, moving_down, moving_left, moving_right, moving_up, world, enemy_list, item_group, score_coin))