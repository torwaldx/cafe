from rapidfuzz import fuzz, utils
from unidecode import unidecode


def are_equivalent(str1, str2, tresh=80.0):
    if get_tr_score(str1, str2) > tresh:
        return True

    return False


def get_tr_score(str1, str2):
    raw_score = get_simple_score(str1, str2)

    tr_str1 = unidecode(str1)
    tr_str2 = unidecode(str2)

    tr_score = get_simple_score(tr_str1, tr_str2)

    return max(raw_score, tr_score)


def get_simple_score(str1, str2):
    processor = utils.default_process
    return fuzz.token_set_ratio(str1, str2, processor=processor)
