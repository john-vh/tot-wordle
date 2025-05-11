import os
import re
import pandas as pd
from tot.tasks.base import Task
from src.tot.prompts.wordle import * 


def evaluate_guess(guess, target):
    new_guess = "Invalid guess or target"
    match = re.search(r'[^A-Z]?([A-Z]{5})[^A-Z]?', guess)
    if match:
        new_guess = match.group(1).lower()
    else:
        return new_guess
    
    feedback = ['⬛'] * 5
    letter_counts = {}
    
    for letter in target:
        letter_counts[letter] = letter_counts.get(letter, 0) + 1
    
    for i in range(5):
        if new_guess[i] == target[i]:
            feedback[i] = '🟩'
            letter_counts[new_guess[i]] -= 1
    
    for i in range(5):
        if feedback[i] != '🟩' and new_guess[i] in letter_counts and letter_counts[new_guess[i]] > 0:
            feedback[i] = '🟨'
            letter_counts[new_guess[i]] -= 1
    
    return ''.join(feedback)

def format_guesses_and_feedback(guesses, target):
    formatted_guesses = []
    formatted_feedback = []
    
    for guess in guesses:
        formatted_guesses.append(guess)
        formatted_feedback.append(evaluate_guess(guess, target))
    
    return '\n'.join(formatted_guesses), '\n'.join(formatted_feedback)

class WordleTask(Task):
    """
    Input (x)   : a 5-letter word from wordle.csv
    Output (y)  : a sequence of up to 6 guesses, with the last guess being correct
    Reward (r)  : 1 if solved within 6 guesses, partial score based on letters correct otherwise
    Input Example: 
        table
    Output Example: 
        crane
        pilot
        table
    """
    def __init__(self, file='wordle.csv'):
        """
        file: a csv file with a list of 5-letter words
        """
        super().__init__()
        current_dir = os.path.dirname(os.path.abspath(__file__))  # Get directory of this .py file
        path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'tot','data', 'wordle', file)
        self.data = [word.strip() for word in open(path).readlines()]
        self.value_cache = {}
        self.steps = 6 
        self.stops = ['\n'] * 6

        self.valid_words = set(self.data)

    def __len__(self) -> int:
        return len(self.data)
    
    def get_input(self, idx: int) -> str:
        return self.data[idx]

    def test_output(self, idx: int, output: str):
        target = self.data[idx]
        lines = output.strip().split('\n')
        guesses = [line.strip() for line in lines if line.strip()]
        
        if guesses and guesses[-1].lower() == target.lower():
            score = max(0.1, 1.0 - (len(guesses) - 1) * 0.15)
            return {'r': score, 'solved': True, 'guesses': len(guesses)}
        
        if guesses:
            last_guess = guesses[-1].lower()
            if len(last_guess) == 5:
                correct_positions = sum(1 for i in range(5) if i < len(last_guess) and i < len(target) and last_guess[i] == target[i])
                correct_letters = sum(1 for letter in set(last_guess) if letter in target)
                partial_score = (correct_positions * 0.1 + correct_letters * 0.02)
                return {'r': partial_score, 'solved': False, 'correct_positions': correct_positions, 'correct_letters': correct_letters}
        
        return {'r': 0, 'solved': False}
            
    def standard_prompt_wrap(self, x: str, y: str='') -> str:
        """Wrap the input and current guesses into a standard prompt"""
        guesses = y.strip().split('\n') if y else []
        formatted_guesses, formatted_feedback = format_guesses_and_feedback(guesses, x)
        return standard_prompt.format(input="[hidden]", guesses=formatted_guesses)

    def cot_prompt_wrap(self, x: str, y: str='') -> str:
        """Wrap the input and current guesses into a chain-of-thought prompt"""
        guesses = y.strip().split('\n') if y else []
        formatted_guesses, formatted_feedback = format_guesses_and_feedback(guesses, x)
        return cot_prompt.format(input="[hidden]", guesses=formatted_guesses, feedback=formatted_feedback)
    
    def propose_prompt_wrap(self, x: str, y: str='') -> str:
        """Wrap the input and current guesses into a proposal prompt"""
        guesses = y.strip().split('\n') if y else []
        formatted_guesses, formatted_feedback = format_guesses_and_feedback(guesses, x)
        return propose_prompt.format(guesses=formatted_guesses, feedback=formatted_feedback)
    
    def value_prompt_wrap(self, x: str, y: str) -> str:
        """Wrap a proposed guess for evaluation"""
        lines = y.strip().split('\n')
        current_guesses = lines[:-1] if lines else []
        next_guess = lines[-1] if lines else ""
        
        formatted_guesses, formatted_feedback = format_guesses_and_feedback(current_guesses, x)
        
        return value_prompt.format(
            guesses=formatted_guesses,
            feedback=formatted_feedback,
            next_guess=next_guess
        )
    
    def value_outputs_unwrap(self, x: str, y: str, value_outputs: list) -> float:
        """Convert the value outputs into a numerical score"""
        value_ratings = [output.strip().split('\n')[-1] for output in value_outputs]
        value_map = {'Poor': 0.2, 'Good': 1.0, 'Excellent': 5.0}
        
        counts = {'Poor': 0, 'Good': 0, 'Excellent': 0}
        for rating in value_ratings:
            for key in value_map:
                if key in rating:
                    counts[key] += 1
                    break
        
        value = sum(value_map[key] * count for key, count in counts.items())
        
        lines = y.strip().split('\n')
        if lines:
            guess = lines[-1].strip().lower()
            
            if not (len(guess) == 5 and guess in self.valid_words):
                value *= 0.1

            if guess in lines[:-1]:
                value *= 0.2
            
            if guess == x.lower():
                value += 10.0
        
        return max(0.01, value)  
    
    def vote_prompt_wrap(self, x: str, candidates: list) -> str:
        """Create a prompt for voting between multiple candidates"""
        if not candidates:
            return "No candidates to evaluate."
        
        common_guesses = []
        for line in candidates[0].strip().split('\n')[:-1]: 
            if line.strip():
                common_guesses.append(line.strip())
        
        new_guesses = []
        for candidate in candidates:
            lines = candidate.strip().split('\n')
            if lines:
                new_guesses.append(lines[-1].strip())
        
        formatted_guesses, formatted_feedback = format_guesses_and_feedback(common_guesses, x)
        candidates_str = "\n".join([f"{i+1}. {guess}" for i, guess in enumerate(new_guesses)])
        
        return vote_prompt.format(
            guesses=formatted_guesses,
            feedback=formatted_feedback,
            candidates=candidates_str,
            n_candidates=len(candidates)
        )
    
    def vote_outputs_unwrap(self, vote_outputs: list, n_candidates: int) -> list:
        """Extract votes from the outputs and convert to values"""
        values = [0] * n_candidates
        
        for output in vote_outputs:
            lines = output.strip().split('\n')
            for line in lines:
                for i in range(n_candidates):
                    rank_patterns = [
                        f"{i+1}\.", f"Rank {i+1}:", f"{i+1} -", f"#{i+1}",
                        f"({i+1})", f"{i+1}st", f"{i+1}nd", f"{i+1}rd", f"{i+1}th"
                    ]
                    if any(pattern in line for pattern in rank_patterns):
                        values[i] += (n_candidates - i)
                        break
        
        return values
