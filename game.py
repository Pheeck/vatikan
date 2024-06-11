"""
The Game class

This file contains the main class of this program.
"""

import pygame
import pygame.image
import pygame.font

from config import *
from card import Card
import widgets
import ai

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        deck_img = pygame.image.load(DECK_IMG_FILE)

        # Load card images
        card_imgs = {}
        for color in COLORS:
            card_imgs[color] = {}
            for rank in RANKS:
                # TODO Nejak chytreji
                card_imgs[color][rank] = pygame.image.load(
                    CARDS_DIR + "/card_" + str(((RANKS.index(rank) + 1) % len(RANKS)) + 1) + "_" + color + ".png"
                )
        missing_img = pygame.image.load(DECK_IMG_FILE)

        missing_card = Card(SPECIAL_COLOR, RANKS[0], missing_img)

        # Setup font
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)

        # Setup board
        pickup_width = HAND_PX_HEIGHT * 3 / 4
        # The bottom player
        self.pickup1 = widgets.PickUpArea(
                (0, SCREEN_SIZE[1] - HAND_PX_HEIGHT),
                (pickup_width, HAND_PX_HEIGHT)
        )
        self.hand1 = widgets.Hand(
                (pickup_width + STACK_PX_MARGINS, SCREEN_SIZE[1] - HAND_PX_HEIGHT),
                (SCREEN_SIZE[0] - pickup_width, HAND_PX_HEIGHT)
        )
        # The top player
        self.pickup2 = widgets.PickUpArea(
                (0, 0),
                (pickup_width, HAND_PX_HEIGHT)
        )
        self.hand2 = widgets.Hand(
                (pickup_width + STACK_PX_MARGINS, 0),
                (SCREEN_SIZE[0] - pickup_width, HAND_PX_HEIGHT)
        )

        stack_width = (SCREEN_SIZE[0] - (COLUMNS_OF_STACKS + 1) * STACK_PX_MARGINS) / \
                        COLUMNS_OF_STACKS
        stack_height = (SCREEN_SIZE[1] - HAND_PX_HEIGHT * 2 - \
                        (ROWS_OF_STACKS + 1) * STACK_PX_MARGINS) / \
                        ROWS_OF_STACKS
        # The middle of the board
        self.stacks = []
        for col in range(COLUMNS_OF_STACKS - 1): # The -1 is to make space for the deck
            for row in range(ROWS_OF_STACKS):
                x = (col + 1) * STACK_PX_MARGINS + col * stack_width
                y = HAND_PX_HEIGHT + (row + 1) * STACK_PX_MARGINS + row * stack_height
                self.stacks.append(widgets.Stack((x, y),
                                                 (stack_width, stack_height),
                                                 missing_card))

        deck_width = stack_width
        deck_height = stack_width * CARD_HEIGHT_WIDTH_RATIO
        deck_x = (COLUMNS_OF_STACKS - 1) * deck_width + \
                COLUMNS_OF_STACKS * STACK_PX_MARGINS
        deck_y = (SCREEN_SIZE[1] - deck_height) / 2 # Center
        self.deck = widgets.Deck(
                (deck_x, deck_y),
                (deck_width, deck_height),
                card_imgs,
                deck_img,
                self.font
        )
        button_width = stack_width
        button_height = (stack_height - deck_height) / 2 - STACK_PX_MARGINS
        button_x = deck_x
        button_y = deck_y + deck_height + STACK_PX_MARGINS
        self.end_turn_button = widgets.EndTurnButton(
                (button_x, button_y),
                (button_width, button_height),
                self.font
        )

        # Put starting cards into players' hands
        for i in range(STARTING_HAND_NUM_CARDS):
            card = self.deck.pop()
            self.hand1.add(card)
            card = self.deck.pop()
            self.hand2.add(card)

        # DEBUG
        #self.stacks[0].add(Card("heart", "Q", card_imgs["heart"]["Q"]))
        #self.hand1.add(Card("clover", "5", card_imgs["clover"]["5"]))
        self.end_turn_button.set_board_valid()

        self.winner = None

        self.win_screen = self.screen.copy()
        self.win_screen.fill(FG_COLOR)
        self.win_screen.set_alpha(255 * 0.60)

    def board_is_valid(self):
        valid = True
        for stack in self.stacks:
            valid &= stack.is_valid()
        return valid

    def board_is_frozen(self):
        """
        Does the board contain only frozen cards (No new card was put on the board
        this turn)?
        """
        frozen = True
        for stack in self.stacks:
            frozen &= stack.is_frozen()
        return frozen

    def select_winner(self, player):
        self.winner = player
        s = self.font.render(f"Player {player} won", True, TEXT_COLOR)
        x = self.screen.get_width() / 2 - s.get_width() / 2
        y = self.screen.get_height() / 2 - s.get_height() / 2
        self.win_screen.blit(s, (x, y))

    def end_turn(self):
        if self.pickup.has_card():
            card = self.pickup.pop()
            self.hand.add(card)

        if self.winner is None and self.hand.is_empty():
            self.select_winner(self.player)

        if self.player == 1:
            self.player = 2
            self.pickup = self.pickup2
            self.hand = self.hand2
        else:
            self.player = 1
            self.pickup = self.pickup1
            self.hand = self.hand1

        # Freeze all cards on the board
        for stack in self.stacks:
            stack.freeze()

        self.end_turn_button.set_player(self.player)

        print(f"\nPlayer {self.player}") # DEBUG
        ai_moves = ai.generate_moves(self)
        ai.print_moves(ai_moves) # DEBUG

    def process_mouse_click(self, pos):
        if self.end_turn_button.collidepoint(pos):
            # Ending the turn
            if self.board_is_valid():
                if self.board_is_frozen():
                    if not self.deck.is_empty():
                        card = self.deck.pop()
                        self.hand.add(card)
                        self.end_turn()
                else:
                    self.end_turn()
        else:
            if self.pickup.has_card():
                if self.hand.collidepoint(pos):
                    # Deselecting a card from the hand
                    card = self.pickup.get()
                    if not card.is_frozen():
                        self.hand.add(card)
                        self.pickup.pop()
                else:
                    # Putting a card onto a stack
                    for stack in self.stacks:
                        if stack.collidepoint(pos):
                            card = self.pickup.pop()
                            stack.add(card)
            else:
                if self.hand.collidepoint(pos):
                    # Selecting a card from the hand
                    card = self.hand.card_at_point(pos)
                    if card:
                        self.hand.remove(card)
                        self.pickup.put(card)
                else:
                    # Selecting a card from a stack
                    for stack in self.stacks:
                        if stack.collidepoint(pos):
                            card = stack.card_at_point(pos)
                            if card:
                                stack.remove(card)
                                self.pickup.put(card)

        if self.board_is_valid():
            self.end_turn_button.set_board_valid()
        else:
            self.end_turn_button.unset_board_valid()
        if self.board_is_frozen():
            if self.deck.is_empty():
                self.end_turn_button.unset_card_draw_needed()
                self.end_turn_button.unset_board_valid()
            else:
                self.end_turn_button.set_card_draw_needed()
        else:
            self.end_turn_button.unset_card_draw_needed()

    def draw(self):
        self.screen.fill(BG_COLOR)

        self.pickup1.draw(self.screen)
        self.hand1.draw(self.screen)
        self.pickup2.draw(self.screen)
        self.hand2.draw(self.screen)
        for stack in self.stacks:
            stack.draw(self.screen)
        self.deck.draw(self.screen)
        self.end_turn_button.draw(self.screen)

        if self.winner is not None:
            self.screen.blit(self.win_screen, (0, 0))

        pygame.display.flip()

    def run(self):
        self.player = 1 # 1 or 2
        self.pickup = self.pickup1
        self.hand = self.hand1

        self.draw()

        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    pos = pygame.mouse.get_pos()
                    self.process_mouse_click(pos)
            self.draw()
            clock.tick(FPS)
