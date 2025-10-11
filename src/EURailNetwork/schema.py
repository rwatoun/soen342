import unicodedata

# this is the dictionary that presents the mapping of the days of the week to integers
D3 = {"MON":0,"TUE":1,"WED":2,"THU":3,"FRI":4,"SAT":5,"SUN":6}

# this method helps parsing the days of operation
def _strip_accents_upper(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.strip())
    return "".join(ch for ch in s if not unicodedata.combining(ch)).upper()

# this method is used to parse the days of operation field in three scenarios
def parse_days(s: str):
    raw = s.strip()
    if not raw:
        raise ValueError("Empty days_of_operation")
    
    # when the days of operations are daily
    if raw.lower() == "daily":
        return frozenset(range(7))
    
    # when there are consecutive days during which the connection operates
    if "-" in raw and "," not in raw:
        a,b = ( _strip_accents_upper(t)[:3] for t in raw.split("-",1) )
        ai, bi = D3[a], D3[b]
        seq = list(range(ai, bi+1)) if ai <= bi else list(range(ai,7))+list(range(0,bi+1))
        return frozenset(seq)
    
    # when there are specific days for operations
    sep = "|" if "|" in raw else ","
    toks = [ _strip_accents_upper(t)[:3] for t in raw.split(sep) if t.strip() ]
    return frozenset(D3[t] for t in toks)

# this method parses the prices for both the first and the second class
def parse_price_int(s: str) -> int:
    t = s.strip().replace(",","").replace(" ", "")
    if t == "": raise ValueError("Empty price")
    n = int(t)
    if n < 0: raise ValueError("Negative price")
    return n
