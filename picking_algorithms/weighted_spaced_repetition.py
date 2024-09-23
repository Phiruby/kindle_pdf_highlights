import random
from datetime import datetime, timedelta

def pick_questions(qa_pairs, processed_dict, num_questions):
    """
    Selects a specified number of questions from a set of question-answer pairs 
    using a weighted approach that considers both the length of the questions 
    and the time since they were last sent.

    Parameters:
    qa_pairs (dict): A dictionary where keys are questions and values are their corresponding answers.
    processed_dict (dict): A dictionary where keys are questions and values are timestamps 
                           indicating when the questions were last sent.
    num_questions (int): The number of questions to select.

    Returns:
    list: A list of selected questions, weighted by their length and the time since they were last sent.
    """
    current_time = datetime.now()
    questions = []
    
    for q in qa_pairs.keys():
        if q not in processed_dict:
            days_since = 30  # Give new questions high priority
        else:
            last_sent = datetime.strptime(processed_dict[q], '%Y-%m-%d %H:%M:%S')
            days_since = (current_time - last_sent).days
        
        length_weight = len(qa_pairs[q])
        time_weight = min(days_since, 30)  # Cap time weight at 30 days
        
        # Combine length and time weights
        combined_weight = length_weight * (1 + time_weight / 2)  # Adjust this formula as needed
        
        questions.append((q, combined_weight))
    
    # Sort questions by combined weight, highest first
    questions.sort(key=lambda x: x[1], reverse=True)
    
    # Select questions randomly, but weighted by their combined weight
    selected_questions = []
    remaining_questions = [q[0] for q in questions]
    remaining_weights = [q[1] for q in questions]
    
    while len(selected_questions) < num_questions and remaining_questions:
        chosen = random.choices(remaining_questions, weights=remaining_weights, k=1)[0]
        selected_questions.append(chosen)
        index = remaining_questions.index(chosen)
        remaining_questions.pop(index)
        remaining_weights.pop(index)
    
    return selected_questions