"""
Load a tiled map file and run around with multiple players

Author: Fred Derks
Version: 23-12-2019
Artwork from: http://kenney.nl
Tiled available from: http://www.mapeditor.org/
Tutorial at: http://arcade.academy/examples/platform_tutorial/index.html
"""

import random
import os
import sys
import pandas as pd
import arcade
from win32api import GetSystemMetrics

os.chdir(sys.path[0])               # Change working directory to the one in which this script is located
print(os.getcwd())

SPRITE_SCALING = 0.5
SCREEN_WIDTH = GetSystemMetrics(0)
SCREEN_HEIGHT = GetSystemMetrics(1)
SCREEN_TITLE = "Progress Game"
SPRITE_PIXEL_SIZE = 64
CLOUD_COUNT = 12
GRID_PIXEL_SIZE = int(SPRITE_PIXEL_SIZE * SPRITE_SCALING)
BEBAS = "res/BebasNeue Bold.otf"                        # Calco lettertype

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
VIEWPORT_MARGIN_TOP = 270
VIEWPORT_MARGIN_BOTTOM = 120
VIEWPORT_RIGHT_MARGIN = 270
VIEWPORT_LEFT_MARGIN = 270

# Physics
MOVEMENT_SPEED = 5
JUMP_SPEED = 17
GRAVITY = 1.8
ANGLE_SPEED = 5

# Positions
POSITION_DATA = pd.read_csv("res/position_data.csv")
CURRENT_PLAYER = int(0)
CHOSEN_PLAYER = int(0)

# Animation
BOTTLE_ANGLE = 0  # Do not adjust
TURN_RIGHT = True
ANIMATION_COUNTER = 0  # Do not adjust
ANIMATION_DURATION = 5


class Cloud(arcade.Sprite):
    """
    This class represents the clouds on our screen. It is a child class of
    the arcade library's "Sprite" class.
    """
    def reset_pos(self):
        # Reset the cloud to a random spot above the screen
        self.center_y = random.randrange(SCREEN_HEIGHT - 50, SCREEN_HEIGHT + 300)
        self.center_x = random.randrange(-300, -200)

    def update(self):
        # Move the cloud
        self.center_x += 0.3

        # See if the cloud has fallen off the edge of the screen.
        # If so, reset it.
        if self.left > SCREEN_WIDTH + 500:
            self.reset_pos()


class Champagne(arcade.Sprite):
    """
    This class represents the champagne bottle on our screen. It is a child class of
    the arcade library's "Sprite" class.
    """
    def update(self):
        # Rotate the bottle
        global BOTTLE_ANGLE

        if TURN_RIGHT:                  # Swing Right
            self.angle += ANGLE_SPEED
            BOTTLE_ANGLE += 1
        else:                           # Swing Left
            self.angle -= ANGLE_SPEED
            BOTTLE_ANGLE -= 1


