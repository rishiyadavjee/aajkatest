import math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Documents
docs = [
    'What are the library timings during exam week?',
    'Where is the medical room and when is the doctor available?',
    'How do I get a duplicate ID card from the admin office?',
    'What are the canteen timings and is food available after 8 pm?',
    'Can visitors enter the hostel after 8 pm?',
    'How do I book the sports ground for a match?'
]

print('=== Q4(c) ===')
vec = TfidfVectorizer(stop_words='english', smooth_idf=False, norm=None)
X_tfidf = vec.fit_transform(docs)
feature_names = vec.get_feature_names_out()
print('Vocabulary size:', len(feature_names))

timings_idx = list(feature_names).index('timings')
sklearn_tfidf_timings_d4 = X_tfidf[3, timings_idx]
print('sklearn TF-IDF of timings in D4:', sklearn_tfidf_timings_d4)

# Manual math
N = len(docs)
df_timings = sum(1 for d in docs if 'timings' in d.lower())
manual_idf = math.log(N / df_timings) + 1.0
tf_timings_d4 = 1.0
manual_tfidf = tf_timings_d4 * manual_idf
print(f'Manual IDF: ln({N}/{df_timings}) + 1 = {manual_idf:.6f}')
print(f'Manual TF-IDF: {manual_tfidf:.6f}')
print('Match?', math.isclose(sklearn_tfidf_timings_d4, manual_tfidf))

# D4 top-3 terms
d4_row = X_tfidf[3].toarray().flatten()
d4_terms = sorted([(feature_names[i], d4_row[i]) for i in range(len(feature_names)) if d4_row[i] > 0], key=lambda x: x[1], reverse=True)
print('D4 terms sorted:', d4_terms[:5])

print('\n=== Q4(d) Chatbot ===')
cb_vec = TfidfVectorizer(stop_words='english')
cb_tfidf = cb_vec.fit_transform(docs)

d = 6
tau = 0.20 + 0.05 * (d % 4) # 0.20 + 0.05 * 2 = 0.30
print(f'Threshold tau for d={d}: {tau:.2f}')

queries = [
    ('q1', 'library timings in exam week'),
    ('q2', 'where can I eat late at night'),
    ('q3', 'I lost my ID card'),
    ('q4', 'office timings'),
    ('q5', 'book a room in hostel'),
    ('q6', 'can my parents visit the hostel at night')
]

for q_id, q_text in queries:
    q_vec = cb_vec.transform([q_text])
    norm_q = np.linalg.norm(q_vec.toarray())
    if norm_q == 0:
        print(f'{q_id} ("{q_text}"): ALL-ZERO VECTOR -> Fallback: Clarifying question asked.')
        continue
    sims = cosine_similarity(q_vec, cb_tfidf).flatten()
    sorted_indices = np.argsort(sims)[::-1]
    best_idx = sorted_indices[0]
    best_score = sims[best_idx]
    second_idx = sorted_indices[1]
    second_score = sims[second_idx]
    
    if abs(best_score - second_score) <= 0.01 and best_score >= tau:
        status = f'TIE between D{best_idx+1} ({best_score:.4f}) and D{second_idx+1} ({second_score:.4f}) -> Clarifying question asked'
    elif best_score >= tau:
        status = f'Answered with D{best_idx+1} (score: {best_score:.4f})'
    else:
        status = f'Fallback: score {best_score:.4f} < tau ({tau:.2f})'
    print(f'{q_id} ("{q_text}") -> Best: D{best_idx+1}, Score: {best_score:.4f} -> {status}')

print('\n=== Q4(e) Sentiment Analysis ===')
sia = SentimentIntensityAnalyzer()
sentences = [
    'The canteen food is not bad at all.',
    'Great, another two-hour queue at the admin office.',
    'Library staff were helpful but the wifi was terrible.',
    'Hostel rooms are clean.'
]
for s in sentences:
    tb = TextBlob(s).sentiment
    vad = sia.polarity_scores(s)
    print(f'Sentence: "{s}"')
    print(f'  TextBlob: polarity={tb.polarity:.4f}, subjectivity={tb.subjectivity:.4f}')
    print(f'  VADER: compound={vad["compound"]:.4f}, pos={vad["pos"]}, neg={vad["neg"]}, neu={vad["neu"]}')
