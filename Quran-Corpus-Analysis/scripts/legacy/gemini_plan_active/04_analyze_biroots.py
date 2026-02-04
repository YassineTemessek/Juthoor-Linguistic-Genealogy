import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display
import seaborn as sns

# --- Config ---
INPUT_FILE = "auto_examples_expanded.csv"
TARGET_BI_ROOT = "كت"  # Let's analyze the "K-T" family (Writing vs Hiding)

# 1. Load Data
df = pd.read_csv(INPUT_FILE)

# Filter for the target Bi-root
df_bi = df[df['bi_root'] == TARGET_BI_ROOT].copy()

print(f"Analyzing Bi-Root: {TARGET_BI_ROOT}")
print(f"Total Ayahs found: {len(df_bi)}")
print(f"Tri-roots involved: {df_bi['tri_root'].unique()}")

# 2. Vectorize (Context Analysis)
vectorizer = CountVectorizer(analyzer="word")
X = vectorizer.fit_transform(df_bi["text_ayah"])

# 3. Clustering (Can we separate the meanings?)
# We set clusters equal to the number of tri-roots to see if they align
n_clusters = len(df_bi['tri_root'].unique()) 
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
df_bi["cluster"] = kmeans.fit_predict(X)

# 4. Visualization
pca = PCA(n_components=2)
coords = pca.fit_transform(X.toarray())

# Create a nice plot
plt.figure(figsize=(12, 8))

# Map tri-roots to colors/markers for comparison
unique_tri_roots = df_bi['tri_root'].unique()
palette = sns.color_palette("hsv", len(unique_tri_roots))
root_color_map = dict(zip(unique_tri_roots, palette))

# Plot each point
for i, row in df_bi.reset_index().iterrows():
    x, y = coords[i, 0], coords[i, 1]
    
    # Color by Tri-root (The "Truth" we want to see if the machine found)
    color = root_color_map[row['tri_root']]
    
    # Marker style by Cluster (The Machine's opinion)
    marker = 'o' if row['cluster'] == 0 else 'x' 
    if row['cluster'] > 1: marker = '^'
    
    plt.scatter(x, y, color=color, s=100, label=row['tri_root'], marker=marker, alpha=0.7)
    
    # Label some points
    if i % 5 == 0: # Label every 5th point to avoid clutter
        reshaped_label = get_display(arabic_reshaper.reshape(f"{row['tri_root']}"))
        plt.text(x+0.02, y+0.02, reshaped_label, fontsize=9)

# Deduplicate legend
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys(), title="Tri-Roots")

title_text = f"تحليل عائلة الجذر الثنائي ({TARGET_BI_ROOT})"
plt.title(get_display(arabic_reshaper.reshape(title_text)))
plt.grid(True)
plt.show()

# 5. Print Text Samples per Cluster
print("\n=== Semantic Clustering Results ===")
for c in sorted(df_bi["cluster"].unique()):
    print(f"\n--- Cluster {c} ---")
    # Show top 3 examples
    sub = df_bi[df_bi["cluster"] == c].head(3)
    for _, row in sub.iterrows():
        print(f"[{row['tri_root']}] {row['text_ayah'][:60]}...")
