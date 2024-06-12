"""
Widgets

This file contains classes which form the UI of the game. They also represent
the state of the game.

For example the Stack class represents a stack somewhere on the board. It
contains some Card objects and knows whether the card sequence inside is valid.
It also is able to draw itself onto a canvas and given a point on the screen
answer if the point intersects any of the cards in the stack and which one.
"""

from random import shuffle
import pygame
import pygame.draw
import pygame.transform

import util
from config import *
from card import Card

class Stack:
    def __init__(self, pos, size):
        """
        pos ... (x, y) coordinates
        size ... (x, y) coordinates
        """
        self._rect = pygame.Rect(pos, size)
        self._cards = [] # Contains just cards, no missing markers
        self._cards_with_missing = [] # Sorted cards, contains missing markers
        self._is_valid = True # Is empty or contains a flush or a triplet

        # UI Invariant: At least the top 1/5 of each card should be visible
        # Also, lets assume that at least one card should be visible fully
        #
        # Now, given the total height of stack we want to compute how to resize
        # the cards to achieve this.
        #
        # We know that there will be at most len(RANKS) cards in a stack
        #
        # So stack_height <= len(RANKS) * a + 4 * a
        # Where a = 1/5 * height of a card

        a = self._rect.height / (len(RANKS) + 4)
        self._card_height = a * 5
        self._card_width = self._card_height / CARD_HEIGHT_WIDTH_RATIO

        # But if width of the stack is the limiting factor, compute height
        # based on it instead. The invariant will be kept that way too.
        if self._card_width > self._rect.w:
            self._card_width = self._rect.w
            self._card_height = self._card_width * CARD_HEIGHT_WIDTH_RATIO

    def is_empty(self):
        return not self._cards

    def size(self):
        return len(self._cards)

    def has_card(self, card):
        return card in self._cards

    def add(self, card):
        """
        Add a card onto the stack.
        """
        self._cards.append(card)
        self.reconstruct()
    
    def remove(self, card):
        """
        Remove given card from stack.
        """
        self._cards.remove(card)
        self.reconstruct()

    def reconstruct(self):
        foo = util.attempt_construct_valid_stack(self._cards)
        self._is_valid = not (foo is None or None in foo)
        if foo is None:
            self._cards_with_missing = [c for c in self._cards]
        else:
            self._cards_with_missing = foo

    def is_valid(self):
        return self._is_valid

    def freeze(self):
        for card in self._cards:
            card.freeze()

    def is_frozen(self):
        """
        Does the stack contain only frozen cards (No new card was put in the
        stack this turn)?
        """
        frozen = True
        for card in self._cards:
            frozen &= card.is_frozen()
        return frozen

    def get_state_copy(self):
        return tuple(self._cards)

    def draw(self, surface):
        # Note: card_at_point() depends on how the stack is drawn
        # When changing anything here, also check if changes shouldn't be made
        # in card_at_point()

        pygame.draw.rect(surface,
                         FG_COLOR if self._is_valid else ERR_COLOR,
                         self._rect)

        a = self._card_height / 5

        for i, card in enumerate(self._cards_with_missing):
            if card is None: # Skip "missing card" markers
                continue

            img = card.img
            card_surface = pygame.transform.scale(
                img,
                (self._card_width, self._card_height)
            )
            pos = (
                self._rect.x,
                self._rect.y + a * i
            )
            surface.blit(card_surface, pos)

    def collidepoint(self, pos):
        return self._rect.collidepoint(pos)

    def card_at_point(self, pos):
        """
        Return the card from this stack that collides with the point 'pos'. If
        there is no card, return None.
        """

        # Note: card_at_point() depends on how the stack is drawn
        # When changing anything here, also check if changes shouldn't be made
        # in draw()

        card_num = len(self._cards_with_missing)

        x = pos[0]
        y = pos[1]

        x -= self._rect.x
        y -= self._rect.y

        a = self._card_height / 5

        if x > self._card_width:
            return None

        i = int(y / a)
        if i >= card_num and i < card_num + 4:
            i = card_num - 1
        if i < 0 or i >= card_num:
            return None
        else:
            card = self._cards_with_missing[i]
            while card is None: # "missing card" marker
                i -= 1
                assert i >= 0
                card = self._cards_with_missing[i]
            return card

class Hand:
    def __init__(self, pos, size, hide_cards, deck_img=None):
        """
        pos ... (x, y) coordinates
        size ... (x, y) coordinates
        hide_cards ... if cards should be visible or turned upside down
        deck_img ... image to show for upside down cards (card backside)
        """
        self.hide_cards = hide_cards
        self.deck_img = deck_img

        self._rect = pygame.Rect(pos, size)
        self._cards = []

        self._card_height = self._rect.height
        self._card_width = self._card_height / CARD_HEIGHT_WIDTH_RATIO

        # Dynamic width based on _card_width. Smaller than _card_width when
        # there are too many cards in hand
        self._dynamic_card_width = 0
        self._update_dynamic_card_width()

    def _update_dynamic_card_width(self):
        if not self._cards:
            self._dynamic_card_width = self._card_width
        else:
            self._dynamic_card_width = min(self._card_width,
                                           self._rect.width / len(self._cards))

    def has_card(self, card):
        return card in self._cards

    def add(self, card):
        self._cards.append(card)
        self._update_dynamic_card_width()

    def remove(self, card):
        self._cards.remove(card)
        self._update_dynamic_card_width()

    def is_empty(self):
        return len(self._cards) == 0

    def get_state_copy(self):
        return set(self._cards)

    def draw(self, surface):
        # Note: card_at_point() depends on how the hand is drawn
        # When changing anything here, also check if changes shouldn't be made
        # in card_at_point()

        pygame.draw.rect(surface, FG_COLOR, self._rect)

        x = self._rect.centerx - len(self._cards) * self._dynamic_card_width / 2

        for card in self._cards:
            img = self.deck_img if self.hide_cards else card.img
            card_surface = pygame.transform.scale(
                img,
                (self._card_width, self._card_height)
            )
            pos = (
                x,
                self._rect.y
            )
            surface.blit(card_surface, pos)

            x += self._dynamic_card_width

    def collidepoint(self, pos):
        return self._rect.collidepoint(pos)

    def card_at_point(self, pos):
        """
        Return the card from this stack that collides with the point 'pos'. If
        there is none, return None.
        """

        # Note: card_at_point() depends on how the hand is drawn
        # When changing anything here, also check if changes shouldn't be made
        # in draw()

        card_num = len(self._cards)

        x = pos[0]
        y = pos[1]

        # hand_x and hand_y is at the top left corner of the leftmost card
        hand_x = self._rect.x + \
                 (self._rect.w - self._dynamic_card_width * card_num) / 2
        hand_y = self._rect.y

        x -= hand_x
        y -= hand_y

        i = int(x / self._dynamic_card_width)
        if i < 0 or i >= card_num:
            return None
        else:
            return self._cards[i]

