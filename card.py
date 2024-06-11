"""
The Card class

This file contains the class representing cards in this program.
"""

from config import *

class Card:
    def __init__(self, color, rank, img):
        self.color = color
        self.rank = rank
        self.img = img.copy()

        self._frozen = False
        self._update_alpha()

    def freeze(self):
        self._frozen = True
        self._update_alpha()

    def is_frozen(self):
        return self._frozen

    def _update_alpha(self):
        if self._frozen:
            self.img.set_alpha(255 * 1.00)
        else:
            self.img.set_alpha(255 * (1.00 - CARD_TRANSPARENCY))
