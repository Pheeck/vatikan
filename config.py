"""
Configuration file

This file contains global constants.
"""

# Game logic
COLORS = ("heart", "clover", "spade", "diamond")
SPECIAL_COLOR = "special" # For missing cards
RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
STARTING_HAND_NUM_CARDS = 12

# General graphics
SCREEN_SIZE = (1440, 900)
FPS = 30

# UI colors
BG_COLOR = "0x005500"
FG_COLOR = "0x227722"
ERR_COLOR = "0x772222"
TEXT_COLOR = "0x000000"
# For not frozen cards. From 0.00 (opaque) to 1.00 (invisible)
CARD_TRANSPARENCY = 0.20

# UI dimensions
ROWS_OF_STACKS = 2
COLUMNS_OF_STACKS = 19
HAND_PX_HEIGHT = 100
STACK_PX_MARGINS = 8
CARD_HEIGHT_WIDTH_RATIO = 4. / 3

# UI font
FONT_NAME = "arial"
FONT_SIZE = 9

# Files
CARDS_DIR = "cards2"
DECK_IMG_FILE = "karta.png"