class PickUpArea:
    def __init__(self, pos, size):
        """
        pos ... (x, y) coordinates
        size ... (x, y) coordinates
        """
        self._rect = pygame.Rect(pos, size)
        self._card = None

    def has_card(self):
        return not self._card is None

    def put(self, card):
        self._card = card

    def get(self):
        return self._card

    def pop(self):
        card = self._card
        self._card = None
        return card
    
    def draw(self, surface):
        pygame.draw.rect(surface, FG_COLOR, self._rect)
        if self._card:
            card_surface = pygame.transform.scale(self._card.img,
                                                  self._rect.size)
            surface.blit(card_surface, self._rect.topleft)

class Deck:
    def __init__(self, pos, size, card_imgs, deck_img, font):
        """
        pos ... (x, y) coordinates
        size ... (x, y) coordinates
        card_imgs ... 2d list mapping (color, rank) to pygame image objects
        deck_img ... pygame image object representing the deck
        font ... font with which to display the remaining number of cards

        Fill the deck with cards and shuffle it
        """
        self._rect = pygame.Rect(pos, size)
        self._surface = pygame.transform.scale(deck_img, size)

        self._cards = []
        for color in COLORS:
            for rank in RANKS:
                img = card_imgs[color][rank]
                # Each card two times
                self._cards.append(Card(color, rank, img))
                self._cards.append(Card(color, rank, img))
        shuffle(self._cards)

        self._font = font
        self._text_surface = None
        self._update_text()

    def _update_text(self):
        """
        Update the surface displaying the number of remaining cards
        """
        self._text_surface = self._font.render(
            str(len(self._cards)), 
            True,
            TEXT_COLOR
        )

    def is_empty(self):
        return not self._cards

    def pop(self):
        if self._cards:
            card = self._cards.pop()
            self._update_text()
            return card
        else:
            return None

    def draw(self, surface):
        if self._cards:
            surface.blit(self._surface, self._rect.topleft)
        else:
            pygame.draw.rect(surface, FG_COLOR, self._rect)

        pos = (
            self._rect.centerx - self._text_surface.get_width() / 2,
            self._rect.top - self._text_surface.get_height()
        )
        surface.blit(self._text_surface, pos)

    def collidepoint(self, pos):
        return self._rect.collidepoint(pos)

class EndTurnButton:
    def __init__(self, pos, size, font):
        self._rect = pygame.Rect(pos, size)
        self._font = font

        self._board_valid = True
        self._card_draw_needed = True
        self._player_name = ""

        self._text_surface1 = None
        self._text_surface2 = None
        self._text_surface3 = None
        self._update_text()

    def _update_text(self):
        text1 = f"Hraje {self._player_name}"
        text2 = "Predat tah" if self._board_valid else ""
        text3 = "a liznout si" if self._board_valid and \
            self._card_draw_needed else ""
        self._text_surface1 = self._font.render(
            text1,
            True,
            TEXT_COLOR
        )
        self._text_surface2 = self._font.render(
            text2,
            True,
            TEXT_COLOR
        )
        self._text_surface3 = self._font.render(
            text3,
            True,
            TEXT_COLOR
        )

    def set_board_valid(self):
        self._board_valid = True
        self._update_text()

    def unset_board_valid(self):
        self._board_valid = False
        self._update_text()

    def set_card_draw_needed(self):
        self._card_draw_needed = True
        self._update_text()

    def unset_card_draw_needed(self):
        self._card_draw_needed = False
        self._update_text()

    def set_player_name(self, player):
        self._player_name = player
        self._update_text()

    def draw(self, surface):
        color = FG_COLOR if self._board_valid else BG_COLOR
        pygame.draw.rect(surface, color, self._rect)
        pos = (
                self._rect.x,
                self._rect.centery \
                - (self._text_surface1.get_height() +
                   self._text_surface2.get_height() +
                   self._text_surface3.get_height())
        )
        surface.blit(self._text_surface1, pos)
        pos = (
                pos[0],
                pos[1] + self._text_surface1.get_height()
        )
        surface.blit(self._text_surface2, pos)
        pos = (
                pos[0],
                pos[1] + self._text_surface2.get_height()
        )
        surface.blit(self._text_surface3, pos)

    def collidepoint(self, pos):
        return self._rect.collidepoint(pos)
