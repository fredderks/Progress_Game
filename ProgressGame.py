"""
Load a tiled map file and run around with multiple players

Author: Fred Derks
Version: 25-11-2019
Artwork from: http://kenney.nl
Tiled available from: http://www.mapeditor.org/
"""

import arcade
import os
import pandas as pd

SPRITE_SCALING = 0.5
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Progress Game"
SPRITE_PIXEL_SIZE = 64
GRID_PIXEL_SIZE = int(SPRITE_PIXEL_SIZE * SPRITE_SCALING)
BEBAS = 'res\\BebasNeue Bold.otf'

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
VIEWPORT_MARGIN_TOP = 60
VIEWPORT_MARGIN_BOTTOM = 60
VIEWPORT_RIGHT_MARGIN = 270
VIEWPORT_LEFT_MARGIN = 270

# Physics
MOVEMENT_SPEED = 5
JUMP_SPEED = 17
GRAVITY = 1.8

# Positions
POSITION_DATA = pd.read_csv('res\position_data.csv')
CURRENT_PLAYER = int(0)
CHOSEN_PLAYER = int(0)


class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self):
        """
        Initializer
        """
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Sprite lists
        self.wall_list = None
        self.player_list = None
        self.coin_list = None
        self.text_list = None
        self.char_list = None

        # Set up the player
        self.score = 0
        self.player_sprite = None

        # Set up physics and logic
        self.physics_engine = None
        self.view_left = 0
        self.view_bottom = 0
        self.end_of_map = 0
        self.game_over = False
        self.last_time = None
        self.frame_count = 0
        self.fps_message = None

        # Set up other logic
        self.theme = None
        self.first_time = True

    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.text_list = arcade.SpriteList()

        # Set up the players
        self.char_list = [
            arcade.Sprite("res/philip.png", SPRITE_SCALING),
            arcade.Sprite("res/heleen.png", SPRITE_SCALING),
            arcade.Sprite("res/alexandra.png", SPRITE_SCALING),
            arcade.Sprite("res/bart.png", SPRITE_SCALING),
            arcade.Sprite("res/jessica.png", SPRITE_SCALING),
            arcade.Sprite("res/evelien.png", SPRITE_SCALING)
        ]

        # Read in the tiled map
        my_map = arcade.read_tiled_map('mount.tmx', SPRITE_SCALING)

        # --- Walls ---
        # Grab the layer of items we can't move through
        map_array = my_map.layers_int_data['Platforms']

        # Calculate the right edge of the my_map in pixels
        self.end_of_map = len(map_array[0]) * GRID_PIXEL_SIZE

        # --- Platforms ---
        self.wall_list = arcade.generate_sprites(my_map, 'Platforms', SPRITE_SCALING)

        # --- Text ---
        self.text_list = arcade.generate_sprites(my_map, 'Text', SPRITE_SCALING)

        # --- Set the background color
        if my_map.backgroundcolor:
            arcade.set_background_color(my_map.backgroundcolor)

        # --- Players ---
        # --- Choose Player and save position of current player
        global CURRENT_PLAYER
        self.choose_player(CURRENT_PLAYER, CHOSEN_PLAYER)
        CURRENT_PLAYER = CHOSEN_PLAYER

        # --- Starting position of the players
        i = 0
        for char in self.char_list:
            char.center_x = POSITION_DATA.at[i, 'x']
            char.bottom = POSITION_DATA.at[i, 'y']
            self.player_list.append(char)
            i += 1

        # Keep player from running through the wall_list layer
        self.physics_engine = \
            arcade.PhysicsEnginePlatformer(self.player_sprite,
                                           self.wall_list,
                                           gravity_constant=GRAVITY)

        # Set the view port boundaries
        # These numbers set where we have 'scrolled' to.
        self.view_left = 0
        self.view_bottom = 0

        self.game_over = False

    def on_draw(self):
        """
        Render the screen.
        """

        self.frame_count += 1

        # This command has to happen before we start drawing
        arcade.start_render()
        super().on_draw()

        # Draw all the sprites.
        self.wall_list.draw()
        self.coin_list.draw()
        self.text_list.draw()
        self.player_list.draw()

        # Get viewport dimensions
        screen_width, screen_height = self.get_size()

        # Draw text on the screen so the user has an idea of what is happening
        arcade.draw_text('\nUse the arrow buttons to navigate\n\n'
                         'Choose a player using the number keys\n\n'
                         'Press F to toggle between full screen and windowed mode.\n\n'
                         'Press S to save the positions of the players before closing the window',
                         screen_width // 8 + 200, screen_height // 8,
                         arcade.color.BLACK, 16, align="center",
                         font_name=BEBAS)

        arcade.draw_text('\n1. Philip\n\n'
                         '2. Heleen\n\n'
                         '3. Alexandra\n\n'
                         '4. Bart\n\n'
                         '5. Jessica\n\n'
                         '6. Evelien',
                         screen_width // 8 + 800, screen_height // 8,
                         arcade.color.BLACK, 16, align="left",
                         font_name=BEBAS)

        if self.game_over:
            arcade.draw_text("\nGame Over", self.view_left + 600, self.view_bottom + 600,
                             arcade.color.WHITE, 70, font_name=BEBAS)

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
        elif key in (arcade.key.F, arcade.key.ESCAPE):
            # User hits f. Flip between full and not full screen.
            self.set_fullscreen(not self.fullscreen)
        elif key == arcade.key.S:
            POSITION_DATA.at[CURRENT_PLAYER, 'x'] = self.player_sprite.center_x
            POSITION_DATA.at[CURRENT_PLAYER, 'y'] = self.player_sprite.bottom
            POSITION_DATA.to_csv('res\position_data.csv', index=False)
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
        elif key in (arcade.key.KEY_6, arcade.key.NUM_6):
            CHOSEN_PLAYER = 5
            self.setup()
            self.jump_on_choose()

    def on_key_release(self, key, modifiers):
        """
        Called when the user releases the key.
        """
        if key in (arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.D):
            self.player_sprite.change_x = 0

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Game over when sprite reaches end of map
        if self.player_sprite.right >= self.end_of_map or self.player_sprite.left <= -100:
            self.game_over = True

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        if not self.game_over:
            self.physics_engine.update()

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
        Called when player is chosen [1 to 6]
        It is called at setup on initialisation
        And subsequently from on_key_release
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
