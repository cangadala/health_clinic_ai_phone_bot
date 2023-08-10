import re 

def ordinal(num: int) -> str:
    """Return number with ordinal string."""
    if 10 <= num % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
    return f"{num}{suffix}"


def strip_punctuation(s):
    return re.sub(r'[^\w\s]', '', s)