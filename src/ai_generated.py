import re
import spacy
nlp = spacy.load('en_core_web_sm')
import document as doc  # Assuming this is your document module
from core.resolution import *
import roman

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

class ResolutionComponent:
    def __init__(self, startIdx: int, endIdx: int, pattern: str, currentIdx: int = 0):
        self.startIdx = startIdx
        self.endIdx = endIdx
        self.pattern = pattern
        self.currentIdx = currentIdx
        self.parsed = False
        self.value: list[str] = []
        self.result: re.Match | None = None
        self.found = False
    
    def extract(self, text: str, flag: int | None = None) -> None:
        """Extract content using the pattern and store result"""
        self.result = self.getContentFrom(text, flag)
        if self.result is not None:
            extracted_value = self.result.group(1).strip() if self.result.groups() else self.result.group(0).strip()
            self.value.append(extracted_value)
            self.found = True
            self.parsed = True
    
    def getContentFrom(self, text: str, flag: int | None = None) -> re.Match | None:
        """Search for pattern in text with optional flags"""
        if flag is not None:
            return re.search(self.pattern, text, flag)
        return re.search(self.pattern, text)
    
    def setValue(self, value: list[str]) -> None:
        """Set the value list directly"""
        self.value = value
    
    def appendValue(self, newValue: str) -> None:
        """Append a new value to the value list"""
        self.value.append(newValue)
    
    def getValue(self) -> list[str]:
        """Get the current value list"""
        return self.value
    
    def getStringValue(self) -> str:
        """Get value as string (first value or empty string)"""
        return self.value[0] if self.value else ""
    
    def getListValue(self, delimiter: str = ",") -> list[str]:
        """Get values as list, splitting by delimiter if single string value exists"""
        if not self.value:
            return []
        
        # If we have multiple values, return them as is
        if len(self.value) > 1:
            return self.value
        
        # If we have one value that might contain delimiters, split it
        if delimiter in self.value[0]:
            return [item.strip() for item in self.value[0].split(delimiter)]
        
        return self.value

