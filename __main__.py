#!/usr/bin/env python3

"""
A prototype PyGame implementation of the card game 'Vatikán'.

Note: What do we mean by "cyclic order" mentioned in code comments?
In cyclic order we treat the highest card rank as a predecessor of the lowest
card rank. So K is the predecessor of A and A is the predecessort of 2.

Note2: What do we mean by a "flush" and a "triplet"?
A flush is a list of size >= 3 containing cards of same color but unique ranks
that form a cyclic sequence. A triplet is a list of size >= 3 containing cards
of unique color but same ranks.
"""

from random import shuffle
import pygame
import pygame.image
import pygame.draw
import pygame.transform
import pygame.font


#############
# CONSTANTS #
#############

BG_COLOR = "0x005500"
FG_COLOR = "0x227722"
ERR_COLOR = "0x772222"
TEXT_COLOR = "0x000000"
SCREEN_SIZE = (1440, 900)
FPS = 30
COLORS = ("heart", "clover", "spade", "diamond")
SPECIAL_COLOR = "special" # For missing cards
RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
ROWS_OF_STACKS = 1
COLUMNS_OF_STACKS = 8
HAND_PX_HEIGHT = 160
STACK_PX_MARGINS = 16
CARD_HEIGHT_WIDTH_RATIO = 4. / 3
STARTING_HAND_NUM_CARDS = 7
FONT_NAME = "arial"
FONT_SIZE = 24


#####################
# UTILITY FUNCTIONS #
#####################

def sorted_by_rank(cards):
    """
    Return the given list of cards (class Card) sorted by rank
    """
    return sorted(cards, key=lambda x: x.rank)

def get_biggest_gap(cards):
    """
    Given a list of Card objects sorted by ranks, return the biggest rank gap.
    That means return i such that the difference of ranks of cards[i] and
    cards[(i+1) % len(cards)] is the biggest
    """

    max_gap_i = 0
    max_difference = 0
    for i in range(len(cards)):
        rank1 = cards[i].rank
        rank2 = cards[(i + 1) % len(cards)].rank
        difference = (RANKS.index(rank2) - RANKS.index(rank1)) % len(RANKS)
        if difference > max_difference:
            max_gap_i = i
            max_difference = difference
    return max_gap_i

def is_cyclic_sequence(cards): # TODO ?Archive? and remove
    """
    Do ranks of given cards (class Card) form a gapless cyclic sequence? If
    yes, return -1. Else return the index i such that cards[i] and cards[i+1]
    have the biggest rank gap between them.

    Do not consider colors.

    A sorted list must be given.
    """

    i = get_biggest_gap(cards)

    # There must be no other gaps
    j = (i + 1) % len(cards)
    while j != i:
        rank1 = cards[j].rank
        rank2 = cards[(j + 1) % len(cards)].rank
        difference = (RANKS.index(rank2) - RANKS.index(rank1)) % len(cards)

        if difference > 1:
            return i

        j = (j + 1) % len(cards)

    return -1

def is_triplet(cards):
    """
    Return True iff cards form a triplet (see Note2 for definition)
    """
    # Three or four
    if len(cards) < 3 or len(cards) > 4:
        return False

    # Same rank
    rank = cards[0].rank
    for card in cards:
        if card.rank != rank:
            return False

    # Different colors
    colors = []
    for card in cards:
        if card.color in colors:
            return False
        else:
            colors.append(card.color)

    return True

def attempt_construct_flush(cards):
    """
    Try to construct a flush (see Note2 for definition) from given cards
    possibly using missing card markers and return the flush. If constructing
    the flush is not possible (there are less than 3 cards, there are multiple
    cards of same rank or not all cards are of the same color), return None.
    """
    flush = sorted_by_rank(cards)

    # At least three cards
    if len(flush) < 3:
        return None

    # Same color
    color = flush[0].color
    for card in flush:
        if card.color != color:
            return None

    # Different ranks
    ranks = []
    for card in flush:
        if card.rank in ranks:
            return None
        else:
            ranks.append(card.rank)

    # We now know flush can be constructed. Construct it.
    result = []

    # Rotate flush so that the biggest gap is on the outside (it is between the
    # last and the first card)
    i = get_biggest_gap(flush)
    i = (i + 1) % len(flush)
    flush = flush[i:] + flush[:i]

    result.append(flush[0])
    last_card = flush[0]
    for card in flush[1:]:
        x = RANKS.index(last_card.rank)
        y = RANKS.index(card.rank)
        d = (y - x) % len(RANKS) # Difference of ranks

        # If there is a gap between cards, insert missing markers
        while d > 1:
            result.append(missing_card)
            d -= 1

        last_card = card
        result.append(card)

    return result


