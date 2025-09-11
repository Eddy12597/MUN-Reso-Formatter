from docx.api import Document
import document as doc
from pathlib import Path
from core.resolution import *
import re
import roman
import ai_generated
from typing import Generic, TypeVar, cast, Callable
import inspect
import json

# ==== CONFIG ====

preamb_config_path = Path("./config/preambs/config.json")
operationals_config_path = Path("./config/operationals/config.json")

preamb_config: dict[str, list[str] | str] = {}
with preamb_config_path.open("r", encoding="utf-8") as f:
    preamb_config = json.load(f)

operationals_config: dict[str, list[str] | str] = {}
with operationals_config_path.open("r", encoding="utf-8") as f:
    operationals_config = json.load(f)

preamb_phrases = preamb_config.get('preamb_phrases', [])
operationals_phrases = cast(list[str], operationals_config.get('operationals_phrases', []))

if preamb_phrases is []:
    print("Warning: no preamb phrases loaded")
if operationals_phrases is []:
    print("Warning: no operational phrases loaded")

# ====
print("Loading language package. This may take a while.")
import spacy
nlp = spacy.load('en_core_web_sm')

class ResolutionParsingError(BaseException):
    def __init__(self, msg: str, line: int):
        super().__init__(msg)
        self.line = line
    def __str__(self):
        return super().__str__() + f"\n\tIN LINE {self.line}"
    
def strip_punctuations(text: str) -> str:
    """
    Removes extra space for punctuations when tokens of a sentence is joined by a space literal
    """
    for punc in [',', '.', ';', ':', '!', '?']:
        text = text.replace(f" {punc}", f"{punc}")
    return text

def extract_first_participial_phrase(text: str) -> tuple[str | None, str]:
    doc = nlp(text)
    
    for i, token in enumerate(doc):
        # Check for participles more carefully
        is_participle = (
            token.pos_ == 'VERB' and 
            token.morph.get('VerbForm', None) == ['Part']
        )
        
        # Also check for words ending with -ing, -ed, -en that might be participles
        is_likely_participle = (
            token.pos_ == 'VERB' and 
            (token.text.endswith('ing') or 
             token.text.endswith('ed') or 
             token.text.endswith('en'))
        )
        
        if is_participle or is_likely_participle:
            # Start building the participial phrase
            phrase_tokens = [token.text]
            j = i + 1
            
            # Include modifiers, prepositions, particles, etc.
            while (j < len(doc) and 
                  (doc[j].pos_ in ['ADP', 'ADV', 'PART', 'SCONJ'] or 
                   doc[j].dep_ in ['prep', 'agent', 'pcomp', 'mark', 'advmod'])):
                phrase_tokens.append(doc[j].text)
                j += 1
            
            # Extract the first participial phrase
            participial_phrase = ' '.join(phrase_tokens)
            remaining_text = ' '.join([t.text for t in doc[j:]])
            remaining_text = strip_punctuations(remaining_text)
            print("Participial phrase: " + participial_phrase + ", remaining: " + remaining_text)
            return participial_phrase, remaining_text
    
    return None, text

# Doesn't work for 'be' verbs and 'will' aux verbs
def extract_first_verb(text: str) -> tuple[str | None, str | None, bool]:
    """
    Extracts first verb from a sentence. Includes a preposition after the verb if there is any (used for the clause verb extraction). Returns the verb and the preposition, the rest of the sentence, and whether it occurs at the beginning of the sentence.
    Params:
    ------------
    text: str
        The text in which to extract the first verb
    Returns:
    ------------
    tuple [str | None, str, bool]
        1. The first element (str | None): 
            the verb of the sentence. If there is no verb in the sentence or if the sentence is empty, returns None

        2. The second element (str | None): 
            the rest of the sentence. If the sentence is empty, returns None

        3. The third element (bool):
            whether the verb occurs at the beginning of the sentence. If it does not, or if the text is empty, or if the text contains no verb, returns False
    """
    if not text or text.isspace():
        return None, None, False

    doc = nlp(text)
    
    for i, token in enumerate(doc):
        if token.pos_ in ['VERB', 'AUX']:
            # Check if this is part of a phrasal verb
            verb_phrase = token.text
            
            # Look for particles/prepositions that might be part of phrasal verbs
            if i + 1 < len(doc) and doc[i+1].dep_ in ['prt', 'prep']:
                verb_phrase += " " + doc[i+1].text
            
            # Reconstruct the rest of the sentence
            tokens_to_remove = [token]
            if i + 1 < len(doc) and doc[i+1].dep_ in ['prt', 'prep']:
                tokens_to_remove.append(doc[i+1])
            
            rest_of_sentence = ' '.join([
                t.text for t in doc 
                if t not in tokens_to_remove and not t.is_space
            ]).strip()
            
            # Clean up punctuation
            rest_of_sentence = strip_punctuations(rest_of_sentence)
            return verb_phrase, rest_of_sentence, i == 0
    
    # No verb found
    rest_of_sentence = ' '.join([t.text for t in doc if not t.is_space]).strip()
    rest_of_sentence = strip_punctuations(rest_of_sentence)
    return None, rest_of_sentence, False