def parseToResolution(document: doc.document) -> tuple[Resolution, int, int, int, int, int, int, int, int]:
    reso: Resolution
    paragraphs = document.get_paragraphs()
    
    # Create components for each part of the resolution
    committeeComponent = ResolutionComponent(-1, -1, r'committee: (.*)')
    mainsubComponent = ResolutionComponent(-1, -1, r'main submitter: (.*)')
    cosubsComponent = ResolutionComponent(-1, -1, r'co-submitters: (.*)')
    topicComponent = ResolutionComponent(-1, -1, r'topic: (.*)')
    committeeSubjectComponent = ResolutionComponent(-1, -1, r'the (.*),')
    operationalsStartComponent = ResolutionComponent(-1, -1, r'1\. (.*)')
    
    # Other variables
    committeeIdx: int = -1
    mainsubIdx: int = -1
    cosubsIdx: int = -1
    topicIdx: int = -1
    committeeSubjectIdx: int = -1
    preambsStartIdx: int = -1  # inclusive
    preambsEndIdx: int = -1    # exclusive
    operationalsStartIdx: int = -1

    currentClauseIdx: int = -1
    currentSubClauseIdx: int = -1
    currentSubSubClauseIdx: int = -1
    
    committeeSubjectPlacement: bool = False
    preambsList: list[preamb] = []
    operationalsList: list[clause] = []
    
    parsedComponents = {}  # Track which components have been parsed
    
    try:
        print("Extracting document: ")
        for i, p in enumerate(paragraphs):
            print(f"{i}\t| {p}")
            
            # Extract components in order of resolution structure
            if not committeeComponent.parsed:
                committeeComponent.extract(p, re.IGNORECASE)
                if committeeComponent.found:
                    committeeIdx = i
                    parsedComponents['committee'] = committeeComponent.result
                    print("> Committee name extracted")
                    continue
            
            if not mainsubComponent.parsed:
                mainsubComponent.extract(p, re.IGNORECASE)
                if mainsubComponent.found:
                    mainsubIdx = i
                    parsedComponents['main sub'] = mainsubComponent.result
                    print("> Main submitter name extracted")
                    continue
            
            if not cosubsComponent.parsed:
                cosubsComponent.extract(p, re.IGNORECASE)
                if cosubsComponent.found:
                    cosubsIdx = i
                    parsedComponents['co subs'] = cosubsComponent.result
                    print("> Co submitters names extracted")
                    continue
            
            if not topicComponent.parsed:
                topicComponent.extract(p, re.IGNORECASE)
                if topicComponent.found:
                    topicIdx = i
                    parsedComponents['topic'] = topicComponent.result
                    print("> Topic name extracted")
                    continue
            
            # Committee as subject detection
            if not committeeSubjectComponent.parsed:
                committeeSubjectComponent.extract(p, re.IGNORECASE)
                if committeeSubjectComponent.found:
                    committeeSubjectIdx = i
                    print("> Committee name detected as subject of resolution")
                    
                    # Check if we've already started parsing preambs
                    committeeSubjectPlacement = 'preambs start' in parsedComponents.keys()
                    if not committeeSubjectPlacement:
                        preambsStartIdx = i + 1
                        print("===Preambs start extracted===")
                    continue
            
            # Operationals start detection
            if not operationalsStartComponent.parsed:
                operationalsStartComponent.extract(p, re.IGNORECASE)
                if operationalsStartComponent.found:
                    operationalsStartIdx = i
                    currentClauseIdx = 1
                    currentSubClauseIdx = 1
                    currentSubSubClauseIdx = 1
                    print("> Operationals start extracted")
                    continue
            
            # Preambs extraction
            if preambsStartIdx != -1 and preambsEndIdx == -1:
                if p.startswith('1'):
                    print("> Operationals start detected")
                    preambsEndIdx = i
                    operationalsStartIdx = i
                    continue
                
                # Extract participial phrase for preamb
                print(f"Extracting participial from {paragraphs[i+1]}")
                [adverb], text = extract_first_participial_phrase(paragraphs[i + 1])
                if adverb is None:
                    raise ResolutionParsingError(f"Preamb clause {i - preambsStartIdx + 2} doesn't start with participial")
                preambsList.append(preamb(adverb, text))
            
            # Operationals extraction
            if operationalsStartIdx != -1:
                # Clause detection
                clauseSearch = re.search(rf'{currentClauseIdx}\. (.*)', p)
                if clauseSearch:
                    print("===Clause extracted===")
                    clauseContent = clauseSearch.group(1).strip()
                    augmentedSentence = f"The {committeeSubjectComponent.getStringValue()} {clauseContent}"
                    clauseVerb, clauseContent, verbAtBeginning = extract_first_verb(augmentedSentence)
                    if clauseVerb is None:
                        raise ResolutionParsingError(f"Clause {currentClauseIdx} ({augmentedSentence}) does not start with a verb")
                    if clauseContent is None:
                        raise ResolutionParsingError(f"Clause {currentClauseIdx} ({augmentedSentence}) does not contain main content")
                    operationalsList.append(clause(currentClauseIdx, clauseVerb, clauseContent))
                    currentClauseIdx += 1
                    currentSubClauseIdx = 1
                    currentSubSubClauseIdx = 1
                
                # Subclause detection
                subclauseSearch = re.search(rf'{chr(96 + currentSubClauseIdx)}\. (.*)', p)
                if subclauseSearch:
                    print("===Sub clause extracted===")
                    subclauseContent = subclauseSearch.group(1).strip()
                    operationalsList[-1].append(subclause(currentSubClauseIdx, subclauseContent))
                    currentSubClauseIdx += 1
                    currentSubSubClauseIdx = 1
                
                # Subsubclause detection
                subsubclauseSearch = re.search(rf'{roman.toRoman(currentSubSubClauseIdx).lower()}\. (.*)', p)
                if subsubclauseSearch:
                    print("===Sub sub clause extracted===")
                    subsubclauseContent = subsubclauseSearch.group(1).strip()
                    operationalsList[-1].listsubclauses[-1].append(subsubclause(currentSubSubClauseIdx, subsubclauseContent))
                    currentSubSubClauseIdx += 1

    except ResolutionParsingError as rpe:
        print("\t=== ERROR PARSING RESOLUTION / FORMATTING ERROR ===\n" + str(rpe))
        print("Parsed Components: " + str(parsedComponents) + "\n")
    
    # Create Resolution object with extracted values
    reso = Resolution(
        committeeComponent.getStringValue() or "Committee Name Not Found",
        mainsubComponent.getStringValue() or "Main Submitter Not Found",
        cosubsComponent.getListValue() or ["Co Submitters Not Found"],
        topicComponent.getStringValue() or "Topic Not Found",
        preambsList,
        operationalsList
    )
    
    print("Preambs Start Idx: " + str(preambsStartIdx))
    return (
        reso,
        committeeIdx,
        mainsubIdx,
        cosubsIdx,
        topicIdx,
        committeeSubjectIdx,
        preambsStartIdx,
        preambsEndIdx,
        operationalsStartIdx,
    )

