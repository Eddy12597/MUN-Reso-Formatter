"""

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
                committeeSubjectSearch = None
                committeeSubjectPlacement = 'preambs start' in parsedList.keys()
                if not committeeSubjectPlacement: # hasn't parsed preambs
                    preambsStartIdx = i + 1
                    print("===Preambs start extracted===")
            
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
                print(f"Extracting participial from {paragraphs[i+1]}")
                [adverb], text = extract_first_participial_phrase(paragraphs[i + 1])
                if adverb is None:
                    raise ResolutionParsingError(f"Preamb clause {i - preambsStartIdx + 2} doesn't start with participial")
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
                    currentSubSubClauseIdx = 1
                
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
    print("Preambs Start Idx: " + str(preambsStartIdx))
    return (reso,
                committeeIdx,
                mainsubIdx,
                cosubsIdx,
                topicIdx,
                committeeSubjectIdx,
                preambsStartIdx,
                preambsEndIdx,
                operationalsStartIdx,)


"""