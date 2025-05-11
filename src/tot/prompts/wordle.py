# Wordle prompt templates
standard_prompt = """You're playing Wordle. Your goal is to guess a 5-letter word in one shot.

Target word: {input}

Provide your guess (a valid 5-letter word):
"""

cot_prompt = """You're playing Wordle. Your goal is to guess a 5-letter word within 6 tries.
After each guess, you'll be shown:
🟩 = correct letter in correct position
🟨 = correct letter in wrong position
⬛ = letter not in the word

Target word: {input}
Your guesses:
{guesses}
Our feedback:
{feedback}

Let's think step by step to figure out the best guess.
First, let's analyze what we know from previous guesses.
Then, let's identify potential candidates that match our constraints.
Finally, let's choose the best guess that will narrow down possibilities.

Reasoning:
"""

propose_prompt = """Based on the Wordle guesses so far:
{guesses}

And the feedback:
{feedback}

Let's brainstorm possible 5-letter words that could match. Suggest 5 different words as possible guesses, ranking them from most likely to least likely. For each one, explain briefly why it's a good guess. 

If there is no feedback or guesses so far, you must choose random 5-letter words to get started. Do not under any situation respond with anything outside of the following format.

Format:
1. [WORD] - explanation
2. [WORD] - explanation
3. [WORD] - explanation
4. [WORD] - explanation
5. [WORD] - explanation
"""

value_prompt = """In Wordle, we need to evaluate how good a guess is.

Current state:
Guesses so far: 
{guesses}

Feedback so far:
{feedback}

Next guess: {next_guess}

How good is this guess? Consider:
1. Does it use information from previous guesses effectively?
2. Does it test new letters that haven't been tested?
3. Is it a common English word?
4. Will it help narrow down possibilities significantly?

Rate this guess as either:
- "Excellent" - Uses all available information and tests new possibilities optimally
- "Good" - Reasonable guess that uses most available information
- "Poor" - Ignores some known information or is an unlikely word

Rating:
"""
