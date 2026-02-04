import pandas as pd
import re

csv_file_path = 'المعجم الاشتقاقي الجامع.xlsx - mushtaq.csv'

# Load the CSV file
df_mushtaq = pd.read_csv(csv_file_path)

print("Original DataFrame head:")
print(df_mushtaq.head())
print("\nOriginal DataFrame columns:")
print(df_mushtaq.columns)

# Rename columns for easier access (assuming they are consistent)
df_mushtaq.columns = [
    'باب',
    'الفصل المعجمي',
    'المعنى المشترك للفصل',
    'التركيب',
    'المعنى المحوري للتركيب',
    'التطبيق القرآني (أمثلة)'
]

print("\nRenamed DataFrame columns:")
print(df_mushtaq.columns)

# Analyze 'الفصل المعجمي'
unique_alfasl = df_mushtaq['الفصل المعجمي'].dropna().unique()
print(f"\nNumber of unique entries in 'الفصل المعجمي': {len(unique_alfasl)}")
print(f"Sample unique entries from 'الفصل المعجمي': {unique_alfasl[:20]}")

# Analyze 'التركيب'
unique_altarkeeb = df_mushtaq['التركيب'].dropna().unique()
print(f"\nNumber of unique entries in 'التركيب': {len(unique_altarkeeb)}")
print(f"Sample unique entries from 'التركيب': {unique_altarkeeb[:20]}")

# Filter for valid Arabic root patterns (2-4 Arabic letters) in 'الفصل المعجمي'
def is_arabic_root(text):
    if pd.isna(text):
        return False
    # Check if text contains only Arabic letters and length is between 2 and 4
    return bool(re.fullmatch(r'[\u0621-\u064A]{2,4}', text.replace(" ", ""))) # Remove spaces for checking length

df_filtered_alfasl = df_mushtaq[df_mushtaq['الفصل المعجمي'].apply(is_arabic_root)]

print(f"\nNumber of valid Arabic roots (2-4 letters) in 'الفصل المعجمي': {len(df_filtered_alfasl['الفصل المعجمي'].unique())}")
print(f"Sample filtered 'الفصل المعجمي' entries: {df_filtered_alfasl['الفصل المعجمي'].unique()[:20]}")

# Examine relationship between 'الفصل المعجمي' and 'التركيب'
# Get rows where both are present and differ
df_diff_roots = df_mushtaq[
    df_mushtaq['الفصل المعجمي'].notna() & 
    df_mushtaq['التركيب'].notna() & 
    (df_mushtaq['الفصل المعجمي'] != df_mushtaq['التركيب'])
]

print(f"\nNumber of rows where 'الفصل المعجمي' and 'التركيب' differ: {len(df_diff_roots)}")
if not df_diff_roots.empty:
    print("Sample rows where 'الفصل المعجمي' and 'التركيب' differ:")
    print(df_diff_roots[['الفصل المعجمي', 'التركيب', 'المعنى المحوري للتركيب']].head())

# Further analysis: combine meanings for similar roots if needed
# For now, let's just focus on unique roots from 'الفصل المعجمي' that pass the filter
# And take the first 'المعنى المحوري للتركيب' associated with it.

# Create roots_dictionary_candidate
roots_dictionary_candidate = []
processed_roots = set()

for index, row in df_mushtaq.iterrows():
    root_letters_raw = row['الفصل المعجمي']
    
    if is_arabic_root(root_letters_raw):
        root_letters = root_letters_raw.replace(" ", "") # Clean spaces
        core_meaning = row['المعنى المحوري للتركيب']
        
        if root_letters not in processed_roots:
            roots_dictionary_candidate.append({
                'root_letters': root_letters,
                'description': core_meaning, # We'll refine this later if multiple meanings per root
                'category': row['باب'] # Using 'باب' as category for now
            })
            processed_roots.add(root_letters)

df_roots_dictionary = pd.DataFrame(roots_dictionary_candidate)
df_roots_dictionary['root_id'] = df_roots_dictionary.index + 1 # Assign unique ID

print(f"\nCandidate roots_dictionary.csv created with {len(df_roots_dictionary)} entries.")
print(df_roots_dictionary.head())

# This DataFrame (df_roots_dictionary) is a good starting point for roots_dictionary.csv.
# We will save it after further refinement.
