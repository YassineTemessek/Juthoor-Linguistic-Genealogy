import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display

# --- 1. Load All Data ---
quran_text_path = 'quran_text.csv'
roots_dict_path = 'roots_dictionary.csv'
word_root_map_path = 'word_root_map.csv'

df_quran_text = pd.read_csv(quran_text_path)
df_roots_dictionary = pd.read_csv(roots_dict_path)
df_word_root_map = pd.read_csv(word_root_map_path)

# Ensure 'root_id' is integer, fill NaN with a placeholder or drop
df_word_root_map['root_id'] = df_word_root_map['root_id'].fillna(-1).astype(int)

# Create a lookup for root_letters to root_id and vice-versa
root_letters_to_id = pd.Series(df_roots_dictionary.root_id.values, index=df_roots_dictionary.root_letters).to_dict()
root_id_to_letters = pd.Series(df_roots_dictionary.root_letters.values, index=df_roots_dictionary.root_id).to_dict()

# --- 2. Define Target Root ---
target_root_letters = "رجم" # Example: The root 'رجم'
target_root_id = root_letters_to_id.get(target_root_letters)

if target_root_id is None:
    print(f"Target root '{target_root_letters}' not found in roots_dictionary.csv. Exiting.")
    exit()

print(f"Analyzing target root: '{target_root_letters}' (ID: {target_root_id})")

# --- 3. Extract Relevant Ayahs ---
# Find all ayah_ids that contain the target root
ayah_ids_with_target_root = df_word_root_map[
    (df_word_root_map['root_letters'] == target_root_letters)
]['ayah_id'].unique()

print(f"Found {len(ayah_ids_with_target_root)} ayahs containing the root '{target_root_letters}'.")

# Filter quran_text to get the full text of these ayahs
df_target_ayahs = df_quran_text[df_quran_text['id'].isin(ayah_ids_with_target_root)].copy()

# --- 4. Co-occurrence Vectorization (Root-based) ---
# Create a matrix where each row is an ayah, and columns are other roots
# Values indicate presence (1) or absence (0) of that root in the ayah

# Get all unique root IDs present in our word_root_map (excluding the target root)
all_co_occurring_root_ids = df_word_root_map[
    (df_word_root_map['root_id'] != -1) & # Exclude unmapped words
    (df_word_root_map['root_id'] != target_root_id)
]['root_id'].unique()

# Sort for consistent vector dimension order
all_co_occurring_root_ids.sort()

# Create a mapping from root_id to its index in the co-occurrence vector
root_id_to_vector_index = {root_id: i for i, root_id in enumerate(all_co_occurring_root_ids)}

# Prepare co-occurrence vectors for each target ayah
ayah_co_occurrence_vectors = []
ayah_texts = []

for ayah_id in ayah_ids_with_target_root:
    # Get all words (and their mapped roots) for the current ayah
    ayah_words_roots = df_word_root_map[df_word_root_map['ayah_id'] == ayah_id]
    
    # Get unique root_ids present in this ayah (excluding the target root itself and unmapped)
    roots_in_current_ayah = ayah_words_roots[
        (ayah_words_roots['root_id'] != -1) &
        (ayah_words_roots['root_id'] != target_root_id)
    ]['root_id'].unique()

    # Create a zero vector for co-occurrence
    co_occurrence_vector = np.zeros(len(all_co_occurring_root_ids))
    
    for root_id_in_ayah in roots_in_current_ayah:
        if root_id_in_ayah in root_id_to_vector_index:
            vector_index = root_id_to_vector_index[root_id_in_ayah]
            co_occurrence_vector[vector_index] = 1 # Mark presence

    ayah_co_occurrence_vectors.append(co_occurrence_vector)
    
    # Get the full text of the ayah for display
    ayah_full_text = df_quran_text[df_quran_text['id'] == ayah_id]['text_with_diacritics'].iloc[0]
    ayah_texts.append(ayah_full_text)

# Convert list of vectors to a numpy array
X_co_occurrence = np.array(ayah_co_occurrence_vectors)

if len(X_co_occurrence) < 2:
    print("Not enough data points for clustering (less than 2 ayahs with target root). Exiting.")
    exit()

# --- 5. Clustering and Visualization ---
n_clusters = min(3, len(X_co_occurrence)) # Use max 3 clusters, but not more than data points
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
kmeans.fit(X_co_occurrence)
cluster_labels = kmeans.labels_

# Add cluster labels to our DataFrame of target ayahs for easy access
df_target_ayahs['cluster_id'] = cluster_labels
df_target_ayahs['full_text'] = ayah_texts # Store full text for display

print(f"\nClustering results for '{target_root_letters}' with {n_clusters} clusters:")
for i in range(n_clusters):
    print(f"\nCluster #{i}:")
    cluster_ayahs = df_target_ayahs[df_target_ayahs['cluster_id'] == i]
    for _, ayah_row in cluster_ayahs.iterrows():
        # Reshape and re-order Arabic text for correct display
        reshaped_text = arabic_reshaper.reshape(ayah_row['full_text'])
        displayed_text = get_display(reshaped_text)
        print(f" - {ayah_row['id']}: {displayed_text}")

# --- Visualization ---
if len(X_co_occurrence[0]) > 0: # Ensure there are features for PCA
    pca = PCA(n_components=2)
    coords = pca.fit_transform(X_co_occurrence)

    plt.figure(figsize=(12, 8))
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink', 'gray'][:n_clusters]

    for i in range(len(coords)):
        plt.scatter(coords[i, 0], coords[i, 1], c=colors[cluster_labels[i]], s=100, alpha=0.7)
        
        # Reshape and re-order Arabic text for correct display in plot labels
        ayah_text_to_display = df_target_ayahs.iloc[i]['full_text']
        reshaped_text = arabic_reshaper.reshape(f"({df_target_ayahs.iloc[i]['id']}) {ayah_text_to_display[:30]}...") # Limit text length
        displayed_text = get_display(reshaped_text)
        
        plt.text(coords[i, 0]+0.02, coords[i, 1]+0.02, displayed_text, 
                 fontsize=9, fontname='Arial', ha='left', va='center')

    title_text = f"توزيع سياقات الجذر '{target_root_letters}' حسب التحليل الآلي"
    plt.title(get_display(arabic_reshaper.reshape(title_text)), fontsize=14)
    plt.xlabel(get_display(arabic_reshaper.reshape("مكون PCA 1")),
               fontsize=12)
    plt.ylabel(get_display(arabic_reshaper.reshape("مكون PCA 2")),
               fontsize=12)
    plt.grid(True)
    plt.show()
else:
    print("Cannot perform PCA and visualization: No co-occurring roots found for the target root.")
