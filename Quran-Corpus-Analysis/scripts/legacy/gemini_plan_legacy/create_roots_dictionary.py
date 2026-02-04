import pandas as pd
import re

csv_file_path = 'المعجم الاشتقاقي الجامع.xlsx - mushtaq.csv'
output_roots_csv_path = 'roots_dictionary.csv'

# Load the CSV file
df_mushtaq = pd.read_csv(csv_file_path)

# Rename columns for easier access
df_mushtaq.columns = [
    'chapter', 
    'lexical_chapter_root_raw', 
    'common_meaning_lexical_chapter',
    'structure_raw', 
    'core_meaning_structure',
    'quranic_examples'
]

# Function to clean and validate roots
def clean_and_validate_root(root_text):
    if pd.isna(root_text):
        return None
    # Handle entries like "أ و ب - أ ي ب" by taking the first part
    if ' - ' in root_text:
        root_text = root_text.split(' - ')[0]
    
    # Remove all non-Arabic characters and spaces
    clean_root = re.sub(r'[^\u0621-\u064A]', '', root_text)
    
    # Check if length is between 2 and 4 Arabic letters
    if 2 <= len(clean_root) <= 4:
        return clean_root
    return None

# Apply cleaning and validation to 'structure_raw' to get potential roots
df_mushtaq['root_letters'] = df_mushtaq['structure_raw'].apply(clean_and_validate_root)

# Filter out rows where root_letters could not be extracted or validated
df_filtered_roots = df_mushtaq.dropna(subset=['root_letters'])

# Group by 'root_letters' to handle cases where one root might have multiple entries
# Concatenate descriptions if a root appears multiple times
roots_data = []
for root, group in df_filtered_roots.groupby('root_letters'):
    descriptions = group['core_meaning_structure'].dropna().tolist()
    # Use lexical_chapter_root_raw as parent_root, take the first valid one if multiple
    parent_root = group['lexical_chapter_root_raw'].dropna().iloc[0] if not group['lexical_chapter_root_raw'].dropna().empty else None
    
    # Combine descriptions
    combined_description = " / ".join(descriptions)

    roots_data.append({
        'root_letters': root,
        'description': combined_description,
        'parent_root': parent_root # Using this as category for now
    })

df_roots_dictionary = pd.DataFrame(roots_data)
df_roots_dictionary['root_id'] = df_roots_dictionary.index + 1 # Assign unique ID

# Reorder columns to match schema: root_id, root_letters, description, category
df_roots_dictionary = df_roots_dictionary[['root_id', 'root_letters', 'description', 'parent_root']]
df_roots_dictionary.rename(columns={'parent_root': 'category'}, inplace=True)

# Save to CSV
df_roots_dictionary.to_csv(output_roots_csv_path, index=False, encoding='utf-8')

print(f"roots_dictionary.csv created with {len(df_roots_dictionary)} entries.")
print(f"Sample of roots_dictionary.csv:\n{df_roots_dictionary.head()}")