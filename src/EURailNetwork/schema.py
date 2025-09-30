import unicodedata

D3 = {"MON":0,"TUE":1,"WED":2,"THU":3,"FRI":4,"SAT":5,"SUN":6}

def _strip_accents_upper(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.strip())
    return "".join(ch for ch in s if not unicodedata.combining(ch)).upper()

def parse_days(s: str):
    raw = s.strip()
    if not raw:
        raise ValueError("Empty days_of_operation")
    if raw.lower() == "daily":
        return frozenset(range(7))
    if "-" in raw and "|" not in raw and "," not in raw:
        a,b = ( _strip_accents_upper(t)[:3] for t in raw.split("-",1) )
        ai, bi = D3[a], D3[b]
        seq = list(range(ai, bi+1)) if ai <= bi else list(range(ai,7))+list(range(0,bi+1))
        return frozenset(seq)
    sep = "|" if "|" in raw else ","
    toks = [ _strip_accents_upper(t)[:3] for t in raw.split(sep) if t.strip() ]
    return frozenset(D3[t] for t in toks)

def parse_price_int(s: str) -> int:
    t = s.strip().replace("€","").replace(",","").replace(" ", "")
    if t == "": raise ValueError("Empty price")
    if "." in t: raise ValueError(f"Decimals not allowed for int price: {s}")
    n = int(t)
    if n < 0: raise ValueError("Negative price")
    return n
