#!/usr/bin/env python3

"""
PyGame implementation of the card game 'Vatikán'.

Note: What do we mean by "cyclic order" mentioned in code comments?
In cyclic order we treat the highest card rank as a predecessor of the lowest
card rank. So K is the predecessor of A and A is the predecessort of 2.

Note2: What do we mean by a "flush" and a "triplet"?
A flush is a list of size >= 3 containing cards of same color but unique ranks
that form a cyclic sequence. A triplet is a list of size >= 3 containing cards
of unique color but same ranks.

Note3: What do we mean by a "frozen" card?
The rules prohibit you from picking up cards from the board to your hand. So
at the end of a turn, all cards on the board are set as frozen. Frozen cards
can be moved between stacks on the board but cannot enter a players hand. We
allow you to move the cards that were in your hand at the start of the turn
freely. This way you can interactively figure out what works and only fully
commit to placing cards on the board by ending your turn.
"""

import pygame

from menu import Menu
from game import Game
from config import *

if __name__ == "__main__":
    pygame.init()

    # Load images
    deck_img = pygame.image.load(DECK_IMG_FILE)
    missing_img = pygame.image.load(DECK_IMG_FILE)
    card_imgs = {}
    for color in COLORS:
        card_imgs[color] = {}
        for rank in RANKS:
            card_imgs[color][rank] = pygame.image.load(
                CARDS_DIR + "/card_" \
                + str(((RANKS.index(rank) + 1) % len(RANKS)) + 1) \
                + "_" + color + ".png"
            )

    screen = pygame.display.set_mode(SCREEN_SIZE)

    menu = Menu(screen)
    gamemode = menu.run()

    game = Game(gamemode, screen, deck_img, missing_img, card_imgs)
    game.run()
