import typing as t

FILE_HEADER_LINE_PREFIX = "##"
NULL_VALUE__NA = "NA"
NULL_VALUE__NAN = "NAN"
NULL_VALUE__NAN_CASED = "NaN"
NULL_VALUE__N_SLASH_A = "N/A"
NULL_VALUE__NULL = "NULL"
NULL_VALUE__EMPTY = ""


def get_null_values() -> t.List[str]:
    nulls = [
        NULL_VALUE__EMPTY,
        NULL_VALUE__NULL,
        NULL_VALUE__NA,
        NULL_VALUE__NAN,
        NULL_VALUE__NAN_CASED,
        NULL_VALUE__N_SLASH_A,
    ]
    return nulls.copy()


def get_null_values__all_cases() -> t.List:
    nulls = get_null_values()
    nulls__all_cases = transform_to_many_cases(nulls)
    return nulls__all_cases.copy()


def transform_to_many_cases(values: t.Iterable[str]) -> t.List[str]:
    funcs = [
        lambda x: x,  # do nothing - preserve case
        str.lower,
        str.upper,
        str.title,
    ]
    values__all_cases = [func(value) for value in values for func in funcs]
    return values__all_cases
