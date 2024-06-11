"""
Utility functions

This file contains miscellaneous functions that aren't game-logic-, ui- or ai-
specific.
"""

from card import Card
from config import *

def sorted_by_rank(cards):
    """
    Return the given list of cards (class Card) sorted by rank
    """
    return sorted(cards, key=lambda x: RANKS.index(x.rank))

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

def attempt_construct_flush(cards, missing_card):
    """
    Try to construct a flush (see Note2 for definition) from given cards
    possibly using missing card markers and return the flush. If constructing
    the flush is not possible (there are less than 3 cards, there are multiple
    cards of same rank or not all cards are of the same color), return None.

    Returns a tuple.

    missing_card ... the singleton Card object representing a missing card
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

    return tuple(result)

def sorted_by_flush(stack):
    """
    Given a list/tuple of at least 3 cards which form a cyclic contiguous sequence,
    return the cards in a tuple ordered by the sequence.

    Example:
    IN: K 2 A 4 3
    OUT: K A 2 3 4
    """
    assert len(stack) >= 3

    if is_triplet(stack):
        return tuple(stack)
    else:
        return attempt_construct_flush(stack, None)

def card_to_string(card):
    return str(card.color) + str(card.rank)

def stack_to_string(stack):
    stack = sorted_by_flush(stack)
    l = [card_to_string(c) for c in stack]
    return ", ".join(l)
