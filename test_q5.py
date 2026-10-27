import re
from collections import deque
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- Graph Setup ---
edges = [
    ('G', 'A'), ('G', 'P'), ('A', 'C'), ('A', 'L'),
    ('P', 'S'), ('C', 'L'), ('C', 'H'), ('L', 'B'),
    ('S', 'H'), ('H', 'M'), ('B', 'M')
]
nodes = sorted(list(set([u for u, v in edges] + [v for u, v in edges])))
adj_raw = {u: [] for u in nodes}
for u, v in edges:
    adj_raw[u].append(v)
    adj_raw[v].append(u)
degrees = {u: len(adj_raw[u]) for u in nodes}

def sort_neighbours(nbrs):
    return sorted(nbrs, key=lambda x: (degrees[x], x), reverse=True)

adj_list = {u: sort_neighbours(adj_raw[u]) for u in nodes}

node_names = {
    'G': 'Main Gate', 'A': 'Admin Office', 'P': 'Parking',
    'C': 'Canteen', 'L': 'Library', 'S': 'Sports Ground',
    'H': 'Hostel', 'B': 'Lab Block', 'M': 'Medical Room'
}

def bfs_path(start, goal):
    if start == goal:
        return [start]
    queue = deque([start])
    visited = {start}
    parent = {start: None}
    found = False
    while queue:
        curr = queue.popleft()
        if curr == goal:
            found = True
            break
        for nbr in adj_list[curr]:
            if nbr not in visited:
                visited.add(nbr)
                parent[nbr] = curr
                queue.append(nbr)
    if not found:
        return None
    path = []
    c = goal
    while c:
        path.append(c)
        c = parent[c]
    path.reverse()
    return path

# --- Knowledge Base & Forward Chaining ---
kb_rules = [
    ('R1', ['student', 'has_id'], 'can_enter_campus'),
    ('R2', ['visitor', 'has_appointment'], 'can_enter_campus'),
    ('R3', ['can_enter_campus', 'library_member'], 'can_enter_library'),
    ('R4', ['exam_week'], 'extended_library_hours'),
    ('R5', ['extended_library_hours', 'after_8pm'], 'library_open_late'),
    ('R6', ['can_enter_library', 'library_open_late'], 'allow_route_library'),
    ('R7', ['fever', 'cough'], 'flu_suspected'),
    ('R8', ['flu_suspected'], 'visit_medical'),
    ('R9', ['visit_medical', 'after_8pm'], 'call_warden'),
    ('R10', ['call_warden', 'hostel_resident'], 'escort_to_medical'),
    ('R11', ['visitor', 'can_enter_campus', 'after_8pm'], 'deny_hostel_entry'),
    ('R12', ['escort_to_medical'], 'allow_route_hostel_medical'),
]

def forward_chain(initial_facts):
    facts = set(initial_facts)
    justification = {}
    while True:
        fired = False
        for r_name, ants, conc in kb_rules:
            if all(a in facts for a in ants) and (conc not in facts):
                facts.add(conc)
                justification[conc] = (r_name, ants)
                fired = True
                break
        if not fired:
            break
    return facts, justification

def get_why_explanation(fact, justification, initial_facts):
    if fact not in justification:
        if fact in initial_facts:
            return f"'{fact}' is an initial base fact."
        return f"'{fact}' could not be derived from the available facts."
    
    r_name, ants = justification[fact]
    lines = [f"'{fact}' was derived by rule {r_name} because {ants} were established."]
    for a in ants:
        if a in justification:
            lines.append(f"  - {get_why_explanation(a, justification, initial_facts)}")
        elif a in initial_facts:
            lines.append(f"  - '{a}' is a known base fact.")
    return "\n".join(lines)

# --- NLP Chatbot Setup ---
faq_docs = [
    'What are the library timings during exam week?',
    'Where is the medical room and when is the doctor available?',
    'How do I get a duplicate ID card from the admin office?',
    'What are the canteen timings and is food available after 8 pm?',
    'Can visitors enter the hostel after 8 pm?',
    'How do I book the sports ground for a match?'
]
faq_answers = {
    0: "D1: Library timings are extended until late hours (after 8 PM) during exam week for library members.",
    1: "D2: The medical room (M) is next to Hostel/Lab block. A doctor is available during working hours and emergency on-call.",
    2: "D3: To get a duplicate ID card, visit the Admin Office (A) with your enrolment details and application form.",
    3: "D4: Canteen timings are 12 PM - 3 PM for lunch; snacks are available until 8 PM. Canteen is closed after 8 PM.",
    4: "D5: Visitors are NOT allowed to enter the hostel after 8 PM under security policy (Rule R11).",
    5: "D6: You can book the sports ground (S) by submitting a match request form at the sports coordinator's desk."
}
cb_vec = TfidfVectorizer(stop_words='english')
cb_tfidf = cb_vec.fit_transform(faq_docs)
d_val = 6
TAU = 0.20 + 0.05 * (d_val % 4) # 0.30

