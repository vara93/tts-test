import re
import unicodedata

VOWELS = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"
WORD = re.compile(r"[А-Яа-яЁёЙй\u0301+]+")

def validate_stress(text: str) -> None:
    text = unicodedata.normalize("NFD", text)
    for i, ch in enumerate(text):
        if ch == "+" and (i + 1 == len(text) or text[i + 1] not in VOWELS):
            raise ValueError("Знак + должен стоять непосредственно перед русской гласной")
        if ch == "\u0301" and (i == 0 or text[i - 1] not in VOWELS):
            raise ValueError("Ударение U+0301 должно следовать за русской гласной")

def canonical(text: str) -> str:
    """Convert both accepted syntaxes to '+' understood by Chatterbox RU frontend."""
    text = unicodedata.normalize("NFD", text)
    validate_stress(text)
    out = []
    for ch in text:
        if ch == "\u0301":
            vowel = out.pop()
            out.extend(("+", vowel))
        else:
            out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))

def prepare(source: str, dictionary: dict[str, str] | None = None) -> str:
    """Manual occurrence wins; then dictionary. Auto accent is deliberately opt-in."""
    validate_stress(source)
    dictionary = {k.casefold(): canonical(v) for k, v in (dictionary or {}).items()}
    def repl(m: re.Match) -> str:
        token = m.group(0)
        if "+" in token or "\u0301" in unicodedata.normalize("NFD", token):
            return canonical(token)
        return dictionary.get(token.casefold(), token)
    return WORD.sub(repl, source)

def segments(text: str, limit: int = 220) -> list[str]:
    if not text.strip(): return []
    pieces = re.split(r"(?<=[.!?…])\s+|(?<=\n)\s*", text)
    result=[]
    for piece in pieces:
        piece=piece.strip()
        while len(piece)>limit:
            cut=max(piece.rfind(" ",0,limit+1),1)
            result.append(piece[:cut]); piece=piece[cut:].strip()
        if piece: result.append(piece)
    return result

