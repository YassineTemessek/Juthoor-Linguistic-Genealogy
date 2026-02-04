import pandas as pd
import re
import os

# Paths
# We assume the script is running from inside 'chatgpt_plan_active' or we handle paths relative to root
# Adjusting paths to be safe relative to where we run the command
input_path = '../المعجم الاشتقاقي الجامع.xlsx - mushtaq.csv' 
output_path = 'bi_root_dictionary.csv'

# Load Data
try:
    df = pd.read_csv(input_path)
except FileNotFoundError:
    print(f"Error: Could not find {input_path}. Make sure you run this script from the 'chatgpt_plan_active' directory.")
    exit()

# Rename columns based on previous inspection
# The CSV has headers: الباب, الفصل المعجمي, المعنى المشترك للفصل, التركيب, المعنى المحوري للتركيب, التطبيق القرآني (أمثلة)
df.columns = [
    'door', 
    'bi_root_raw',      # الفصل المعجمي (The Bi-Root Origin)
    'bi_root_meaning', 
    'tri_root_raw',     # التركيب (The Expanded Root)
    'tri_root_meaning', # المعنى المحوري
    'examples'
]

def clean_root(text):
    if pd.isna(text):
        return None
    # Remove spaces, hyphens, and non-Arabic chars, keep Arabic letters
    # Dr. Jabal often writes "ب - ب" or "ب ب". We want "بب"
    clean = re.sub(r'[^\u0621-\u064A]', '', text)
    return clean

processed_data = []

print("Processing Dr. Jabal's Dictionary...")

for index, row in df.iterrows():
    bi_raw = row['bi_root_raw']
    tri_raw = row['tri_root_raw']
    meaning = row['tri_root_meaning']
    
    bi_root = clean_root(bi_raw)
    # Handle cases where tri_root might be multiple forms like "أ و ب - أ ي ب"
    # We take the first one for now or split them. Let's take the first valid one.
    if isinstance(tri_raw, str) and '-' in tri_raw:
        tri_raw = tri_raw.split('-')[0]
    
    tri_root = clean_root(tri_raw)
    
    if bi_root and tri_root:
        # Calculate extra letters (The Mutation)
        # This is a naive calc, just for info. 
        # Real logic is more complex (finding which letter was added), but this suffices for data structure.
        
        processed_data.append({
            'bi_root': bi_root,
            'tri_root': tri_root,
            'core_meaning': meaning,
            'original_chapter': bi_raw
        })

# Create DataFrame
df_out = pd.DataFrame(processed_data)

# Save locally in the active plan folder
df_out.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"Success! Created '{output_path}' with {len(df_out)} entries.")
print("Sample Hierarchy:")
print(df_out[['bi_root', 'tri_root', 'core_meaning']].head(10))