# Synonym mapping for campus locations
synonyms = {
    'gate': 'G', 'main gate': 'G', 'entrance': 'G',
    'admin': 'A', 'admin office': 'A', 'office': 'A',
    'parking': 'P',
    'canteen': 'C', 'food court': 'C', 'cafeteria': 'C',
    'library': 'L',
    'sports': 'S', 'ground': 'S', 'sports ground': 'S',
    'hostel': 'H',
    'lab': 'B', 'lab block': 'B', 'laboratory': 'B',
    'medical': 'M', 'medical room': 'M', 'doctor': 'M', 'dispensary': 'M', 'clinic': 'M'
}

def parse_route_request(text):
    text_clean = text.lower()
    # Match patterns like "from <X> to <Y>" or "take me from <X> to <Y>" or "<X> to <Y>"
    m = re.search(r'from\s+([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:$|\?|\.|\bafter\b)', text_clean)
    if not m:
        return None, None
    src_raw = m.group(1).strip()
    dst_raw = m.group(2).strip()
    
    src_node = None
    dst_node = None
    
    for syn, node in sorted(synonyms.items(), key=lambda x: len(x[0]), reverse=True):
        if syn in src_raw and not src_node:
            src_node = node
        if syn in dst_raw and not dst_node:
            dst_node = node
            
    return src_node, dst_node

def campusbot(text, facts):
    src, dst = parse_route_request(text)
    
    if src and dst:
        # Route Request
        print(f"[CampusBot Routing] Detected route request: {node_names[src]} ({src}) -> {node_names[dst]} ({dst})")
        
        derived_facts, justification = forward_chain(facts)
        
        # Check KB Gating Rules:
        # 1. Going to L requires allow_route_library
        if dst == 'L':
            if 'allow_route_library' not in derived_facts:
                expl = get_why_explanation('allow_route_library', justification, facts)
                return (f"ACCESS DENIED to {node_names['L']}.\n"
                        f"Reason: Permission 'allow_route_library' was not granted.\n"
                        f"Explanation:\n{expl}")
                        
        # 2. Going H -> M after 8 PM requires allow_route_hostel_medical
        if (src, dst) == ('H', 'M') or ('hostel' in text.lower() and 'doctor' in text.lower()):
            if 'after_8pm' in facts:
                if 'allow_route_hostel_medical' not in derived_facts:
                    expl = get_why_explanation('allow_route_hostel_medical', justification, facts)
                    return (f"ACCESS DENIED from Hostel to Medical Room after 8 PM.\n"
                            f"Reason: 'allow_route_hostel_medical' is required.\n"
                            f"Explanation:\n{expl}")
                            
        # If permitted, get path from BFS
        path = bfs_path(src, dst)
        if path:
            path_str = " -> ".join([f"{n} ({node_names[n]})" for n in path])
            return f"ACCESS GRANTED!\nOptimal Path: {path_str} (Total distance: {len(path)-1} edges)."
        else:
            return f"No path found between {node_names[src]} and {node_names[dst]}."
            
    # Otherwise: Fallback to Q4 NLP Chatbot
    q_vec = cb_vec.transform([text])
    if np.linalg.norm(q_vec.toarray()) == 0:
        return "Chatbot Fallback: I could not understand your query because no keywords matched our FAQ database. Could you please rephrase or specify a campus facility (e.g. library, canteen, hostel)?"
        
    sims = cosine_similarity(q_vec, cb_tfidf).flatten()
    sorted_idx = np.argsort(sims)[::-1]
    best_i = sorted_idx[0]
    best_score = sims[best_i]
    second_i = sorted_idx[1]
    second_score = sims[second_i]
    
    if abs(best_score - second_score) <= 0.01 and best_score >= TAU:
        return (f"Chatbot Clarification: Your query could relate to multiple FAQs with similar relevance ({best_score:.2f}):\n"
                f"1) {faq_docs[best_i]}\n2) {faq_docs[second_i]}\nPlease clarify which topic you need.")
    elif best_score >= TAU:
        return f"Chatbot Answer (Matched FAQ {best_i+1}, score: {best_score:.4f}):\n{faq_answers[best_i]}"
    else:
        return f"Chatbot Fallback: Low confidence match (score {best_score:.4f} < threshold {TAU:.2f}). Please contact the admin helpdesk."

# Test runs
print('=== TEST RUN T1 ===')
fs1 = {'student', 'has_id', 'library_member', 'exam_week', 'after_8pm'}
print(campusbot("How do I go from the gate to the library?", fs1))

print('\n=== TEST RUN T2 ===')
fs1_no_exam = {'student', 'has_id', 'library_member', 'after_8pm'}
print(campusbot("How do I go from the gate to the library?", fs1_no_exam))

print('\n=== TEST RUN T3 ===')
fs2 = {'student', 'has_id', 'hostel_resident', 'fever', 'cough', 'after_8pm'}
print(campusbot("I have fever and cough, take me from hostel to the doctor", fs2))

print('\n=== TEST RUN T4 ===')
print(campusbot("where can I eat late at night", set()))

print('\n=== TEST RUN T5 (Own Test) ===')
print(campusbot("How do I go from admin office to lab block?", fs1))