###########
# CLASSES #
###########

class Card:
    def __init__(self, color, rank, img):
        self.color = color
        self.rank = rank
        self.img = img

class Stack:
    def __init__(self, pos, size):
        """
        pos ... (x, y) coordinates
        size ... (x, y) coordinates
        """
        self._rect = pygame.Rect(pos, size)
        self._cards = [] # Contains just cards, no missing markers
        self._cards_with_missing = [] # Sorted cards, contains missing markers
        self._valid = True # Is empty or contains a flush or a triplet

        # UI Invariant: At least the top 1/5 of each card should be visible
        # Also, lets assume that at least on card should be visible fully
        #
        # Now, given the total height of stack we want to compute how to resize
        # the cards to achieve this.
        #
        # We know that there will be at most len(RANKS) cards in a stack
        #
        # So stack_height <= len(RANKS) * a + 4 * x
        # Where a = 1/5 * height of a card

        a = self._rect.height / (len(RANKS) + 4)
        self.card_height = a * 5 # TODO Schovat do nejake konstanty?
        self.card_width = self.card_height / CARD_HEIGHT_WIDTH_RATIO

    def add(self, card):
        """
        Add a card into the stack. Return True if card was successfully added.
        Return False if the stack rejected the card (for example it may already
        contain a card of the same color and rank).
        """
        self._cards.append(card)
        self.reconstruct()
    
    def remove(self, card):
        """
        Remove given card from stack
        """
        self._cards.remove(card)
        self.reconstruct()

    def reconstruct(self):
        """
        Construct _cards_with_missing from _cards and update _valid.

        If _cards form a triplet, _cards_with_missing := _cards. If _cards form
        a flush (possibly with missing cards), fill missing cards with missing
        card markers. If neither a triplet nor a flush can be formed from
        _cards, _cards_with_missing := _cards.

        _valid = True if a triplet or a flush was formed and if a flush was
        formed, it contained no missing cards. _valid = True also if the stack
        is empty.
        """
        if not self._cards:
            self._cards_with_missing = []
            self._valid = True
            return

        if is_triplet(self._cards):
            self._cards_with_missing = [c for c in self._cards]
            self._valid = True
            return

        foo = attempt_construct_flush(self._cards)
        if not foo is None:
            self._cards_with_missing = foo
            self._valid = missing_card not in foo
            return

        self._cards_with_missing = [c for c in self._cards]
        self._valid = False

    def draw(self, surface):
        # Note: card_at_point() depends on how the stack is drawn
        # When changing anything here, also check if changes shouldn't be made
        # in card_at_point()

        pygame.draw.rect(surface,
                         FG_COLOR if self._valid else ERR_COLOR,
                         self._rect)

        a = self.card_height / 5

        for i, card in enumerate(self._cards_with_missing):
            img = card.img
            card_surface = pygame.transform.scale(
                img,
                (self.card_width, self.card_height)
            )
            pos = (
                self._rect.x,
                self._rect.y + a * i
            )
            screen.blit(card_surface, pos)

    def collidepoint(self, pos):
        return self._rect.collidepoint(pos)

    def card_at_point(self, pos):
        """
        Return the card from this stack that collides with the point 'pos'. If
        there is none, return None.
        """

        # Note: card_at_point() depends on how the stack is drawn
        # When changing anything here, also check if changes shouldn't be made
        # in draw()

        card_num = len(self._cards_with_missing)

        x = pos[0]
        y = pos[1]

        x -= self._rect.x
        y -= self._rect.y

        a = self.card_height / 5

        if x > self.card_width:
            return None

        i = int(y / a)
        if i >= card_num and i < card_num + 4:
            i = card_num - 1
        if i < 0 or i >= card_num:
            return None
        else:
            return self._cards_with_missing[i]

