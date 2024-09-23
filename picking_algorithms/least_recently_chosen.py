from datetime import datetime

def pick_questions(qa_pairs, processed_dict, num_questions):
    never_sent = [q for q in qa_pairs.keys() if q not in processed_dict]
    sent_questions = [q for q in qa_pairs.keys() if q in processed_dict]
    
    sorted_sent = sorted(sent_questions, key=lambda q: processed_dict[q])
    all_sorted = never_sent + sorted_sent
    
    return all_sorted[:num_questions]