import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display

# 1) Read the manual experimental file
df = pd.read_csv("examples_rj.csv")

# 2) Use the full ayah text as the context
texts = df["text_ayah"].tolist()

# 3) Build a simple numerical representation (Bag of Words)
# We use binary=True to just check for presence/absence, or standard count
vectorizer = CountVectorizer(analyzer="word")
X = vectorizer.fit_transform(texts)

# 4) Cluster the ayahs into 2 groups (for this small example)
kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X)

# 5) Print results to see the semantic grouping
print("=== Clustering Results (bi-root: ر ج | full-root: ر ج م) ===")
for c in sorted(df["cluster"].unique()):
    print(f"\n--- Cluster {c} ---")
    sub = df[df["cluster"] == c]
    for _, row in sub.iterrows():
        print(f"[{row['sura']}:{row['ayah']}] {row['word_form']} -> {row['text_ayah'][:60]}...")

# 6) Simple 2D Visualization
pca = PCA(n_components=2)
coords = pca.fit_transform(X.toarray())

plt.figure(figsize=(10, 7))
colors = {0: "red", 1: "blue", 2: "green"}

for i, row in df.iterrows():
    x, y = coords[i, 0], coords[i, 1]
    c = colors[row["cluster"]]
    plt.scatter(x, y, c=c, s=100)
    
    # Reshape Arabic text for the label
    label_text = f"{row['sura']}:{row['ayah']} {row['word_form']}"
    reshaped_label = get_display(arabic_reshaper.reshape(label_text))
    
    plt.text(x + 0.02, y + 0.02, reshaped_label, fontsize=10)

title_text = "سياقات الجذر الثنائي (ر ج) عبر تركيب (ر ج م)"
plt.title(get_display(arabic_reshaper.reshape(title_text)))
plt.grid(True)
plt.show()