class Hand:
    def __init__(self, pos, size):
        """
        pos ... (x, y) coordinates
        size ... (x, y) coordinates
        """
        self._rect = pygame.Rect(pos, size)
        self._cards = []

        self._card_height = self._rect.height
        self._card_width = self._card_height / CARD_HEIGHT_WIDTH_RATIO

    def add(self, card):
        self._cards.append(card)

    def remove(self, card):
        self._cards.remove(card)

    def draw(self, surface):
        # Note: card_at_point() depends on how the hand is drawn
        # When changing anything here, also check if changes shouldn't be made
        # in card_at_point()

        pygame.draw.rect(surface, FG_COLOR, self._rect)

        x = self._rect.centerx - len(self._cards) * self._card_width / 2

        for card in self._cards:
            img = card.img
            card_surface = pygame.transform.scale(
                img,
                (self._card_width, self._card_height)
            )
            pos = (
                x,
                self._rect.y
            )
            screen.blit(card_surface, pos)

            x += self._card_width

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
                 (self._rect.w - self._card_width * card_num) / 2
        hand_y = self._rect.y

        x -= hand_x
        y -= hand_y

        i = int(x / self._card_width)
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
            False,
            TEXT_COLOR
        )

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
        surface.blit(self._text_surface, self._rect.topleft)

    def collidepoint(self, pos):
        return self._rect.collidepoint(pos)

class EndTurnButton:
    def __init__(self, pos, size, font):
        self._rect = pygame.Rect(pos, size)
        self._font = font

        self._active = False
        self._player = 1

        self._text_surface1 = None
        self._text_surface2 = None
        self._update_text()

    def _update_text(self):
        text1 = f"Hraje hrac {self._player}"
        text2 = "Predat tah" if self._active else ""
        self._text_surface1 = self._font.render(
            text1,
            False,
            TEXT_COLOR
        )
        self._text_surface2 = self._font.render(
            text2,
            False,
            TEXT_COLOR
        )

    def activate(self):
        self._active = True
        self._update_text()

    def deactivate(self):
        self._active = False
        self._update_text()

    def set_player(self, player):
        self._player = player
        self._update_text()

    def draw(self, surface):
        color = FG_COLOR if self._active else BG_COLOR
        pygame.draw.rect(surface, color, self._rect)
        surface.blit(
                self._text_surface1,
                (self._rect.x, self._rect.y)
        )
        surface.blit(
                self._text_surface2,
                (self._rect.x, self._rect.y + self._text_surface1.get_height())
        )

    def collidepoint(self, pos):
        return self._rect.collidepoint(pos)


#########
# SETUP #
#########

pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
deck_img = pygame.image.load("karta.png") # TODO

# Load card images
card_imgs = {}
for color in COLORS:
    card_imgs[color] = {}
    for rank in RANKS:
        # TODO Nejak chytreji
        card_imgs[color][rank] = pygame.image.load(
            "cards/card_" + str(((RANKS.index(rank) + 1) % len(RANKS)) + 1) + "_" + color + ".png"
        )
missing_img = pygame.image.load("karta.png") # TODO

missing_card = Card(SPECIAL_COLOR, RANKS[0], missing_img)

# Setup font
font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)

# Setup board
pickup_width = HAND_PX_HEIGHT * 3 / 4
# The bottom player
pickup1 = PickUpArea(
        (0, SCREEN_SIZE[1] - HAND_PX_HEIGHT),
        (pickup_width, HAND_PX_HEIGHT)
)
hand1 = Hand(
        (pickup_width + STACK_PX_MARGINS, SCREEN_SIZE[1] - HAND_PX_HEIGHT),
        (SCREEN_SIZE[0] - pickup_width, HAND_PX_HEIGHT)
)
# The top player
pickup2 = PickUpArea(
        (0, 0),
        (pickup_width, HAND_PX_HEIGHT)
)
hand2 = Hand(
        (pickup_width + STACK_PX_MARGINS, 0),
        (SCREEN_SIZE[0] - pickup_width, HAND_PX_HEIGHT)
)

