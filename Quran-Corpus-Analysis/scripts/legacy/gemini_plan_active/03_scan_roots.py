import pandas as pd

# --- Configuration ---
# Target Bi-roots to scan for (The "Fathers")
TARGET_BI_ROOTS = ['رج', 'كت', 'ضر'] 

# Paths
quran_path = '../quran_text.csv' # In root
dict_path = 'bi_root_dictionary.csv' # In current folder
output_path = 'auto_examples_expanded.csv'

# --- Load Data ---
print("Loading data...")
try:
    df_quran = pd.read_csv(quran_path)
    df_dict = pd.read_csv(dict_path)
except FileNotFoundError as e:
    print(f"Error loading files: {e}")
    exit()

# --- Helper to get children ---
def get_tri_roots_for_bi(bi_root):
    # Filter dictionary for this bi_root
    daughters = df_dict[df_dict['bi_root'] == bi_root]['tri_root'].unique()
    return daughters

# --- Scanning Logic ---
results = []

print(f"Scanning for Bi-roots: {TARGET_BI_ROOTS}...")

for bi in TARGET_BI_ROOTS:
    # 1. Get all Tri-roots (e.g., for 'رج' -> 'رجم', 'رجل', 'رجو'...)
    tri_roots = get_tri_roots_for_bi(bi)
    print(f" > Bi-root '{bi}' has daughters: {list(tri_roots)}")
    
    for tri in tri_roots:
        if not isinstance(tri, str) or len(tri) < 3: 
            continue
            
        # 2. Build Regex: Find the tri-root letters contiguously
        # We search in 'text_clean' which has no diacritics
        # Pattern: simply the letters joined (e.g., "رجم")
        pattern = tri 
        
        # 3. Scan Quran
        # We look for the pattern inside the clean text
        matches = df_quran[df_quran['text_clean'].str.contains(pattern, na=False)]
        
        for _, row in matches.iterrows():
            # Find the specific word that matched (for the 'word_form' column)
            # We split the clean text and check each word
            words = str(row['text_clean']).split()
            matched_word = "N/A"
            
            for w in words:
                if pattern in w:
                    matched_word = w
                    break
            
            results.append({
                'sura': row['surah_no'],
                'ayah': row['ayah_no'],
                'word_form': matched_word,
                'bi_root': bi,
                'tri_root': tri,
                'text_ayah': row['text_with_diacritics'] # We save the original text for display
            })

# --- Save Results ---
df_results = pd.DataFrame(results)
df_results.to_csv(output_path, index=False, encoding='utf-8-sig')

print("\nScan Complete.")
print(f"Found {len(df_results)} occurrences.")
print(f"Saved to '{output_path}'.")
print("Sample:")
print(df_results.head())
