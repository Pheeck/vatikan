"""
Experimental AI for the vatikan game. Looks at game state and prints suggested
moves into standard output.
"""

import itertools
import __main__ as vatikan

MAX_DEPTH = 4
# Na hodnotu 5 se uz v early game musi cekat, je nepouzitelna

def stack_to_string(stack):
    # TODO sort
    l = [str(c.color) + str(c.rank) for c in stack]
    return ", ".join(l)

def find_subsets(x, n):
    """
    Return set of all n-element subsets of x (subsets represented as lists)
    """
    return set(itertools.combinations(x, n))

def possible_sums(n, k):
    """
    Return a list of all possible k-tuples of numbers >= 1 that sum up to n.

    For example: n = 3, k = 2 -> [(1,2), (2,1)]
    """
    assert k >= 1
    assert n >= k

    if k == 1:
        return [[n]]

    result = []

    for t in itertools.combinations(range(n - 1), k - 1):
        sum_ = [t[0] + 1]
        i = 0
        while i < len(t) - 1:
            a = t[i]
            b = t[i + 1]
            sum_.append(b - a)
            i += 1
        sum_.append(n - 1 - t[-1])
        result.append(sum_)

    return result

def find_groupings_internal(x, group_sizes):
    if not group_sizes:
        return [[]]

    result = []

    k = group_sizes[0]
    group_sizes1 = group_sizes[1:]
    for group in find_subsets(x, k):
        x1 = set(x) - set(group)
        for grouping in find_groupings_internal(x1, group_sizes1):
            result.append([group] + grouping)

    return result

def find_groupings(x, n):
    """
    Return set of all possible groupings of elements of x into n groups where
    each group has at least one element.
    """
    result = []

    for group_sizes in possible_sums(len(x), n):
        result += find_groupings_internal(x, group_sizes)

    return result

def is_valid_stack(cards):
    mock_stack = vatikan.Stack((0, 0), (0, 0), None)
    mock_stack._cards = cards
    mock_stack.reconstruct()
    return mock_stack.is_valid()

def suggest_move(game):
    print(f"Player: {game.player}")

    # Represent everything by just lists and sets

    # Get stacks (only the nonempty ones)
    stacks = []
    for s in game.stacks:
        if s._cards:
            stacks.append(s._cards)

    # Get hand
    hand = set(game.hand._cards)

    # All pairs (stack, card)
    board = []
    for stack in stacks:
        for card in stack:
            board.append((stack, card))

    # 1) From cards in hand, try to create as many new stacks as possible
    foo = True
    while foo:
        foo = False
        for triplet in find_subsets(hand, 3):
            if is_valid_stack(triplet):
                print("Suggested move: Put a new stack " +
                      f"{stack_to_string(triplet)} on the board")

                hand -= set(triplet)
                stacks.append(triplet)
                foo = True
                break

    # 2) Try to put as many cards on the board as possible (capped by
    # MAX_DEPTH) without creating new stacks
    #
    # n ... how many cards to put on the board
    # k ... to how many different stacks

    # Decide how many cards to put on the board
    for n in range(MAX_DEPTH, 0, -1):
        # Select cards to put on the board
        for hand_subset in find_subsets(hand, n):
            # Decide how many stacks to put cards into
            for k in range(1, min(n, len(stacks)) + 1):
                # Decide how to split cards between the stacks
                for grouping in find_groupings(hand_subset, k):
                    # Select stacks to put the cards into
                    for stack_subset in find_subsets(range(len(stacks)), k):
                        # We have now instantiated all variables. Now check,
                        # that this is a correct solution

                        correct = True
                        for cards, stack_i in zip(grouping, stack_subset):
                            stack = stacks[stack_i]
                            new_stack = list(stack) + list(cards)
                            correct &= is_valid_stack(new_stack)

                        # If the solution is correct, print it to the player
                        # and stop searching for new solutions
                        if correct:
                            for cards, stack_i in zip(grouping, stack_subset):
                                stack = stacks[stack_i]
                                new_stack = list(stack) + list(cards)
                                diff = set(new_stack) - set(stack)
                                print("Suggested move: Add cards " +
                                      f"{stack_to_string(diff)} to " +
                                      f"the stack {stack_to_string(stack)}")
                            print("Suggested move: End turn")
                            return

    print("Suggested move: End turn")

def suggest_move_advanced(game):
    print(f"Player: {game.player}")

    # Represent everything by just lists and sets

    # Get stacks (only the nonempty ones)
    stacks = []
    for s in game.stacks:
        if s._cards:
            stacks.append(s._cards)

    # Get hand
    hand = set(game.hand._cards)

    # All pairs (stack, card)
    board = []
    for stack in stacks:
        for card in stack:
            board.append((stack, card))

    # 1) From cards in hand, try to create as many new stacks as possible
    foo = True
    while foo:
        foo = False
        for triplet in find_subsets(hand, 3):
            if is_valid_stack(triplet):
                print("Suggested move: Put a new stack " +
                      f"{stack_to_string(triplet)} on the board")

                hand -= set(triplet)
                stacks.append(triplet)
                foo = True
                break

    # 2) Try to put as many cards on the board as you can (without creating new
    # stacks). Total number of cards moved (n + m) is capped by MAX_DEPTH.
    #
    # m ... how many cards to lift from the board
    # n ... how many cards to put on the board from hand
    # N ... m + n
    # k ... place cards to how many different stacks

    # Decide how many cards to try to move
    for N in range(MAX_DEPTH, 0, -1):
        # Decide how many of these are frozen cards (0 .. N - 1)
        for m in range(1):
            n = N - m
            # Select frozen cards to lift from the board
            for board_subset in find_subsets(board, m):
                cards_to_place = []
                # Lift the cards
                for stack, card in board_subset:
                    cards_to_place.append(card)
                    stack.remove(card)

                # Select cards from hand to put on the board
                for hand_subset in find_subsets(hand, n):
                    # We'll be placing both the lifted cards and the cards from
                    # hand
                    cards_to_place += hand_subset

                    # Decide how many stacks to put cards into
                    for k in range(1, min(N, len(stacks)) + 1):
                        # Decide how to split cards between the stacks
                        for grouping in find_groupings(cards_to_place, k):
                            # Select stacks to put the cards into
                            for stack_subset in find_subsets(range(len(stacks)), k):
                                # We have now instantiated all variables. Now check,
                                # that this is a correct solution

                                correct = True
                                for cards, stack_i in zip(grouping, stack_subset):
                                    stack = stacks[stack_i]
                                    new_stack = list(stack) + list(cards)
                                    correct &= is_valid_stack(new_stack)

                                # If the solution is correct, print it to the player
                                # and stop searching for new solutions
                                if correct:
                                    for stack, card in board_subset:
                                        print("Suggested move: Lift card " +
                                              f"{stack_to_string([card])} from " +
                                              "the stack " +
                                              f"{stack_to_string(full_stack)}")
                                    for cards, stack_i in zip(grouping, stack_subset):
                                        stack = stacks[stack_i]
                                        new_stack = list(stack) + list(cards)
                                        diff = set(new_stack) - set(stack)
                                        print("Suggested move: Add cards " +
                                              f"{stack_to_string(diff)} to " +
                                              f"the stack {stack_to_string(stack)}")
                                    print("Suggested move: End turn")
                                    return

                # Return the lifted frozen cards
                for (stack, card) in board_subset:
                    stack.append(card)

    print("Suggested move: End turn")
