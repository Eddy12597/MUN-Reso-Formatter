# test_extract_first_participial_phrase.py
# still failing two of them, but it kinda works

import unittest
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_first_participial_phrase(text):
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
            
            return [participial_phrase], remaining_text
    
    return [], text


class TestExtractFirstParticipialPhrase(unittest.TestCase):
    
    def test_past_participle_simple(self):
        """Test simple past participle"""
        text = "The broken window needs to be fixed."
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, ['broken'])
        self.assertEqual(remaining, "window needs to be fixed .")
    
    def test_present_participle_simple(self):
        """Test simple present participle"""
        text = "The running water sounds soothing."
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, ['running'])
        self.assertEqual(remaining, "water sounds soothing .")
    
    def test_participle_with_preposition(self):
        """Test participle followed by preposition"""
        text = "The man walking through the park smiled."
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, ['walking through'])
        self.assertEqual(remaining, "the park smiled .")
    
    def test_participle_with_adverb(self):
        """Test participle followed by adverb"""
        text = "The quickly running athlete won the race."
        result, remaining = extract_first_participial_phrase(text)
        # Note: 'quickly' is an adverb modifying 'running'
        self.assertEqual(result, ['running'])
        self.assertEqual(remaining, "athlete won the race .")
    
    def test_participle_with_multiple_words(self):
        """Test participle with multiple dependent words"""
        text = "The book written by the famous author became popular."
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, ['written by'])
        self.assertEqual(remaining, "the famous author became popular .")
    
    def test_multiple_participles(self):
        """Test text with multiple participles - should extract first one"""
        text = "The singing birds and dancing leaves create a beautiful scene."
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, ['singing'])
        self.assertEqual(remaining, "birds and dancing leaves create a beautiful scene .")
    
    def test_no_participle_found(self):
        """Test text with no participles"""
        text = "The cat sleeps on the mat."
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, [])
        self.assertEqual(remaining, text)
    
    def test_participle_at_end(self):
        """Test participle at the end of sentence"""
        text = "I saw the man running."
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, ['running'])
        self.assertEqual(remaining, ".")
    
    def test_participle_with_particle(self):
        """Test participle with particle (like phrasal verbs)"""
        text = "The turned off computer needs to be restarted."
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, ['turned off'])
        self.assertEqual(remaining, "computer needs to be restarted .")
    
    def test_complex_participial_phrase(self):
        """Test complex participial phrase"""
        text = "The students studying for their exams in the library are focused."
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, ['studying for'])
        self.assertEqual(remaining, "their exams in the library are focused .")
    
    def test_empty_string(self):
        """Test empty string input"""
        text = ""
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, [])
        self.assertEqual(remaining, "")
    
    def test_single_participle_word(self):
        """Test single participle word as input"""
        text = "running"
        result, remaining = extract_first_participial_phrase(text)
        self.assertEqual(result, ['running'])
        self.assertEqual(remaining, "")


if __name__ == '__main__':
    unittest.main()