import spacy

nlp = spacy.load('en_core_web_sm')

import unittest

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
            rest_of_sentence = rest_of_sentence.replace(' ,', ',').replace(' .', '.').replace(' ?', '?').replace(' !', '!')
            
            return verb_phrase, rest_of_sentence, i == 0
    
    # No verb found
    rest_of_sentence = ' '.join([t.text for t in doc if not t.is_space]).strip()
    rest_of_sentence = rest_of_sentence.replace(' ,', ',').replace(' .', '.').replace(' ?', '?').replace(' !', '!')
    return None, rest_of_sentence, False



class TestExtractFirstVerb(unittest.TestCase):
    
    def setUp(self):
        """Set up spaCy NLP model for testing"""
        self.nlp = spacy.load('en_core_web_sm')
    
    def test_empty_string(self):
        """Test with empty string input"""
        result = extract_first_verb('')
        expected = (None, None, False)
        self.assertEqual(result, expected)
    
    def test_no_verb_in_sentence(self):
        """Test with sentence containing no verbs"""
        result = extract_first_verb('The quick brown fox.')
        expected = (None, 'The quick brown fox.', False)
        self.assertEqual(result, expected)
    
    def test_verb_at_beginning(self):
        """Test with verb at the beginning of sentence"""
        result = extract_first_verb('Run quickly to the store')
        expected = ('Run', 'quickly to the store', True)
        self.assertEqual(result, expected)
    
    def test_verb_in_middle(self):
        """Test with verb in the middle of sentence"""
        result = extract_first_verb('The cat jumps over the fence')
        expected = ('jumps over', 'The cat over the fence', False)
        self.assertEqual(result, expected)
    
    def test_verb_at_end(self):
        """Test with verb at the end of sentence"""
        result = extract_first_verb('The dog will bark')
        expected = ('bark', 'The dog will', False)
        self.assertEqual(result, expected)
    
    def test_multiple_verbs(self):
        """Test with multiple verbs - should return first one"""
        result = extract_first_verb('She sings and dances beautifully')
        expected = ('sings', 'She and dances beautifully', False)
        self.assertEqual(result, expected)
    
    def test_auxiliary_verb_first(self):
        """Test with auxiliary verb first"""
        result = extract_first_verb('Will you go to the party?')
        expected = ('Will', 'you go to the party?', True)
        self.assertEqual(result, expected)
    
    def test_imperative_sentence(self):
        """Test with imperative sentence (verb at beginning)"""
        result = extract_first_verb('Close the door please')
        expected = ('Close', 'the door please', True)
        self.assertEqual(result, expected)
    
    def test_single_verb(self):
        """Test with single verb only"""
        result = extract_first_verb('Run')
        expected = ('Run', '', True)
        self.assertEqual(result, expected)
    
    def test_question_with_verb_first(self):
        """Test with question where verb comes first"""
        result = extract_first_verb('Is this the right way?')
        expected = ('Is', 'this the right way?', True)
        self.assertEqual(result, expected)
    
    def test_complex_sentence(self):
        """Test with complex sentence structure"""
        result = extract_first_verb('After the rain stopped, we went outside')
        expected = ('stopped', 'After the rain, we went outside', False)
        self.assertEqual(result, expected)
    
    def test_verb_with_punctuation(self):
        """Test with punctuation around the verb"""
        result = extract_first_verb('Hello, how are you doing?')
        expected = ('doing', 'Hello, how are you ?', False)
        self.assertEqual(result, expected)
    
    def test_contracted_verbs(self):
        """Test with contracted verbs"""
        result = extract_first_verb("I'm going to the store")
        expected = ("'m", 'I going to the store', False)
        self.assertEqual(result, expected)
    
    def test_whitespace_only(self):
        """Test with whitespace-only string"""
        result = extract_first_verb('   ')
        # Should behave like empty string since spaCy will treat it as empty
        self.assertEqual(result, (None, None, False))
    
    def test_return_types(self):
        """Test that return types are correct"""
        result = extract_first_verb('The bird flies high')
        self.assertIsInstance(result[0], str)  # Verb should be string
        self.assertIsInstance(result[1], str)  # Rest should be string
        self.assertIsInstance(result[2], bool)  # Position should be boolean
        
        result_empty = extract_first_verb('')
        self.assertIsNone(result_empty[0])  # Verb should be None
        self.assertIsNone(result_empty[1])  # Rest should be None
        self.assertIsInstance(result_empty[2], bool)  # Position should be boolean

if __name__ == '__main__':
    unittest.main()