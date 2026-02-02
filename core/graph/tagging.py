"""NLP-based tagging system using spaCy and Scryfall keywords."""
import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc
from typing import List, Dict, Set, Tuple, Optional
import re

from core.services.scryfall_keywords import ScryfallKeywords

class KeywordTagger:
    """
    Tagging system that uses NLP to identify and categorize keywords and actions.
    """
    
    # Categorization of keywords
    KEYWORD_CATEGORIES = {
        # Abilities
        "evasion": {"flying", "menace", "trample", "intimidate", "fear", "skulk", 
                   "horsemanship", "shadow", "plainswalk", "islandwalk", 
                   "swampwalk", "mountainwalk", "forestwalk", "landwalk", "unblockable"},
        "combat": {"first strike", "double strike", "deathtouch", "vigilance", "reach", 
                  "trample", "rampage", "flanking", "bushido", "battle cry", "melee", 
                  "mentor", "training"},
        "protection": {"hexproof", "shroud", "indestructible", "protection", "ward", 
                      "defender", "absorb", "regenerate"},
        "speed": {"haste", "flash", "split second"},
        "recursion": {"persist", "undying", "unearth", "embalm", "eternalize", "encore", 
                     "escape", "retrace", "jump-start", "flashback", "aftermath", "recover",
                     "dredge", "scavenge"},
        "economy": {"convoke", "delve", "affinity", "improvise", "assist", "bargain",
                   "offering", "treasure", "gold"},
        "advantage": {"investigate", "clue", "cycling", "monarch", "initiative", 
                     "cascade", "discover", "explore", "scry", "surveil", "fateseal"},
        "removal": {"destroy", "exile", "fight", "bite", "sacrifice", "annihilator"},
        "tokens": {"populate", "proliferate", "amass", "incubate", "fabricate", 
                  "living weapon", "afterlife", "create"},
        "counters": {"proliferate", "support", "bolster", "adapt", "outlast", 
                    "evolve", "graft", "modular", "scavenge", "devour", "riot", "mentor"},
        "graveyard": {"mill", "surveil", "dredge", "delve", "escape", "flashback", 
                     "unearth", "threshold", "delirium"}
    }

    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize NLP model and keyword matchers."""
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            # If model not found, download it (handling this in code might be risky, 
            # ideally it's pre-installed, but we can try/catch)
            from spacy.cli import download
            download(model_name)
            self.nlp = spacy.load(model_name)
            
        self.keywords_service = ScryfallKeywords()
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        self._initialize_patterns()
        
    def _initialize_patterns(self):
        """Load keywords from service and register with matcher."""
        abilities, actions = self.keywords_service.get_all_keywords()
        
        # Add abilities to matcher
        ability_patterns = [self.nlp.make_doc(k) for k in abilities]
        self.matcher.add("KEYWORD_ABILITY", ability_patterns)
        
        # Add actions to matcher
        action_patterns = [self.nlp.make_doc(k) for k in actions]
        self.matcher.add("KEYWORD_ACTION", action_patterns)
        
    def extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """
        Extract keywords from text.
        
        Returns:
            Dictionary with 'abilities' and 'actions' lists.
        """
        if not text:
            return {"abilities": [], "actions": []}
            
        doc = self.nlp(text)
        matches = self.matcher(doc)
        
        found_abilities = set()
        found_actions = set()
        
        for match_id, start, end in matches:
            string_id = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            keyword = span.text
            
            if string_id == "KEYWORD_ABILITY":
                # Filter out partial matches if necessary (e.g. 'Flash' in 'Flashback')
                # But PhraseMatcher is usually greedy enough or strict enough
                found_abilities.add(keyword)
            elif string_id == "KEYWORD_ACTION":
                found_actions.add(keyword)
                
        return {
            "abilities": list(found_abilities),
            "actions": list(found_actions)
        }
    
    def get_category(self, keyword: str) -> Optional[str]:
        """Get the primary category for a keyword."""
        keyword_lower = keyword.lower()
        
        for category, keywords in self.KEYWORD_CATEGORIES.items():
            if keyword_lower in keywords:
                return category
                
        return "other"
        
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        Useful for detecting non-keyword synergy logic.
        """
        if not text1 or not text2:
            return 0.0
            
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)
        
        return doc1.similarity(doc2)
        
    def extract_action_context(self, text: str, action: str) -> List[str]:
        """
        Extract the context/parameters of an action.
        Example: "Scry 2" -> "2"
        Example: "Destroy target creature" -> "target creature"
        """
        if not text or not action:
            return []
            
        doc = self.nlp(text)
        action_lower = action.lower()
        contexts = []
        
        # This is a simplified extraction. 
        # A full dependency parse would be more robust but complex.
        for sent in doc.sents:
            if action_lower in sent.text.lower():
                # Find the action token
                for token in sent:
                    if token.text.lower() == action_lower:
                        # Get children/subtree as context
                        children = [child.text for child in token.children]
                        if children:
                            contexts.append(" ".join(children))
                            
        return contexts
