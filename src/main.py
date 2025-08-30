from docx.api import Document
import document as doc
from pathlib import Path
from resolution import *
import re
import roman

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
            print("Participial phrase: " + participial_phrase + ", remaining: " + remaining_text)
            return [participial_phrase], remaining_text
    
    return [], text

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

def parseToResolution(document: doc.document) -> tuple[Resolution, int, int, int, int, int, int, int, int]:
    reso: Resolution
    paragraphs = document.get_paragraphs()
    committeeIdx: int = -1
    mainsubIdx: int = -1
    cosubsIdx: int = -1
    topicIdx: int = -1
    committeeSubjectIdx: int = -1
    preambsStartIdx: int = -1 # inclusive
    preambsEndIdx:int = -1 # exclusive, like
    operationalsStartIdx: int = -1

    currentClauseIdx: int = -1
    currentSubClauseIdx: int = -1
    currentSubSubClauseIdx: int = -1
    
    # ALL LOWER CASE !!!
    committeePattern = r'committee: (.*)'
    mainsubPattern = r'main submitter: (.*)'
    cosubsPattern = r'co-submitters: (.*)'
    topicPattern = r'topic: (.*)'
    committeeSubjectPattern = r'the (.*),'
    # preambs start: after committee (correct) or after topic (incorrect, need to fix)
    # preambs end: until '1.' (correct) or after committee as Subject (incorrect, need to fix)
    operationalsStartPattern = r'1\. (.*)'
    # operationalsIncorrectStartPattern: after the committee as subject


    parsedList: dict[str, re.Match] = {} # stores list of things parsed in order

    committeeName: str = 'Committee Name Not Found'
    committeeSubject: str = 'Committee as Subject Not Found'
    mainsubName: str = 'Main Submitter Not Found'
    cosubsNameList: list[str] = ['Co Submitters Not Found']
    topicName: str = 'Topic Not Found'
    # for the committee Subject, just add 'The ' to the committee name
    committeeSubjectPlacement: bool = False # whether committee subject is placed before preambs annd not after preambs
    preambsList: list[preamb] = []
    operationalsList: list[clause] = []
    try:
        print("Extracting document: ")
        for i, p in enumerate(paragraphs):
            print(f"{i}\t| {p}")
            committeeSearch = re.search(committeePattern, p, re.IGNORECASE)
            mainsubSearch = re.search(mainsubPattern, p, re.IGNORECASE)
            cosubsSearch = re.search(cosubsPattern, p, re.IGNORECASE)
            topicSearch = re.search(topicPattern, p, re.IGNORECASE)
            committeeSubjectSearch = re.search(committeeSubjectPattern, p, re.IGNORECASE)
            operationalsStartSearch = re.search(operationalsStartPattern, p, re.IGNORECASE)

            if committeeSearch:
                committeeName = committeeSearch.group(1).strip()
                parsedList.update({'committee': committeeSearch})
                committeeIdx = i
                print("> Committee name extracted")
                continue
            if mainsubSearch:
                mainsubName = mainsubSearch.group(1).strip()
                parsedList.update({'main sub': mainsubSearch})
                mainsubIdx = i
                print("> Main submitter name extracted")
                continue
            if cosubsSearch:
                cosubsNameList = cosubsSearch.group(1).strip().split(',')
                parsedList.update({'co subs': cosubsSearch})
                print("> Co submitters names extracted")
                continue
            if topicSearch:
                topicName = topicSearch.group(1).strip()
                parsedList.update({'topic': topicSearch})
                print("> Topic name extracted")
                continue
            if committeeSubjectSearch: # found the phrase 'The ... committeee'
                print("> Committee name detected as subject of resolution")
                committeeSubject = committeeSubjectSearch.group(1).strip()
                committeeSubjectPlacement = 'preambs start' in parsedList.keys()
                # if not committeeSubjectPlacement: # hasn't parsed preambs
                #     preambsStartIdx = i
                #     print("===Preambs start extracted===")
            
            if operationalsStartSearch:
                operationalsStartIdx = i
                currentClauseIdx = 1
                currentSubClauseIdx = 1
                currentSubSubClauseIdx = 1
                print("> Operationals start extracted")
            
            if preambsStartIdx != -1 and preambsEndIdx == -1: # preambs started, hasn't moved on to operationals
                if p.startswith('1'):
                    print("> Operationals start detected")
                    preambsEndIdx = i
                    operationalsStartIdx = i
                    continue
                # currently parsing preambs
                print(f"Extracting participial from {p}")
                [adverb], text = extract_first_participial_phrase(p)
                if adverb is None:
                    raise ResolutionParsingError(f"Preamb clause {i - preambsStartIdx + 1} doesn't start with participial")
                preambsList.append(preamb(adverb, text))
            
            if operationalsStartIdx != -1: # found operationals
                
                # rest are just operationals
                # exclude f'{i}. ', use regex
                clauseSearch = re.search(rf'{currentClauseIdx}\. (.*)', p)
                if clauseSearch:
                    print("===Clause extracted===")
                    clauseContent = clauseSearch.group(1).strip()
                    augmentedSentence = f"The {committeeSubject} {clauseContent}"
                    clauseVerb, clauseContent, verbAtBeginning = extract_first_verb(augmentedSentence)
                    if (clauseVerb is None): #or (not verbAtBeginning):
                        raise ResolutionParsingError(f"Clause {currentClauseIdx} ({augmentedSentence}) does not start with a verb")
                    if clauseContent is None:
                        raise ResolutionParsingError(f"Clause {currentClauseIdx} ({augmentedSentence}) does not contain main content")
                    operationalsList.append(clause(currentClauseIdx, clauseVerb, clauseContent))
                    currentClauseIdx += 1
                    currentSubClauseIdx = 1
                    currentSubSubClauseIdx = 1
                
                subclauseSearch = re.search(rf'{chr(96 + currentSubClauseIdx)}\. (.*)', p)
                if subclauseSearch:
                    print("===Sub clause extracted===")
                    subclauseContent = subclauseSearch.group(1).strip()
                    operationalsList[-1].append(subclause(currentSubClauseIdx, subclauseContent))
                    currentSubClauseIdx += 1
                
                subsubclauseSearch = re.search(rf'{roman.toRoman(currentSubSubClauseIdx).lower()}\. (.*)', p)
                if subsubclauseSearch:
                    print("===Sub sub clause extracted===")
                    subsubclauseContent = subsubclauseSearch.group(1).strip()
                    operationalsList[-1].listsubclauses[-1].append(subsubclause(currentSubSubClauseIdx, subsubclauseContent))
                    currentSubSubClauseIdx += 1



    except ResolutionParsingError as rpe:
        print("\t=== ERROR PARSING RESOLUTION / FORMATTING ERROR ===\n" + str(rpe))
        print("Parsed List: " + str(parsedList) + "\n")
    reso = Resolution(committeeName, mainsubName, cosubsNameList, topicName, preambsList, operationalsList)
    return (reso,
                committeeIdx,
                mainsubIdx,
                cosubsIdx,
                topicIdx,
                committeeSubjectIdx,
                preambsStartIdx,
                preambsEndIdx,
                operationalsStartIdx,)
    

def main():
    

    """
    Step 1: Read doc and parse to object
    """
    thedoc = doc.document(str(input_filename), str(output_filename))
    parseresult = parseToResolution(thedoc)
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