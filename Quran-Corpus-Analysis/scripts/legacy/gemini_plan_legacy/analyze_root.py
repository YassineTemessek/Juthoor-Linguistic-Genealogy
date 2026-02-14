import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display

# ---------------------------------------------------------
# 1. البيانات (محاكاة لما ستجلبه من ملفات CSV)
# هذه آيات مختارة فيها جذر (رجم) وسياقات مختلفة
# ---------------------------------------------------------
data = [
    # سياق الطرد/الهجر
    {"ayah": "لئن لم تنته لأرجمنك واهجرني مليا", "context_type": "Expulsion"},
    {"ayah": "وإني عذت بربي وربكم أن ترجمون", "context_type": "Expulsion"}, 
    {"ayah": "قالوا يا شعيب ما نفقه كثيرا مما تقول وإنا لنراك فينا ضعيفا ولولا رهطك لرجمناك", "context_type": "Threat/Expulsion"},
    
    # سياق الظن/الكلام (الغيب)
    {"ayah": "سيقولون ثلاثة رابعهم كلبهم ويقولون خمسة سادسهم كلبهم رجما بالغيب", "context_type": "Metaphorical/Speaking"},
    {"ayah": "وما لهم به من علم إن يتبعون إلا الظن", "context_type": "Metaphorical/Speaking"}, # سياق مشابه للدعم

    # سياق مادي (نادر) أو عقاب في أمم سابقة
    {"ayah": "قالوا إنا تطيرنا بكم لئن لم تنتهوا لنرجمنكم وليمسنكم منا عذاب أليم", "context_type": "Physical/Punishment"},
]

df = pd.DataFrame(data)

# ---------------------------------------------------------
# 2. المعالجة الأولية (Preprocessing)
# الهدف: استخراج الكلمات المحيطة (Context Window)
# ---------------------------------------------------------

# دالة بسيطة لتنظيف النص (tokenization بدائي)
def get_context_words(text):
    # في المشروع الحقيقي سنستخدم مكتبات مثل NLTK أو PyArabic
    return text.split() 

# نطبق الدالة
df['tokens'] = df['ayah'].apply(get_context_words)

# ---------------------------------------------------------
# 3. بناء المصفوفة الرقمية (Vectorization)
# سنحول كل آية إلى أرقام بناءً على الكلمات الموجودة فيها
# ---------------------------------------------------------

# نستخدم CountVectorizer لعمل (Bag of Words)
# هذا هو "الإنكودر البسيط" الذي اقترحه ChatGPT (الخيار A)
vectorizer = CountVectorizer(analyzer='word')
X = vectorizer.fit_transform(df['ayah'])

# X الآن هي مصفوفة: صفوفها الآيات، وأعمدتها كل كلمات القرآن الموجودة في العينة

# ---------------------------------------------------------
# 4. التجميع (Clustering)
# نطلب من الكمبيوتر تقسيم الآيات إلى مجموعتين (Cluster = 2)
# ونرى هل سيفصل المعاني المعنوية عن المادية؟
# ---------------------------------------------------------

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10) # Added n_init to suppress warning
kmeans.fit(X)
df['cluster_id'] = kmeans.labels_

# ---------------------------------------------------------
# 5. عرض النتائج
# ---------------------------------------------------------
print("--- نتائج تحليل الآلة (بدون تدخل بشري) ---")
for i in range(3):
    print(f"\nCluster #{i}:")
    cluster_ayahs = df[df['cluster_id'] == i]['ayah'].tolist()
    for ayah in cluster_ayahs:
        print(f" - {ayah}")

# ---------------------------------------------------------
# 6. الرسم البياني (Visualization)
# تقليل الأبعاد لرؤية النقاط على الشاشة (PCA)
# ---------------------------------------------------------
pca = PCA(n_components=2)
coords = pca.fit_transform(X.toarray())

plt.figure(figsize=(10, 6))
colors = ['red', 'blue', 'green'] # Added a third color for 3 clusters

for i in range(len(coords)):
    # Reshape and re-order Arabic text for correct display
    reshaped_text = arabic_reshaper.reshape(df.iloc[i]['ayah'][:20]+"...")
    displayed_text = get_display(reshaped_text)
    
    plt.scatter(coords[i, 0], coords[i, 1], c=colors[df.iloc[i]['cluster_id']], s=100)
    plt.text(coords[i, 0]+0.02, coords[i, 1]+0.02, displayed_text, fontsize=12, fontname='Arial')

plt.title(get_display(arabic_reshaper.reshape("توزيع سياقات كلمة 'رجم' حسب التحليل الآلي")))
plt.grid(True)
plt.show()