r"""
# normalize paragraph to text
        text = str(line)
        text = text.strip()
        if not text:
            continue

        # Try to extract header fields (case-insensitive)
        for key in ('committee','mainSubmitter','coSubmitters','topic'):
            comp = components[key]
            if not comp.parsed:
                comp.extract(text, re.I)
                if comp.found:
                    comp.setFinished()

        # Preamb detection: participial phrase + remainder
        adverbs, remaining = extract_first_participial_phrase(text)
        if adverbs and adverbs[0] is not None:
            adv = adverbs[0].strip()
            content = remaining.strip()
            # strip trailing commas/periods/semicolons; preamb.toDocParagraph will add comma
            content = re.sub(r'^[\s,]+|[\s,]+$', '', content)
            content = content.rstrip('.,;:')
            listPreambs.append(preamb(adverb=adv, content=content))
            continue

        # Operational clause detection: verb at sentence start
        verb, rest, begins = extract_first_verb(text)
        if verb and begins:
            cl = clause(index=len(listOperationals)+1, verb=verb.strip(), text=rest.strip() if rest is not None else "")
            listOperationals.append(cl)
            continue

        # Subclause detection: forms like "a) ...", "b) ..."
        m_sub = re.match(r'^[\(\[]?([a-z])[\)\]]\s*(.*)', text, re.I)
        if m_sub:
            if not listOperationals:
                errorList.append(ResolutionParsingError(f"Subclause found before any clause at paragraph {index+1}: '{text}'"))
                continue
            content = m_sub.group(2).strip().rstrip('.,;:')
            parent = listOperationals[-1]
            sc = subclause(index=len(parent.listsubclauses)+1, text=content)
            parent.append(sc)
            continue

        # Sub-subclause detection: roman numerals like "i. ..." or "(i) ..."
        m_ssc = re.match(r'^[\(\[]?([ivxlcdm]+)[\)\].]?\s*(.*)', text, re.I)
        if m_ssc:
            if not listOperationals or not listOperationals[-1].listsubclauses:
                errorList.append(ResolutionParsingError(f"Sub-subclause found with no parent at paragraph {index+1}: '{text}'"))
                continue
            content = m_ssc.group(2).strip().rstrip('.,;:')
            last_sub = listOperationals[-1].listsubclauses[-1]
            ssc = subsubclause(index=len(last_sub.listsubsubclauses)+1, text=content)
            last_sub.append(ssc)
            continue

        # Fallback: continuation of previous clause/subclause (append)
        if listOperationals:
            last_clause = listOperationals[-1]
            if last_clause.listsubclauses:
                last_sub = last_clause.listsubclauses[-1]
                last_sub.text = last_sub.text.rstrip(' ,') + ' ' + text
            else:
                last_clause.text = last_clause.text.rstrip(' ,') + ' ' + text
            continue

        # If nothing matched and no clause exists, we ignore or log
        # (keeps parsing robust for unknown lines)
        # ... no other action for this paragraph

"""