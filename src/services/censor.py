'''
Name: censor.py
Description: Contains Censor class, which scans an input text for profanity, replacing it with a placeholder description if any is suspected.
Author: Joshua Welicky
Creation Date: 4/8/2026
Revision Date: 4/11/2026 -- Comments and removal of redundancies (Josh)
Preconditions: Interface requires a string input. Requires the better-profanity.profanity module.
Postconditions: Returns the inputted string if no potential profanity is found. Otherwise, a placeholder description string is returned.
Side effects: Checking algorithm can cause delays in the face of large inputs.
'''

from better_profanity import profanity

class Censor:
    #Must load in the default censor words package. 
    def __init__(self):
        profanity.load_censor_words()
    

    #Performs an extensive check on the input to search for any potential censorable words.
    #Essentially creates a sliding window along the input to search for any potential swear words.
    #Can cause false positives, but it almost always roots out swear words, which is for the best I think.
    #This algorithm can cause some delay based on the size of the input.
    def deep_check(self, text):
        for i in range(len(text)+1):
            for j in range(len(text)+1):
                subset = text[i:j]
                if profanity.contains_profanity(subset):
                    #print(f"{subset} is profane! Who knew!")
                    return False
        return True
    
    #This simply removes whitespace characters and converts to lower case.
    #Necessary to beat common evasion techniques.
    def normalize(self, text):
        whitespace = [' ', '\t']
        text = text.lower()
        normalized = ''
        for i in range(len(text)):
            if text[i] not in whitespace:
                normalized += text[i]
        return normalized

    #Main interface with other classes(LotController).
    #If ANY profanity is even suspected, a placeholder description is returned instead of the base text.
    def censor(self, text):
        if self.deep_check(self.normalize(text)):
            return text
        else:
            #A vaguer yet still accurate replacement description.
            return "There is a Special Restriction reported for this lot."