# alter this to gui input later

input_filename = input("Enter input filename, ENTER to test: ")
if input_filename == '':
    input_filename = Path("../tests/inputs/test1.docx")
else:
    input_filename = Path(input_filename)

output_filename = input("Enter output filename, ENTER to test: ")
if output_filename == '':
    output_filename = Path("../tests/outputs/test1.docx")
else:
    output_filename = Path(output_filename)

# === TYPES to silence the type checker ===
type _rc_inner_t = str | preamb | clause
type _rc_t = ResolutionComponent[_rc_inner_t]
T = TypeVar('T')
type _mat_func_t[T] = Callable[[str], tuple[T, bool]]

class ResolutionComponent(Generic[T]):
    def __init__(self, startIdx: int = -1, endIdx: int = -1, patterns: list[str] | None = None, currentIdx: int = 0, matchFunc: _mat_func_t[T] | None = None):
        self.startIdx = startIdx
        self.endIdx = endIdx
        self.patterns = patterns if patterns is not None else [r'(.*)']
        self.currentIdx = currentIdx
        self.parsed = False
        self.values: list[T] = [] # single element list if not a list
        self.results: list[re.Match | None] | None = None
        self.found = False
        self.matchFunc: _mat_func_t[T] | None = cast(_mat_func_t[T], matchFunc)

    
    def extract(self, text: str, flag: int | None = None) -> None:
        """Extract content using the pattern and store result"""
        # if self.parsed: return
        if self.matchFunc is None:
            self.results = self.getContentFrom(text, flag)
            if self.results is not None:
                if any(self.results):
                    for result in self.results:
                        if result is not None:
                            extracted_value = result.group(1).strip() if result.groups() else result.group(0).strip()
                            self.appendValue(extracted_value)
        else:
            # matchFunc returns tuple[str, bool]
            # str: remaining, bool: format correctness
            result =self.matchFunc(text)
            if (result[1]):
                self.appendValue(cast(T, result[0]))

    def markFinished(self):
        self.parsed = True
    
    def getContentFrom(self, text: str, flag: int | None = None) -> list[re.Match | None] | None: # None here because it returns early if its parsed already
        # if self.parsed: return
        searchList: list[re.Match | None] = []
        if flag is not None:
            for pattern in self.patterns:
                searchList.append(re.search(pattern, text, flag))
            return searchList
        for pattern in self.patterns:
            searchList.append(re.search(pattern, text))
        return searchList
    
    def setValue(self, values: list[T]) -> None:
        self.values = values
    
    def appendValue(self, newValue: T) -> None:
        self.values.append(newValue)
    
    def getValues(self) -> list[T]:
        return self.values
    
    def getFirst(self) -> T | str:
        if self.values:
            return self.values[0]
        return ""
        
    
    def getListValues(self, delimiter: str = ",") -> list[T] | None:
        """Returns a list of values separated by a delimiter if the type is str"""
        if self.values and not all(isinstance(val, str) for val in self.values):
            return None
        
        if not self.getValues():
            return []
        
        if len(self.getValues()) > 1:
            return self.getValues()
        
        first = self.getFirst()
        if first is not None and isinstance(first, str) and delimiter in first:
            return [item.strip() for item in first.split(delimiter)] # type: ignore
        return self.getValues()


