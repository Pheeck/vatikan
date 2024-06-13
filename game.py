"""
The Game class

This file contains the main class of this program.
"""

import pygame
import pygame.image
import pygame.font
from random import randint

from config import *
from card import Card
import widgets
import ai

class Game:
    def __init__(self, gamemode, screen, deck_img, card_imgs):
        self.gamemode = gamemode
        self.screen = screen

        # Setup font
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
        self.medium_font = pygame.font.SysFont(FONT_NAME, MEDIUM_FONT_SIZE)
        self.big_font = pygame.font.SysFont(FONT_NAME, BIG_FONT_SIZE)

        # Setup board
        pickup_width = HAND_PX_HEIGHT * 3 / 4
        # The bottom player
        self.pickup1 = widgets.PickUpArea(
                (0, SCREEN_SIZE[1] - HAND_PX_HEIGHT),
                (pickup_width, HAND_PX_HEIGHT)
        )
        self.hand1 = widgets.Hand(
                (pickup_width + STACK_PX_MARGINS, SCREEN_SIZE[1] - HAND_PX_HEIGHT),
                (SCREEN_SIZE[0] - pickup_width, HAND_PX_HEIGHT),
                False
        )
        # The top player
        self.pickup2 = widgets.PickUpArea(
                (0, 0),
                (pickup_width, HAND_PX_HEIGHT)
        )
        self.hand2 = widgets.Hand(
                (pickup_width + STACK_PX_MARGINS, 0),
                (SCREEN_SIZE[0] - pickup_width, HAND_PX_HEIGHT),
                gamemode == PLAYER_VS_AI,
                deck_img
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
                                                 (stack_width, stack_height)))

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
                self.medium_font
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
        if self.pickup.has_card():
            valid &= not self.pickup.get().is_frozen()
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
        s = self.big_font.render(f"HRAC {player} VYHRAL", True, TEXT_COLOR)
        x = self.screen.get_width() / 2 - s.get_width() / 2
        y = self.screen.get_height() / 2 - s.get_height() / 2
        self.win_screen.blit(s, (x, y))

    def end_turn(self):
        """
        End turn

        Checks if the current hand isn't empty, possibly choosing the current
        player as winner. Then switches the players. Finally, freezes cards on
        the board.
        """

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
        print(f"\nPlayer {self.player}")

        # Freeze all cards on the board
        for stack in self.stacks:
            stack.freeze()

    def update_end_turn_button(self):
        if self.board_is_valid():
            self.end_turn_button.set_board_valid()
        else:
            self.end_turn_button.unset_board_valid()
        if self.board_is_frozen() and not self.deck.is_empty():
            self.end_turn_button.set_card_draw_needed()
        else:
            self.end_turn_button.unset_card_draw_needed()

        if self.gamemode == AI_VS_AI:
            player = BOT1_NAME if self.player == 1 else BOT2_NAME
            self.end_turn_button.set_player_name(player)
        else:
            self.end_turn_button.set_player_name(f"hrac {self.player}")

    ###################################
    # API FOR MANIPULATING GAME STATE #
    ###################################

    def try_end_turn(self):
        """
        Try to end the turn. This can have 3 results:
        - The turn just ends
        - The current player draws a card and the turn ends
        - The turn doesn't end

        If there is a card in pickup area, we put it into the hand. If that
        isn't possible, the turn cannot end.

        If the turn ends, return True, otherwise return False
        """
        if self.pickup.has_card():
            if not self.try_put_card_into_hand():
                return False

        if self.board_is_valid():
            if self.board_is_frozen():
                if not self.deck.is_empty():
                    # Draw a card first
                    card = self.deck.pop()
                    self.hand.add(card)
                self.end_turn()
                self.update_end_turn_button()
            else:
                self.end_turn()
                self.update_end_turn_button()
            return True
        return False

    def try_take_card_from_stack(self, card, stack):
        """
        Try to take a given card from a given stack widget and put it into the
        pickup area.

        Returns True on success, otherwise False
        """
        if self.pickup.has_card() or not stack.has_card(card):
            return False
        stack.remove(card)
        self.pickup.put(card)
        self.update_end_turn_button()
        return True

    def try_take_card_from_hand(self, card):
        """
        Try to take a given card from hand and put it into the pickup area.

        Returns True on success, otherwise False
        """
        if self.pickup.has_card() or not self.hand.has_card(card):
            return False
        self.hand.remove(card)
        self.pickup.put(card)
        self.update_end_turn_button()
        return True

    def try_put_card_onto_stack(self, stack):
        """
        Try to take the card in the pickup area and put it onto a given stack.

        Returns True on success, otherwise False
        """
        if not self.pickup.has_card():
            return False
        stack.add(self.pickup.pop())
        self.update_end_turn_button()
        return True

    def try_put_card_into_hand(self):
        """
        Try to take the card in the pickup area and put it into hand.

        Returns True on success, otherwise False
        """
        if not self.pickup.has_card() or self.pickup.get().is_frozen():
            return False
        self.hand.add(self.pickup.pop())
        self.update_end_turn_button()
        return True

    def find_stack_containing_cards(self, cards):
        """
        Try to find a Stack widget containing exactly Card objects present in
        the given cards list. Assume no card is present twice in the cards
        list. Assume that for each Stack widget, no card is present twice in
        it.

        Return the Stack widget on success or None on failure.
        """
        for stack in self.stacks:
            if len(cards) != stack.size():
                continue

            this_one = True
            for card in cards:
                if not stack.has_card(card):
                    this_one = False
                    break

            if this_one:
                return stack

        return None

    def get_random_empty_stack(self):
        """
        Return a random empty Stack widget or None if there aren't any.
        """
        empty_stacks = [s for s in self.stacks if s.is_empty()]
        return empty_stacks[randint(0, len(empty_stacks) - 1)]

    def get_state_copy(self):
        """
        Return a tuple representing the current state of the game. 

        (
            set of Cards in hand
            set of *nonempty* stacks {
                stack1 (tuple of Cards),
                stack2 (tuple of Cards),
                ...
            }
        )

        Intended for use in AI.
        """
        hand = self.hand.get_state_copy()

        stacks = set()
        for stack in self.stacks:
            s = stack.get_state_copy()
            if s:
                stacks.add(s)

        return (hand, stacks)

    #####################################
    # MOUSE, DRAWING AND MAIN GAME LOOP #
    #####################################

    def process_mouse_click(self, pos):
        if self.end_turn_button.collidepoint(pos):
            self.try_end_turn()
        else:
            if self.pickup.has_card(): # From pickup
                if self.hand.collidepoint(pos):
                    self.try_put_card_into_hand()
                else:
                    for stack in self.stacks:
                        if stack.collidepoint(pos):
                            self.try_put_card_onto_stack(stack)
                            break
            else: # To pickup
                if self.hand.collidepoint(pos):
                    card = self.hand.card_at_point(pos)
                    if card:
                        self.try_take_card_from_hand(card)
                else:
                    for stack in self.stacks:
                        if stack.collidepoint(pos):
                            card = stack.card_at_point(pos)
                            if card:
                                self.try_take_card_from_stack(card, stack)

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

        self.update_end_turn_button()

        self.draw()

        clock = pygame.time.Clock()
        ai_timer_running = False
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if self.gamemode == PLAYER_VS_PLAYER:
                        self.process_mouse_click(pos)
                    elif self.gamemode == PLAYER_VS_AI:
                        if self.player == 1:
                            self.process_mouse_click(pos)
                    else: # gamemode AI_VS_AI
                        pass
                if event.type == pygame.USEREVENT:
                    ai_timer_running = False
                    moves = ai.generate_moves(self)
                    ai.print_moves(moves)
                    ai.apply_moves(moves, self)

            if self.gamemode == PLAYER_VS_AI and self.player == 2:
                moves = ai.generate_moves(self)
                ai.print_moves(moves)
                ai.apply_moves(moves, self)

            if self.gamemode == AI_VS_AI \
                    and not ai_timer_running \
                    and self.winner is None:
                event = pygame.event.Event(pygame.USEREVENT)
                pygame.time.set_timer(event, AI_VS_AI_TURN_DELAY, loops=1)
                ai_timer_running = True

            self.draw()
            clock.tick(FPS)
