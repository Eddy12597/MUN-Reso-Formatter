# utility for converting new-line separated input to json list

import json
import sys

def main():
    # Read all lines from stdin
    lines = sys.stdin.read().splitlines()
    
    # Filter out empty lines and strip whitespace
    phrases = [line.strip() for line in lines if line.strip()]
    
    # Remove duplicates while preserving order
    unique_phrases = []
    seen = set()
    for phrase in phrases:
        if phrase not in seen:
            seen.add(phrase)
            unique_phrases.append(phrase.lower())
    
    # Convert to JSON
    json_output = json.dumps(unique_phrases, indent=2)
    
    # Print the JSON output
    print(json_output)

if __name__ == "__main__":
    main()