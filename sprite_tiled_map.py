"""
Load a tiled map file and run around with multiple players

Author: Fred Derks
Version: 21-11-2019
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
BEBAS = 'C:\\WINDOWS\\FONTS\\BEBASNEUE BOLD.OTF'

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
VIEWPORT_MARGIN_TOP = 270
VIEWPORT_MARGIN_BOTTOM = 270
VIEWPORT_RIGHT_MARGIN = 400
VIEWPORT_LEFT_MARGIN = 400

# Physics
MOVEMENT_SPEED = 5
JUMP_SPEED = 17
GRAVITY = 1.8

# Positions
POSITION_DATA = pd.read_csv("positions.csv")
CURRENT_PLAYER = 0


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
            arcade.Sprite("images/char1.png", SPRITE_SCALING),
            arcade.Sprite("images/char2.png", SPRITE_SCALING),
            arcade.Sprite("images/char3.png", SPRITE_SCALING),
            arcade.Sprite("images/char4.png", SPRITE_SCALING),
            arcade.Sprite("images/char5.png", SPRITE_SCALING),
            arcade.Sprite("images/char6.png", SPRITE_SCALING)
        ]

        # Starting position of the players
        i = 0
        for char in self.char_list:
            char.center_x = int(POSITION_DATA.at[i, 'x'])
            char.bottom = int(POSITION_DATA.at[i, 'y'])
            self.player_list.append(char)
            i += 1

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

        # --- Other stuff
        # Set the background color
        if my_map.backgroundcolor:
            arcade.set_background_color(my_map.backgroundcolor)

        # --- Switch players
        if self.player_sprite is None:
            self.choose_player(CURRENT_PLAYER)

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
                         'Press F to toggle between full screen and windowed mode.',
                         screen_width // 8 + 200, screen_height // 8 - 80,
                         arcade.color.BLACK, 16, align="center",
                         font_name=BEBAS)

        if self.game_over:
            arcade.draw_text("\nGame Over", self.view_left + 600, self.view_bottom + 600,
                             arcade.color.WHITE, 70, font_name=BEBAS)

    def on_key_press(self, key, modifiers):
        """
        Called whenever the user presses a key.
        """
        if key == arcade.key.UP:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = JUMP_SPEED
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = MOVEMENT_SPEED
        elif key == arcade.key.F:
            # User hits f. Flip between full and not full screen.
            self.set_fullscreen(not self.fullscreen)

            # Get the window coordinates. Match viewport to window coordinates
            # so there is a one-to-one mapping.

    def on_key_release(self, key, modifiers):
        """
        Called when the user releases the key.
        """
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0
        elif key == arcade.key.KEY_1:
            self.choose_player(0)
            self.setup()
        elif key == arcade.key.KEY_2:
            self.choose_player(1)
            self.setup()
        elif key == arcade.key.KEY_3:
            self.choose_player(2)
            self.setup()

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
        left_boundary = self.view_left + VIEWPORT_LEFT_MARGIN
        if self.player_sprite.left < left_boundary:
            self.view_left -= left_boundary - self.player_sprite.left
            changed = True

        # Scroll right
        right_boundary = self.view_left + SCREEN_WIDTH - VIEWPORT_RIGHT_MARGIN
        if self.player_sprite.right > right_boundary:
            self.view_left += self.player_sprite.right - right_boundary
            changed = True

        # Scroll up
        top_boundary = self.view_bottom + SCREEN_HEIGHT - VIEWPORT_MARGIN_TOP
        if self.player_sprite.top > top_boundary:
            self.view_bottom += self.player_sprite.top - top_boundary
            changed = True

        # Scroll down
        bottom_boundary = self.view_bottom + VIEWPORT_MARGIN_BOTTOM
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

    def choose_player(self, player):
        """
        Called when player is chosen [1 to 6]
        It is called at setup on initialisation
        And subsequently from on_key_release
        """
        if self.first_time:
            self.player_sprite = self.player_list[player]
            self.first_time = False
        # if a player is switched, save the position of the current player first.
        else:
            POSITION_DATA.at[CURRENT_PLAYER, 'x'] = int(self.player_sprite.center_x)
            POSITION_DATA.at[CURRENT_PLAYER, 'y'] = int(self.player_sprite.bottom)
            self.player_sprite = self.player_list[player]


def main():
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
