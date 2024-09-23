from datetime import datetime, timedelta

def pick_questions(qa_pairs, processed_dict, num_questions):
    current_time = datetime.now()
    questions = []
    
    for q in qa_pairs.keys():
        if q not in processed_dict:
            questions.append((q, 0))  # New questions have highest priority
        else:
            last_sent = datetime.strptime(processed_dict[q], '%Y-%m-%d %H:%M:%S')
            days_since = (current_time - last_sent).days
            priority = min(days_since, 30)  # Cap priority at 30 days
            questions.append((q, priority))
    
    questions.sort(key=lambda x: x[1], reverse=True)
    return [q[0] for q in questions[:num_questions]]