stack_width = (SCREEN_SIZE[0] - (COLUMNS_OF_STACKS + 1) * STACK_PX_MARGINS) / \
                COLUMNS_OF_STACKS
stack_height = (SCREEN_SIZE[1] - HAND_PX_HEIGHT * 2 - \
                (ROWS_OF_STACKS + 1) * STACK_PX_MARGINS) / \
                ROWS_OF_STACKS
# The middle of the board
stacks = []
for col in range(COLUMNS_OF_STACKS - 1): # The -1 is to make space for the deck
    for row in range(ROWS_OF_STACKS):
        x = (col + 1) * STACK_PX_MARGINS + col * stack_width
        y = HAND_PX_HEIGHT + (row + 1) * STACK_PX_MARGINS + row * stack_height
        stacks.append(Stack((x, y), (stack_width, stack_height)))

deck_width = stack_width
deck_height = stack_width * CARD_HEIGHT_WIDTH_RATIO
deck_x = (COLUMNS_OF_STACKS - 1) * deck_width + \
        COLUMNS_OF_STACKS * STACK_PX_MARGINS
deck_y = (SCREEN_SIZE[1] - deck_height) / 2 # Center
deck = Deck(
        (deck_x, deck_y),
        (deck_width, deck_height),
        card_imgs,
        deck_img,
        font
)
button_width = stack_width
button_height = (stack_height - deck_height) / 2 - STACK_PX_MARGINS
button_x = deck_x
button_y = deck_y + deck_height + STACK_PX_MARGINS
end_turn_button = EndTurnButton(
        (button_x, button_y),
        (button_width, button_height),
        font
)

# Put starting cards into players' hands
for i in range(STARTING_HAND_NUM_CARDS):
    card = deck.pop()
    hand1.add(card)
    card = deck.pop()
    hand2.add(card)

# DEBUG
#stacks[0].add(Card("heart", "Q", card_imgs["heart"]["Q"]))
#hand1.add(Card("clover", "5", card_imgs["clover"]["5"]))
end_turn_button.activate()


#############
# GAME LOOP #
#############

player = 1 # 1 or 2
pickup = pickup1
hand = hand1

clock = pygame.time.Clock()
while True:
    # Process player inputs.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        if event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()

            if deck.collidepoint(pos):
                # Draw a card from the deck
                card = deck.pop()
                hand.add(card)
                # End turn TODO nějak chytřeji
                if pickup.has_card():
                    card = pickup.pop()
                    hand.add(card)
                if player == 1:
                    player = 2
                    pickup = pickup2
                    hand = hand2
                else:
                    player = 1
                    pickup = pickup1
                    hand = hand1
                end_turn_button.set_player(player)
            elif end_turn_button.collidepoint(pos):
                # End turn
                if pickup.has_card():
                    card = pickup.pop()
                    hand.add(card)
                if player == 1:
                    player = 2
                    pickup = pickup2
                    hand = hand2
                else:
                    player = 1
                    pickup = pickup1
                    hand = hand1
                end_turn_button.set_player(player)
            else:
                if pickup.has_card():
                    if hand.collidepoint(pos):
                        card = pickup.pop()
                        hand.add(card)
                    else:
                        for stack in stacks:
                            if stack.collidepoint(pos):
                                card = pickup.pop()
                                stack.add(card)
                else:
                    if hand.collidepoint(pos):
                        card = hand.card_at_point(pos)
                        if card:
                            hand.remove(card)
                            pickup.put(card)
                    else:
                        for stack in stacks:
                            if stack.collidepoint(pos):
                                card = stack.card_at_point(pos)
                                if card:
                                    stack.remove(card)
                                    pickup.put(card)

    # Logic updates.

    # Render.
    screen.fill(BG_COLOR)
    pickup1.draw(screen)
    hand1.draw(screen)
    pickup2.draw(screen)
    hand2.draw(screen)
    for stack in stacks:
        stack.draw(screen)
    deck.draw(screen)
    end_turn_button.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
