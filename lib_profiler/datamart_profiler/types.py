from datetime import datetime
import dateutil.parser
import dateutil.tz
import re
import unittest

from datamart_core.common import Type


_re_int = re.compile(r'^[+-]?[0-9]+$')
_re_float = re.compile(r'^[+-]?'
                       r'(?:'
                       r'(?:[0-9]+\.[0-9]*)|'
                       r'(?:\.[0-9]+)'
                       r')'
                       r'(?:[Ee][0-9]+)?$')
_re_phone = re.compile(r'^'
                       r'(?:\+[0-9]{1,3})?'  # Optional country prefix
                       r'(?=(?:[() .-]*[0-9]){6,11}$)'  # 6-11 digits
                       r'(?:[ .]?\([0-9]{3}\))?'  # Area code in parens
                       r'(?:[ .]?[0-9]{1,12})'  # First group of digits
                       r'(?:[ .-][0-9]{1,10}){0,5}'  # More groups of digits
                       r'$')
_re_whitespace = re.compile(r'\s')


# Tolerable ratio of unclean data
MAX_UNCLEAN = 0.02  # 2%


# Maximum number of different values for categorical columns
MAX_CATEGORICAL = 6


_defaults = datetime(1985, 1, 1), datetime(2005, 6, 15)


def parse_date(string):
    try:
        dt1 = dateutil.parser.parse(string, default=_defaults[0])
        dt2 = dateutil.parser.parse(string, default=_defaults[1])
    except Exception:  # ValueError, OverflowError
        return None
    else:
        if dt1 != dt2:
            # It was not a date, just a time; no good
            return None

        # If no timezone was read, assume UTC
        if dt1.tzinfo is None:
            dt1 = dt1.replace(tzinfo=dateutil.tz.UTC)
        return dt1


def identify_types(array, name):
    num_total = len(array)
    ratio = 1.0 - MAX_UNCLEAN

    # Identify structural type
    num_float = num_int = num_bool = num_empty = num_text = 0
    for elem in array:
        if not elem:
            num_empty += 1
        elif _re_int.match(elem):
            num_int += 1
        elif _re_float.match(elem):
            num_float += 1
        elif len(_re_whitespace.findall(elem)) >= 4:
            num_text += 1
        if elem.lower() in ('0', '1', 'true', 'false', 'y', 'n', 'yes', 'no'):
            num_bool += 1

    threshold = ratio * (num_total - num_empty)

    if num_empty == num_total:
        structural_type = Type.MISSING_DATA
    elif num_int >= threshold:
        structural_type = Type.INTEGER
    elif num_int + num_float >= threshold:
        structural_type = Type.FLOAT
    else:
        structural_type = Type.TEXT

    semantic_types_dict = {}

    # Identify booleans
    if num_bool >= threshold:
        semantic_types_dict[Type.BOOLEAN] = None

    if structural_type == Type.TEXT:
        if num_text >= threshold:
            # Free text
            semantic_types_dict[Type.TEXT] = None
        else:
            # Count distinct values
            values = set()
            for elem in array:
                if elem not in values:
                    values.add(elem)
                    if len(values) > MAX_CATEGORICAL:
                        break
            else:
                semantic_types_dict[Type.CATEGORICAL] = values
    elif structural_type == Type.INTEGER:
        # Identify ids
        # TODO: is this enough?
        # TODO: what about false positives?
        if (name.lower().startswith('id') or
                name.lower().endswith('id') or
                name.lower().startswith('identifier') or
                name.lower().endswith('identifier') or
                name.lower().startswith('index') or
                name.lower().endswith('index')):
            semantic_types_dict[Type.ID] = None

    # Identify lat/long
    num_lat = num_long = 0
    if structural_type == Type.FLOAT:
        for elem in array:
            try:
                elem = float(elem)
            except ValueError:
                pass
            else:
                if -180.0 <= float(elem) <= 180.0:
                    num_long += 1
                    if -90.0 <= float(elem) <= 90.0:
                        num_lat += 1

        if num_lat >= threshold and 'lat' in name.lower():
            semantic_types_dict[Type.LATITUDE] = None
        if num_long >= threshold and 'lon' in name.lower():
            semantic_types_dict[Type.LONGITUDE] = None

    # Identify dates
    if structural_type == Type.TEXT:
        parsed_dates = []
        for elem in array:
            elem = parse_date(elem)
            if elem is not None:
                parsed_dates.append(elem)

        if len(parsed_dates) >= threshold:
            semantic_types_dict[Type.DATE_TIME] = parsed_dates

    # Identify phone numbers
    num_phones = 0
    for elem in array:
        if _re_phone.match(elem) is not None:
            num_phones += 1

    if num_phones >= threshold:
        semantic_types_dict[Type.PHONE_NUMBER] = None

    return structural_type, semantic_types_dict