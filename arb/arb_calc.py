from classes import Bookie
MAXX_MARGIN = 6.0
def find_best_odds(books: dict[int, Bookie], num_odds: int) -> tuple[float, list[Bookie]]:
    bookie_array = [book for book in books.values() if all(o > 0 for o in book.odds) and not book.traded]
    ret_bookies = []
    # not enough books online
    if len(bookie_array) < num_odds:
        return (MAXX_MARGIN, ret_bookies)

    n = len(bookie_array)

    best_margin = MAXX_MARGIN
    if num_odds == 2:
        for i in range(n):
            for j in range(n):
                if i != j:
                    curr_margin = calc_arb([bookie_array[i], bookie_array[j]])
                    if curr_margin < best_margin:
                        best_margin = curr_margin
                        ret_bookies = [bookie_array[i], bookie_array[j]]

    elif num_odds == 3:
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    if i != j and i != k and k != j:
                        curr_margin = calc_arb([bookie_array[i], bookie_array[j], bookie_array[k]])
                        if curr_margin < best_margin:
                            best_margin = curr_margin
                            ret_bookies = [bookie_array[i], bookie_array[j], bookie_array[k]]

    return (best_margin, ret_bookies)
# look into how bonus work, how to set up the classes etc.
# this gives us the house edge, the smaller the number the better, if its a negative num then we have an arb
def calc_arb(books: list[Bookie]) -> float:
    """books[i] is the bookie chosen for outcome i."""
    inv_sum = 0
    for i in range(len(books)):
        inv_sum += (1 - books[i].loss_back)/ (books[i].odds[i] - books[i].loss_back)
    return round((inv_sum - 1) * 100, 2)
