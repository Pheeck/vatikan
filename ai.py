"""
AI for the game.

This file contains the logic behind AI and functions (called from the Game
class) to
- Given a state of the game, let the AI generate moves
- Given moves, print them in human-readable form onto stdout
- Given moves and access to the game state, apply the moves
"""

import itertools

from config import *
from card import Card
import util
import widgets


######################
# INTERNAL FUNCTIONS #
######################

def print_stack_suggestion(stack, *from_stacks):
    """ 
    Print a suggestion to create a new stack. Optionally specify that some of
    the cards should be taken from existing stacks.
    """
    print("Suggested move: Put a new stack " +
          f"{util.stack_to_string(stack)} on the board")
    if from_stacks:
        print("Use cards from stacks " +
              f'{"; ".join([util.stack_to_string(s) for s in from_stacks])}')

def print_card_suggestion(card, stack):
    """
    Print a suggestion to add a card from hand to a stack.
    """
    print("Suggested move: Add card " +
          f"{util.card_to_string(card)} to " +
          f"the stack {util.stack_to_string(stack)}")

def get_subsets(x, n):
    """
    Return set of all n-element subsets of x (subsets represented as lists)
    """
    return set(itertools.combinations(x, n))

def get_big_stacks(stacks):
    """
    Filter stacks so that only big stacks remain. Big stacks are stacks of 4
    cards or more.
    """
    return [s for s in stacks if len(s) >= 4]

def is_valid_stack(cards):
    mock_stack = widgets.Stack((0, 0), (0, 0), None)
    mock_stack._cards = cards
    mock_stack.reconstruct()
    return mock_stack.is_valid()

def is_full_stack(stack):
    return len(stack) == len(RANKS)


##########
# AI API #
##########

def suggest_move(game):
    print(f"Player: {game.player}")

    # Represent everything by just lists and sets

    # Get stacks. Only nonempty ones. Make copies of the stacks so that the AI
    # computations don't interfere with the game. Make sure the stacks are
    # sorted.
    stacks = []
    for s in game.stacks:
        if s._cards:
            stacks.append(util.sorted_by_flush(s._cards))

    # Get big stacks (stacks of 4 cards or more)
    big_stacks = get_big_stacks(stacks)

    # Get hand
    hand = set(game.hand._cards)

    # 1) From cards in hand, try to create as many new stacks as possible

    # 1a) Try to create stacks where all 3 cards are from hand

    # Generate triplets. If one of them is valid, remove its cards from hand
    # and generate new triplets which won't contain the removed cards. Do this
    # until no valid triplet is found in hand.
    found_a_move = True
    while found_a_move:
        found_a_move = False

        triplets = get_subsets(hand, 3)
        for triplet in triplets:
            if found_a_move:
                break

            if is_valid_stack(triplet):
                # Found a valid move!
                print_stack_suggestion(triplet)
                hand -= set(triplet)
                stacks.append(util.sorted_by_flush(list(triplet)))
                found_a_move = True

    # 1b) Try to create stacks where 2 cards are from hand and 1 is from a big
    # stack

    # Use the same strategy as for 1a but this time use the cartesian product
    # of duplets of cards from hand and big stacks. For each (card1, card2,
    # stack) tuple generate two new stacks (take the first OR the last card of
    # the big stack).
    found_a_move = True
    while found_a_move:
        found_a_move = False

        # It is possible we removed enough cards in the last iteration from a
        # stack for it to stop being big. Recompute big stacks.
        big_stacks = get_big_stacks(stacks)

        card_duplets = get_subsets(hand, 2)
        for card_duplet in card_duplets:
            if found_a_move:
                break

            card_duplet = list(card_duplet)

            for big_stack in big_stacks:
                if found_a_move:
                    break

                stack1 = card_duplet + [big_stack[0]]
                stack2 = card_duplet + [big_stack[-1]]

                for stack in (stack1, stack2):
                    if found_a_move:
                        break

                    if is_valid_stack(stack):
                        # Found a valid move!
                        print_stack_suggestion(stack, big_stack)
                        hand -= set(card_duplet)
                        stacks.append(util.sorted_by_flush(stack))
                        if stack == stack1:
                            big_stack.pop(0)
                        else:
                            big_stack.pop()
                        found_a_move = True

    # 1c) Try to create stacks where 1 card is from hand and 2 cards are from
    # big stacks

    # Use the same strategy as for 1b but the cartesian product is now (card,
    # stack1, stack2) and we generate four possible new stacks.
    found_a_move = True
    while found_a_move:
        found_a_move = False

        # It is possible we removed enough cards in the last iteration from a
        # stack for it to stop being big. Recompute big stacks.
        big_stacks = get_big_stacks(stacks)

        # Copy hand so that we don't get into trouble with deleting from
        # hand while iterating over it
        hand_copy = [c for c in hand]

        # Since stacks are represented by lists and lists are not hashable, we
        # have to work around that using indices
        big_stack_indices = set(range(len(big_stacks)))
        stack_duplets = get_subsets(big_stack_indices, 2)
        for stack_duplet in stack_duplets:
            if found_a_move:
                break

            for card in hand_copy:
                if found_a_move:
                    break

                big_stack1 = big_stacks[stack_duplet[0]]
                big_stack2 = big_stacks[stack_duplet[1]]

                stack1 = [big_stack1[0], big_stack2[0], card]
                stack2 = [big_stack1[0], big_stack2[-1], card]
                stack3 = [big_stack1[-1], big_stack2[0], card]
                stack4 = [big_stack1[-1], big_stack2[-1], card]

                for stack in (stack1, stack2, stack3, stack4):
                    if found_a_move:
                        break

                    if is_valid_stack(stack):
                        # Found a valid move!
                        print_stack_suggestion(stack, big_stack1, big_stack2)
                        hand.remove(card)
                        stacks.append(util.sorted_by_flush(stack))
                        if stack == stack1:
                            big_stack1.pop(0)
                            big_stack2.pop(0)
                        elif stack == stack2:
                            big_stack1.pop(0)
                            big_stack2.pop()
                        elif stack == stack3:
                            big_stack1.pop()
                            big_stack2.pop(0)
                        else:
                            big_stack1.pop()
                            big_stack2.pop()
                        found_a_move = True

    # 2) Try to add cards from hand to existing stacks

    # Try visiting stacks and seeing if any of the cards from hand could be
    # added to them. Keep unvisited stacks in worklist. If a card gets added to
    # a stack, add the stack back to the worklist so that we can check if
    # perhaps another card can be added to it.

    worklist = [s for s in stacks]
    while worklist:
        stack = worklist.pop()

        if is_full_stack(stack):
            continue

        for card in hand:
            if is_valid_stack(stack + [card]):
                # Found a valid move!
                print_card_suggestion(card, stack)
                stack.append(card)
                util.sort_by_flush(stack)
                hand.remove(card)
                worklist.append(stack)
                break

    print("Suggested move: End turn")
