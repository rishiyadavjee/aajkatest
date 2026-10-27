import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import pandas as pd

stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

sentences = [
    ("S1", "The students were studying in the libraries during the exams."),
    ("S2", "Visitors entering hostels after hours are being stopped.")
]

for s_id, text in sentences:
    print(f"\n=== Sentence {s_id}: '{text}' ===")
    tokens = word_tokenize(text)
    
    table_rows = []
    for t in tokens:
        if not t.isalnum():
            continue
        is_stop = t.lower() in stop_words
        stem = stemmer.stem(t)
        lem_def = lemmatizer.lemmatize(t.lower())
        lem_v = lemmatizer.lemmatize(t.lower(), pos='v')
        table_rows.append({
            'Token': t,
            'Stopword?': 'Yes' if is_stop else 'No',
            'Porter Stem': stem,
            'WordNet Lemma (default)': lem_def,
            'WordNet Lemma (pos="v")': lem_v
        })
    df = pd.DataFrame(table_rows)
    print(df.to_string(index=False))

print("\n--- Two words where stem and lemma differ ---")
words_to_compare = ['studying', 'libraries', 'entering', 'hostels']
for w in words_to_compare:
    print(f"Word: '{w}' -> Porter Stem: '{stemmer.stem(w)}' | WordNet Lemma: '{lemmatizer.lemmatize(w)}' | WordNet Lemma(v): '{lemmatizer.lemmatize(w, pos='v')}'")
