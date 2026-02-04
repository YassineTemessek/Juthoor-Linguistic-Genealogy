import pandas as pd
import re
from pyarabic import araby

# File paths
quran_text_path = 'quran_text.csv'
roots_dict_path = 'roots_dictionary.csv'
output_word_root_map_path = 'word_root_map.csv'

# Load data
df_quran_text = pd.read_csv(quran_text_path)
df_roots_dictionary = pd.read_csv(roots_dict_path)

# Create a lookup dictionary for roots_dictionary for efficient matching
# Key: root_letters, Value: root_id
roots_lookup = pd.Series(df_roots_dictionary.root_id.values, index=df_roots_dictionary.root_letters).to_dict()

# Data structure to store word-root mappings
word_root_map_data = []

# Function to find Jabal's root
def find_jabal_root(target_word, roots_lookup_dict):
    # 1. Normalize the word (remove tatweel, diacritics, etc.)
    normalized_word = araby.strip_tashkeel(target_word)
    normalized_word = araby.normalize_hamza(normalized_word)
    normalized_word = araby.strip_tatweel(normalized_word)
    
    # 2. Check if the normalized word itself is a root
    if normalized_word in roots_lookup_dict:
        return normalized_word
    
    # 3. Try to strip common prefixes/suffixes to get a 3-letter core
    # This is a simplified approach and not exhaustive
    
    # Common prefixes (al-, wa-, fa-, la-, etc.)
    prefixes = ['ال', 'و', 'ف', 'ل', 'ب', 'ك', 'س', 'ت', 'ن', 'ا'] 
    # Common suffixes (un, in, at, ah, i, u, a, etc.)
    suffixes = ['ون', 'ين', 'ات', 'ة', 'ي', 'و', 'ا'] 
    
    candidate_word = normalized_word
    
    # Remove prefixes
    for p in prefixes:
        if candidate_word.startswith(p) and len(candidate_word) > len(p) and re.fullmatch(r'[\u0621-\u064A]{2,4}', candidate_word[len(p):]):
            candidate_word_after_prefix = candidate_word[len(p):]
            if candidate_word_after_prefix in roots_lookup_dict:
                return candidate_word_after_prefix
    
    candidate_word = normalized_word # Reset for suffix stripping
    # Remove suffixes
    for s in suffixes:
        if candidate_word.endswith(s) and len(candidate_word) > len(s) and re.fullmatch(r'[\u0621-\u064A]{2,4}', candidate_word[:-len(s)]):
            candidate_word_after_suffix = candidate_word[:-len(s)]
            if candidate_word_after_suffix in roots_lookup_dict:
                return candidate_word_after_suffix

    # Combined prefix/suffix stripping (might be too aggressive)
    # This needs careful refinement
    stripped_word = normalized_word
    for p in prefixes:
        if stripped_word.startswith(p) and len(stripped_word) > len(p):
            stripped_word = stripped_word[len(p):]
            break # Take first matching prefix
    for s in suffixes:
        if stripped_word.endswith(s) and len(stripped_word) > len(s):
            stripped_word = stripped_word[:-len(s)]
            break # Take first matching suffix
            
    if 2 <= len(stripped_word) <= 4 and stripped_word in roots_lookup_dict:
        return stripped_word

    # One more attempt: check all substrings of 2, 3, or 4 letters in the original normalized word
    # This is a broad search and might find roots that are not truly the word's root
    for length in range(2, 5):
        for i in range(len(normalized_word) - length + 1):
            sub = normalized_word[i : i + length]
            if sub in roots_lookup_dict:
                return sub

    return None # Root not found in dictionary

# Iterate through each ayah
for index, row in df_quran_text.iterrows():
    ayah_id = row['id']
    text_clean = row['text_clean']

    words = text_clean.split()

    for word_pos, word in enumerate(words):
        extracted_root_letters = find_jabal_root(word, roots_lookup)
        
        root_id = None
        if extracted_root_letters:
            root_id = roots_lookup[extracted_root_letters]

        word_root_map_data.append({
            'ayah_id': ayah_id,
            'word_position': word_pos + 1, # 1-indexed
            'word': word,
            'root_letters': extracted_root_letters,
            'root_id': root_id
        })

# Create DataFrame and save
df_word_root_map = pd.DataFrame(word_root_map_data)
df_word_root_map.to_csv(output_word_root_map_path, index=False, encoding='utf-8')

print(f"word_root_map.csv created with {len(df_word_root_map)} entries.")
print(f"Sample of word_root_map.csv:\n{df_word_root_map.head()}")

# Optional: Print some statistics
total_words = len(df_word_root_map)
words_with_roots = df_word_root_map['root_id'].count()
print(f"\nTotal words processed: {total_words}")
print(f"Words successfully mapped to a root: {words_with_roots} ({words_with_roots / total_words:.2%})")
