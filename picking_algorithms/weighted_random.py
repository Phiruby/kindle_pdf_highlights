import random

def pick_questions(qa_pairs, processed_dict, num_questions):
    questions = list(qa_pairs.keys())
    weights = [len(qa_pairs[q]) for q in questions]
    
    selected_questions = []
    while len(selected_questions) < num_questions and questions:
        chosen = random.choices(questions, weights=weights, k=1)[0]
        selected_questions.append(chosen)
        index = questions.index(chosen)
        questions.pop(index)
        weights.pop(index)
    
    return selected_questions