def parseToResolution (doc: doc.document)\
      -> tuple[Resolution, dict[str, _rc_t], list[ResolutionParsingError]]:
    
    paragraphs = doc.get_paragraphs()

    components: dict[str, ResolutionComponent[_rc_inner_t]] = {}
    errorList: list[ResolutionParsingError] = []

    components['committee'] = cast(_rc_t, ResolutionComponent[str](patterns=[
        r'committee: (.*)',r'comittee: (.*)', r'commitee: (.*)',
        r'committee:(.*)', r'comittee:(.*)', r'commitee:(.*)',
    ]))

    components['mainSubmitter'] = cast(_rc_t, ResolutionComponent[str](patterns=[
        r'main submitter: (.*)', r'main-submitter: (.*)',
        r'main submitters: (.*)' r'main-submitters: (.*)',
        r'main submitter:(.*)', r'main-submitters:(.*)',
        r'main submitters:(.*)', r'main-submitters:(.*)',
    ]))

    components['coSubmitters'] = cast(_rc_t, ResolutionComponent[str](patterns=[
        r'co-submitters: (.*)', r'cosubmitters: (.*)',
        r'co-submitter: (.*)', r'cosubmitter: (.*)',
        r'co-submitters:(.*)', r'cosubmitters:(.*)',
        r'co-submitter:(.*)', r'cosubmitter:(.*)',
    ]))

    components['topic'] = cast(_rc_t, ResolutionComponent[str](patterns=[
        r'topic: (.*)', r'topics: (.*)',
        r'topic:(.*)', r'topics:(.*)',
    ]))

    listPreambs: list[preamb] = []
    listOperationals: list[clause] = []


    def _preambs_match_function(text: str) -> tuple[preamb, bool]: # TODO: Fix
        """
        Parse one line of preambular text.
        
        Returns:
        (preamb_obj, True)  -> created a valid preambular clause
        (preamb_obj, False) -> could not match
        """
        for phrase in preamb_phrases:
            # Match phrase at start, capture the rest until optional comma/semicolon
            pattern = rf'^\s*{re.escape(phrase)}\s+(.*?)[,;]?\s*$'
            result = re.match(pattern, text, re.IGNORECASE)
            if result:
                return (preamb(phrase, result.group(1).strip()), True)

        # no match found
        return (preamb("__ERROR__", text.strip()), False)
    
        
    def _find_first_operational_phrase(text: str, phrases: list[str]) -> tuple[str | None, str, bool]:
        if not phrases:
            return (None, text, False)
        sorted_phrases = sorted(set(phrases), key=lambda s: len(s), reverse=True)
        orig = text
        for ph in sorted_phrases:
            ph_esc = re.escape(ph)
            # allow optional leading brackets/quotes/punctuation before phrase at start
            pattern_start = rf'^\s*[\(\["\']*\s*({ph_esc})\b'
            m = re.search(pattern_start, orig, flags=re.IGNORECASE)
            if m:
                start_idx = m.start(1)
                end_idx = m.end(1)
                rest = orig[end_idx:].lstrip(" \t\n\r:;,-—–.()[]\"'")  # trim likely punctuation after phrase
                return (orig[start_idx:end_idx], rest, True)

        # If no start matches, search anywhere (first occurrence of any phrase)
        for ph in sorted_phrases:
            ph_esc = re.escape(ph)
            pattern_any = rf'\b({ph_esc})\b'
            m = re.search(pattern_any, orig, flags=re.IGNORECASE)
            if m:
                start_idx = m.start(1)
                end_idx = m.end(1)
                rest = orig[end_idx:].lstrip(" \t\n\r:;,-—–.()[]\"'")
                return (orig[start_idx:end_idx], rest, False)

        return (None, text, False)


    def _operationals_match_function(text: str) -> tuple[clause, bool]:
        # persistent state stored on the function object
        if not hasattr(_operationals_match_function, "state"):
            _operationals_match_function.state = { # type: ignore
                "clause_counter": 0,
                "subclause_counter": 0,
                "subsubclause_counter": 0,
                "current_clause": None,
                "current_subclause": None,
                "current_subsubclause": None,
            }
        st = _operationals_match_function.state # type: ignore

        raw = text.strip()
        if not raw:
            return (st["current_clause"] if st["current_clause"] is not None else clause(0, "__EMPTY__", "__EMPTY__"), False)

        # helper to convert roman (lowercase) to int
        def roman_to_int_lower(s: str) -> int | None:
            try:
                return roman.fromRoman(s.upper())
            except Exception:
                return None

        # ---- Top-level clause detection: only Arabic numerals ----
        m_clause = re.match(r'^\s*(\d+)\s*[\.\)]\s*(.+)$', raw)
        if m_clause:
            num = m_clause.group(1)
            body = m_clause.group(2).strip()
            try:
                idx = int(num)
            except Exception:
                st["clause_counter"] += 1
                idx = st["clause_counter"]

            st["clause_counter"] = max(st["clause_counter"], idx)

            # --- new logic: detect verb phrase using operationals_phrases ---
            try:
                phrases = operationals_phrases  # expect this list to exist globally
            except NameError:
                phrases = []

            verb_phrase, rest_of_sentence, at_start = _find_first_operational_phrase(body, phrases)
            if verb_phrase:
                verb = verb_phrase.strip()
                clause_text = rest_of_sentence if rest_of_sentence else ""
            else:
                verb = "clause verb"
                clause_text = body

            new_clause = clause(idx, verb=verb, text=clause_text)
            st["current_clause"] = new_clause
            st["current_subclause"] = None
            st["current_subsubclause"] = None
            st["subclause_counter"] = 0
            st["subsubclause_counter"] = 0

            try:
                listOperationals.append(new_clause)
            except NameError:
                pass

            return (new_clause, True)

        # ---- Sub-subclause detection: restrict to typical lowercase numerals (i, ii, iii, iv, v, vi, vii, viii, ix, x) ----
        m_ssc = re.match(r'^\s*\(?([ivx]{1,4})\)?\s*[\.\)]\s*(.+)$', raw)
        if m_ssc:
            roman_str = m_ssc.group(1)
            body = m_ssc.group(2).strip()
            roman_idx = roman_to_int_lower(roman_str)
            # attach to current subclause if present
            if st["current_subclause"] is not None:
                idx = roman_idx if roman_idx is not None else (st["subsubclause_counter"] + 1)
                st["subsubclause_counter"] += 1
                new_ssc = subsubclause(idx, text=body)
                st["current_subclause"].append(new_ssc)
                st["current_subsubclause"] = new_ssc
                return (st["current_clause"], False)
            # fallback: if no active subclause, create a subclause and attach this as its first sub-subclause
            if st["current_clause"] is not None:
                st["subclause_counter"] += 1
                new_sub = subclause(st["subclause_counter"], text=body)
                st["current_clause"].listsubclauses.append(new_sub)
                st["current_subclause"] = new_sub
                st["current_subsubclause"] = None
                st["subsubclause_counter"] = 0
                return (st["current_clause"], False)

        # ---- Subclause detection: single letter like "a." or "(a)" ----
        m_sub = re.match(r'^\s*\(?([A-Za-z])\)?\s*[\.\)]\s*(.+)$', raw)
        if m_sub and st["current_clause"] is not None:
            letter = m_sub.group(1).lower()
            body = m_sub.group(2).strip()
            # convert letter to index (a->1, b->2, ...)
            if letter.isalpha() and len(letter) == 1:
                idx = ord(letter) - ord('a') + 1
            else:
                st["subclause_counter"] += 1
                idx = st["subclause_counter"]

            new_sub = subclause(idx, text=body)
            st["current_clause"].listsubclauses.append(new_sub)
            st["current_subclause"] = new_sub
            st["current_subsubclause"] = None
            st["subsubclause_counter"] = 0
            return (st["current_clause"], False)

        # ---- Continuation: append to the most recent item ----
        cont = raw
        if st["current_subsubclause"] is not None:
            st["current_subsubclause"].text = strip_punctuations(st["current_subsubclause"].text + " " + cont)
            return (st["current_clause"], False)
        if st["current_subclause"] is not None:
            st["current_subclause"].text = strip_punctuations(st["current_subclause"].text + " " + cont)
            return (st["current_clause"], False)
        if st["current_clause"] is not None:
            st["current_clause"].text = strip_punctuations(st["current_clause"].text + " " + cont)
            return (st["current_clause"], False)

        # nothing matched: return harmless placeholder (don't append)
        return (clause(0, "__ERROR__", raw), False)

    
    components['preambs'] = cast(_rc_t, ResolutionComponent[preamb]())
    components['operationals'] = cast(_rc_t, ResolutionComponent[clause]())

    components['preambs'].matchFunc = _preambs_match_function
    components['operationals'].matchFunc = _operationals_match_function
    componentsList: list[str] = ['committee', 'mainSubmitter', 'coSubmitters', 'topic', 'preambs', 'operationals']

    # Main Loop
    for index, line in enumerate(paragraphs):
        print(f"{index}{(4-len(str(index)) if len(str(index)) < 4 else len(str(index))) * " "}| {line}")
        for componentName in componentsList:
            components[componentName].extract(line, re.IGNORECASE)
        
    
    components['preambs'].setValue(cast(list[_rc_inner_t], listPreambs))
    components['preambs'].markFinished()
    components['operationals'].setValue(cast(list[_rc_inner_t], listOperationals))
    components['operationals'].markFinished()

    reso = Resolution(
        cast(str, components['committee'].getFirst()),
        cast(str, components['mainSubmitter'].getFirst()),
        cast(list[str], components['coSubmitters'].getListValues()),
        cast(str, components['topic'].getFirst()),
    )

    reso.preambs = listPreambs
    reso.clauses = listOperationals

    return (reso, components, errorList)

def main():
    

    """
    Step 1: Read doc and parse to object
    """
    thedoc = doc.document(str(input_filename), str(output_filename))
    parseresult = parseToResolution(thedoc) #ai_generated.parseToResolution(thedoc)
    thereso, components, errorList = parseresult

    print(str(thereso))

    if (len(errorList) != 0):
        print("="*30 + " ERRORS " + "=" * 30)
        for error in errorList:
            print(str(error))

    """
    Step 2: Format object
    """




    """
    Step 3: Conflict showing, resolution and confirmation
    """




    """
    Step 4: Write to file
    """

if __name__ == "__main__":
    main()