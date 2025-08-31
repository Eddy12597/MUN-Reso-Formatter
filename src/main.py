from docx.api import Document
import document as doc
from pathlib import Path
from resolution import *
import re
import roman
import ai_generated
from typing import Generic, TypeVar, cast

print("Loading language package. This may take a while.")
import spacy
nlp = spacy.load('en_core_web_sm')

class ResolutionParsingError(BaseException):
    def __init__(self, msg):
        super().__init__(msg)

def extract_first_participial_phrase(text: str) -> tuple[list[str | None], str]:
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
            remaining_text = remaining_text\
                                .replace(' ,', ',')\
                                .replace(' .', '.')\
                                .replace(' ?', '?')\
                                .replace(' !', '!')\
                                .replace(' :', ':')\
                                .replace(' ;', ';')
            print("Participial phrase: " + participial_phrase + ", remaining: " + remaining_text)
            return [participial_phrase], remaining_text
    
    return [None], text

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
        The first element (str | None): the verb of the sentence. If there is no verb in the sentence or if the sentence is empty, returns None
        The second element (str | None): the rest of the sentence. If the sentence is empty, returns None
        The third element (bool): whether the verb occurs at the beginning of the sentence. If it does not, or if the text is empty, or if the text contains no verb, returns False
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
            rest_of_sentence = rest_of_sentence\
                                .replace(' ,', ',')\
                                .replace(' .', '.')\
                                .replace(' ?', '?')\
                                .replace(' !', '!')\
                                .replace(' :', ':')\
                                .replace(' ;', ';')
            
            return verb_phrase, rest_of_sentence, i == 0
    
    # No verb found
    rest_of_sentence = ' '.join([t.text for t in doc if not t.is_space]).strip()
    rest_of_sentence = rest_of_sentence\
                        .replace(' ,', ',')\
                        .replace(' .', '.')\
                        .replace(' ?', '?')\
                        .replace(' !', '!')\
                        .replace(' :', ':')\
                        .replace(' ;', ';')
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

T = TypeVar('T')
class ResolutionComponent(Generic[T]):
    def __init__(self, startIdx: int = -1, endIdx: int = -1, patterns: list[str] | None = None, currentIdx: int = 0):
        self.startIdx = startIdx
        self.endIdx = endIdx
        self.patterns = patterns if patterns is not None else [r'(.*)']
        self.currentIdx = currentIdx
        self.parsed = False
        self.values: list[T] = [] # single element list if not a list
        self.results: list[re.Match | None] | None = None
        self.found = False
    
    def extract(self, text: str, flag: int | None = None) -> None:
        """Extract content using the pattern and store result"""
        if self.parsed: return
        self.results = self.getContentFrom(text, flag)
        if self.results is not None:
            if any(self.results):
                for result in self.results:
                    if result is not None:
                        extracted_value = result.group(1).strip() if result.groups() else result.group(0).strip()
                        self.appendValue(extracted_value)
                        self.found = True
    def setFinished(self):
        self.parsed = True
    
    def getContentFrom(self, text: str, flag: int | None = None) -> list[re.Match | None] | None: # None here because it returns early if its parsed already
        """Search for pattern in text with optional flags"""
        if self.parsed: return
        searchList: list[re.Match | None] = []
        if flag is not None:
            for pattern in self.patterns:
                searchList.append(re.search(pattern, text, flag))
            return searchList
        for pattern in self.patterns:
            searchList.append(re.search(pattern, text))
        return searchList
    
    def setValue(self, values: list[T]) -> None:
        """Set the value list directly"""
        self.values = values
    
    def appendValue(self, newValue: T) -> None:
        """Append a new value to the value list"""
        self.values.append(newValue)
    
    def getValues(self) -> list[T]:
        """Get the current value list"""
        return self.values
    
    def getFirst(self) -> T | str:
        """Returns string value of first element if it exists, else an empty string"""
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
    
# shuts pylance up
type _rc_type = ResolutionComponent[str | preamb | clause]

def parseToResolution (doc: doc.document) -> tuple[
        Resolution, dict[str,ResolutionComponent]
    ]:

        
    components: dict[str, ResolutionComponent[str | preamb | clause]] = {}
    
    components['committee'] = cast(_rc_type, ResolutionComponent[str](patterns=[
        r'committee: (.*)',r'comittee: (.*)', r'commitee: (.*)',
        
        r'committee:(.*)', r'comittee:(.*)', r'commitee:(.*)',
    ]))

    components['mainSubmitter'] = cast(_rc_type, ResolutionComponent[str](patterns=[
        r'main submitter: (.*)', r'main-submitter: (.*)',
        r'main submitters: (.*)' r'main-submitters: (.*)'

        r'main submitter:(.*)', r'main-submitters:(.*)',
        r'main submitters:(.*)', r'main-submitters:(.*)',
    ]))

    components['coSubmitters'] = cast(_rc_type, ResolutionComponent[str](patterns=[
        r'co-submitters: (.*)', r'cosubmitters: (.*)',
        r'co-submitter: (.*)', r'cosubmitter: (.*)',

        r'co-submitters:(.*)', r'cosubmitters:(.*)',
        r'co-submitter:(.*)', r'cosubmitter:(.*)',
    ]))

    components['topic'] = cast(_rc_type, ResolutionComponent[str](patterns=[
        r'topic: (.*)', r'topics: (.*)',
        r'topic:(.*)', r'topics:(.*)',
    ]))

    components['preambs'] = cast(_rc_type, ResolutionComponent[preamb]())
    components['operationals'] = cast(_rc_type, ResolutionComponent[clause]())

    # Starts searching
    # Todo: implement the main for loop

    reso = Resolution(
        cast(str, components['committee'].getFirst()),
        cast(str, components['mainSubmitter'].getFirst()),
        cast(list[str], components['coSubmitters'].getListValues()),
        cast(str, components['topic'].getFirst()),
    )

    # remember to set preambs and operationals to reso
    
    return (reso, components)

def main():
    

    """
    Step 1: Read doc and parse to object
    """
    thedoc = doc.document(str(input_filename), str(output_filename))
    parseresult = parseToResolution(thedoc) #ai_generated.parseToResolution(thedoc)
    thereso = parseresult[0]

    print(str(thereso))

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