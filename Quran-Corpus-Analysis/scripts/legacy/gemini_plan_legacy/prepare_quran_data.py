import json
import pandas as pd
import re

# Define the path to the holy_quran.json file
json_file_path = 'quran_dataset/data/holy_quran.json'
output_csv_path = 'quran_text.csv'

# Load the JSON data
with open(json_file_path, 'r', encoding='utf-8') as f:
    quran_data = json.load(f)

# Prepare lists to store the data
quran_text_data = []

# Iterate through surahs and ayahs
for surah in quran_data['data']['surahs']:
    surah_no = surah['number']
    
    for ayah in surah['ayahs']:
        ayah_no = ayah['numberInSurah']
        text_with_diacritics = ayah['text']
        
        # Clean the text: remove diacritics and other non-alphabetic characters
        # This regex keeps only Arabic letters (including Hamza forms) and spaces
        text_clean = re.sub(r'[^\u0621-\u064A\s]+', '', text_with_diacritics)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip() # Replace multiple spaces with single space

        quran_text_data.append({
            'id': f"{surah_no}:{ayah_no}", # Unique ID for ayah
            'surah_no': surah_no,
            'ayah_no': ayah_no,
            'text_with_diacritics': text_with_diacritics, # Keep original for reference
            'text_clean': text_clean
        })

# Create a Pandas DataFrame
df_quran_text = pd.DataFrame(quran_text_data)

# Save the DataFrame to a CSV file
df_quran_text.to_csv(output_csv_path, index=False, encoding='utf-8')

print(f"Quran text processed and saved to {output_csv_path}")
print(f"Total ayahs processed: {len(df_quran_text)}")
print(f"Sample of data:\n{df_quran_text.head()}")