class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self):
        """ Initializer """

        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Sprite lists
        self.wall_list = None
        self.player_list = None
        self.decorations_list = None
        self.champagne_list = None
        self.background_list = None
        self.text_list = None
        self.char_list = None
        self.cloud_sprite_list = None
        self.champagne_sprite_list = None

        # Set up the player
        self.score = 0
        self.player_sprite = None

        # Set up physics and logic
        self.physics_engine = None
        self.view_left = 0
        self.view_bottom = 0
        self.end_of_map = 0
        self.top_level = False
        self.last_time = None
        self.frame_count = 0
        self.fps_message = None

        # Set up other logic
        self.first_time = True
        self.background = arcade.load_texture("res/mount_bg2.jpg")

    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.decorations_list = arcade.SpriteList()
        self.champagne_list = arcade.SpriteList()
        self.text_list = arcade.SpriteList()
        self.background_list = arcade.SpriteList()
        self.cloud_sprite_list = arcade.SpriteList()
        self.champagne_sprite_list = arcade.SpriteList()

        # Set up the players
        self.char_list = [
            arcade.Sprite("res/philip.png", SPRITE_SCALING),
            arcade.Sprite("res/heleen.png", SPRITE_SCALING),
            arcade.Sprite("res/alexandra.png", SPRITE_SCALING),
            arcade.Sprite("res/bart.png", SPRITE_SCALING),
            arcade.Sprite("res/jessica.png", SPRITE_SCALING),
        ]

        # Create the clouds
        for i in range(CLOUD_COUNT):
            # Create the cloud instance
            cloud = Cloud("res/cloud.png", SPRITE_SCALING)
            doublecloud = Cloud("res/doublecloud.png", SPRITE_SCALING)

            # Position the cloud
            cloud.center_x = random.randrange(-200, 2200)
            cloud.center_y = random.randrange(SCREEN_HEIGHT - 50, SCREEN_HEIGHT + 300)

            doublecloud.center_x = random.randrange(-200, 2200)
            doublecloud.center_y = random.randrange(SCREEN_HEIGHT - 50, SCREEN_HEIGHT + 300)

            # Add the cloud to the lists
            self.cloud_sprite_list.append(cloud)
            self.cloud_sprite_list.append(doublecloud)

        # Create the Champagne
        champagne = Champagne("res/champagne-closed.png", SPRITE_SCALING)

        # Position the champagne bottle
        champagne.center_x = 1728
        champagne.bottom = 864

        # Add the champagne bottle to the lists
        self.champagne_sprite_list.append(champagne)

        # Read in the tiled map
        my_map = arcade.read_tiled_map('mount.tmx', SPRITE_SCALING)

        # --- Background ---
        self.background_list = arcade.generate_sprites(my_map, 'Background', SPRITE_SCALING)

        # --- Decorations ---
        self.decorations_list = arcade.generate_sprites(my_map, 'Decorations', SPRITE_SCALING)

        # --- Platforms ---
        self.wall_list = arcade.generate_sprites(my_map, 'Platforms', SPRITE_SCALING)

        # --- Text ---
        self.text_list = arcade.generate_sprites(my_map, 'Text', SPRITE_SCALING)

        # --- Champagne ---
        self.champagne_list = arcade.generate_sprites(my_map, 'Champagne', SPRITE_SCALING)

        # --- Set the background color
        if my_map.backgroundcolor:
            arcade.set_background_color(my_map.backgroundcolor)

        # --- Players ---
        # --- Choose Player and save position of current player
        global CURRENT_PLAYER
        self.choose_player(CURRENT_PLAYER, CHOSEN_PLAYER)
        CURRENT_PLAYER = CHOSEN_PLAYER                  # Update current player

        # --- Starting position of the players
        i = 0
        for char in self.char_list:
            char.center_x = POSITION_DATA.at[i, 'x']
            char.bottom = POSITION_DATA.at[i, 'y']
            self.player_list.append(char)
            i += 1

        # Keep player from running through the wall_list layer
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
                                                             self.wall_list, gravity_constant=GRAVITY)

    def on_draw(self):
        """
        Render the screen.
        """

        self.frame_count += 1

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw a rectangle containing our background picture
        arcade.draw_texture_rectangle((SCREEN_WIDTH // 2) + self.view_left, (SCREEN_HEIGHT // 2) + self.view_bottom,
                                      SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

        # Draw all the sprites.
        self.background_list.draw()
        self.wall_list.draw()
        self.decorations_list.draw()
        self.text_list.draw()
        self.player_list.draw()
        self.cloud_sprite_list.draw()
        self.champagne_sprite_list.draw()

        # Get viewport dimensions
        screen_width, screen_height = self.get_size()

        # Draw text on the screen so the user has an idea of what is happening
        arcade.draw_text('\nUse the arrow buttons to navigate\n\n'
                         'Choose a player using the number keys\n\n'
                         'Press F to toggle between full screen and windowed mode.\n\n'
                         'Press S to save the positions of the players before closing the window',
                         screen_width // 4 + 250, screen_height // 4 + 75,
                         arcade.color.BLACK, 16, align="center",
                         font_name=BEBAS)

        arcade.draw_text('\n1. Philip\n\n'
                         '2. Heleen\n\n'
                         '3. Alexandra\n\n'
                         '4. Bart\n\n'
                         '5. Jessica',
                         screen_width // 4 + 850, screen_height // 4 + 75,
                         arcade.color.BLACK, 16, align="left",
                         font_name=BEBAS)

        if self.top_level:                      # If all players are on the top level:
            global BOTTLE_ANGLE
            global TURN_RIGHT
            global ANIMATION_COUNTER

            if ANIMATION_COUNTER < ANIMATION_DURATION:  # Wiggle the champagne bottle a number of times
                self.champagne_sprite_list.update()
            if ANIMATION_COUNTER > 35:          # Wait a bit and draw the open champagne bottle over it.
                self.champagne_list.draw()
            if ANIMATION_COUNTER > 45:
                arcade.draw_text("\nWell Done!", self.view_left + 500, self.view_bottom + 600,
                                 color=(255, 0, 115), font_size=140, font_name=BEBAS)

            if BOTTLE_ANGLE == 10:              # When bottle hits an angle of 10, start turning left
                TURN_RIGHT = False
            elif BOTTLE_ANGLE == -10:           # When bottle hits an angle of -10 start turning right
                TURN_RIGHT = True
            elif BOTTLE_ANGLE == 0:             # Add to the counter when the bottle passes vertical
                ANIMATION_COUNTER += 1

    def on_key_press(self, key, modifiers):
        """
        Called whenever the user presses a key.
        """
        global CHOSEN_PLAYER
        if key in (arcade.key.UP, arcade.key.W):
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = JUMP_SPEED
                self.player_sprite.change_x = 0
        elif key in (arcade.key.LEFT, arcade.key.A):
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.player_sprite.change_x = MOVEMENT_SPEED
        elif key in (arcade.key.F, arcade.key.ESCAPE):             # User hits f. Flip between full and not full screen.
            self.set_fullscreen(not self.fullscreen)
        elif key == arcade.key.S:
            POSITION_DATA.at[CURRENT_PLAYER, 'x'] = self.player_sprite.center_x
            POSITION_DATA.at[CURRENT_PLAYER, 'y'] = self.player_sprite.bottom
            POSITION_DATA.to_csv("res/position_data.csv", index=False)
        elif key in (arcade.key.KEY_1, arcade.key.NUM_1):
            CHOSEN_PLAYER = 0
            self.setup()
            self.jump_on_choose()
        elif key in (arcade.key.KEY_2, arcade.key.NUM_2):
            CHOSEN_PLAYER = 1
            self.setup()
            self.jump_on_choose()
        elif key in (arcade.key.KEY_3, arcade.key.NUM_3):
            CHOSEN_PLAYER = 2
            self.setup()
            self.jump_on_choose()
        elif key in (arcade.key.KEY_4, arcade.key.NUM_4):
            CHOSEN_PLAYER = 3
            self.setup()
            self.jump_on_choose()
        elif key in (arcade.key.KEY_5, arcade.key.NUM_5):
            CHOSEN_PLAYER = 4
            self.setup()
            self.jump_on_choose()

    def on_key_release(self, key, modifiers):
        """ Called when the user releases the key. """
        if key in (arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.D):
            self.player_sprite.change_x = 0

    def on_update(self, delta_time):
        """ Movement and game logic """

        self.cloud_sprite_list.update()

        # # Game over when sprite reaches end of map
        # if self.player_sprite.right >= self.end_of_map or self.player_sprite.left <= -100:
        #     self.game_over = True

        # Call update on all sprites (The sprites don't do much in this example though.)
        self.physics_engine.update()

        # Draw Champagne Bottle if player is on top level
        global ANIMATION_COUNTER
        if self.player_sprite.bottom > 765:
            sprite_positions = []
            for i in range(len(self.char_list)):         # Get positions for all sprites
                if i == CURRENT_PLAYER:
                    continue                            # Skip current sprite
                sprite_positions.append(POSITION_DATA.at[i, 'y'])
            if min(sprite_positions) > 765:             # If all sprites are above 600 px, top level logic is true
                self.top_level = True
        elif self.player_sprite.bottom <= 765 and BOTTLE_ANGLE == 0:
            self.top_level = False
            ANIMATION_COUNTER = 0                       # Reset animation when user leaves the platform

        # --- Manage Scrolling ---

        # Track if we need to change the view port

        changed = False

        # Scroll left
        left_boundary = int(self.view_left + VIEWPORT_LEFT_MARGIN)
        if self.player_sprite.left < left_boundary:
            self.view_left -= left_boundary - self.player_sprite.left
            changed = True

        # Scroll right
        right_boundary = int(self.view_left + SCREEN_WIDTH - VIEWPORT_RIGHT_MARGIN)
        if self.player_sprite.right > right_boundary:
            self.view_left += self.player_sprite.right - right_boundary
            changed = True

        # Scroll up
        top_boundary = int(self.view_bottom + SCREEN_HEIGHT - VIEWPORT_MARGIN_TOP)
        if self.player_sprite.top > top_boundary:
            self.view_bottom += self.player_sprite.top - top_boundary
            changed = True

        # Scroll down
        bottom_boundary = int(self.view_bottom + VIEWPORT_MARGIN_BOTTOM)
        if self.player_sprite.bottom < bottom_boundary:
            self.view_bottom -= bottom_boundary - self.player_sprite.bottom
            changed = True

        # If we need to scroll, go ahead and do it.
        if changed:
            self.view_left = int(self.view_left)
            self.view_bottom = int(self.view_bottom)
            arcade.set_viewport(self.view_left,
                                SCREEN_WIDTH + self.view_left,
                                self.view_bottom,
                                SCREEN_HEIGHT + self.view_bottom)

    def choose_player(self, current, chosen):
        """
        Called when player is chosen [1 to 5].
        It is called at setup on initialisation.
        And subsequently from on_key_press.
        """
        if self.first_time:
            self.player_sprite = self.char_list[chosen]  # This works the first time
            self.first_time = False
        # if a player is switched, save the position of the current player first.
        else:
            POSITION_DATA.at[current, 'x'] = self.player_sprite.center_x
            POSITION_DATA.at[current, 'y'] = self.player_sprite.bottom
            POSITION_DATA.to_csv("res/position_data.csv", index=False)
            self.player_sprite = self.char_list[chosen]

    def jump_on_choose(self):
        if self.physics_engine.can_jump():
            self.player_sprite.change_y = JUMP_SPEED / 2


def main():
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
