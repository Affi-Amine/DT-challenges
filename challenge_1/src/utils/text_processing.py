import re
import string
from typing import List, Set, Dict, Any
from collections import Counter
import logging

try:
    import spacy
    from spacy.lang.en.stop_words import STOP_WORDS
except ImportError:
    spacy = None
    STOP_WORDS = set()

logger = logging.getLogger(__name__)

class TextProcessor:
    """Utility class for text processing and keyword extraction"""
    
    def __init__(self):
        self.nlp = None
        self.stop_words = self._get_stop_words()
        self.diplomatic_terms = self._load_diplomatic_terms()
        
        # Initialize spaCy if available
        self._init_spacy()
    
    def _init_spacy(self):
        """Initialize spaCy NLP model"""
        if spacy:
            try:
                # Try to load English model
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy English model loaded successfully")
            except OSError:
                try:
                    # Fallback to basic English model
                    self.nlp = spacy.load("en")
                    logger.info("spaCy basic English model loaded")
                except OSError:
                    logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                    self.nlp = None
        else:
            logger.warning("spaCy not installed. Some text processing features will be limited.")
    
    def _get_stop_words(self) -> Set[str]:
        """Get comprehensive stop words list"""
        # Basic English stop words
        basic_stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'could', 'should', 'may',
            'might', 'must', 'can', 'shall', 'this', 'these', 'those', 'they',
            'them', 'their', 'there', 'where', 'when', 'why', 'how', 'what',
            'who', 'which', 'whom', 'whose', 'i', 'you', 'we', 'us', 'our',
            'your', 'my', 'me', 'him', 'her', 'his', 'hers', 'ours', 'yours',
            'theirs', 'am', 'been', 'being', 'have', 'had', 'having', 'do',
            'does', 'did', 'doing', 'done', 'get', 'got', 'getting', 'go',
            'going', 'went', 'gone', 'come', 'came', 'coming', 'take', 'took',
            'taken', 'taking', 'make', 'made', 'making', 'see', 'saw', 'seen',
            'seeing', 'know', 'knew', 'known', 'knowing', 'think', 'thought',
            'thinking', 'say', 'said', 'saying', 'tell', 'told', 'telling',
            'ask', 'asked', 'asking', 'work', 'worked', 'working', 'call',
            'called', 'calling', 'try', 'tried', 'trying', 'need', 'needed',
            'needing', 'want', 'wanted', 'wanting', 'use', 'used', 'using',
            'find', 'found', 'finding', 'give', 'gave', 'given', 'giving',
            'put', 'putting', 'become', 'became', 'becoming', 'leave', 'left',
            'leaving', 'feel', 'felt', 'feeling', 'seem', 'seemed', 'seeming',
            'turn', 'turned', 'turning', 'start', 'started', 'starting',
            'show', 'showed', 'shown', 'showing', 'hear', 'heard', 'hearing',
            'play', 'played', 'playing', 'run', 'ran', 'running', 'move',
            'moved', 'moving', 'live', 'lived', 'living', 'believe', 'believed',
            'believing', 'hold', 'held', 'holding', 'bring', 'brought',
            'bringing', 'happen', 'happened', 'happening', 'write', 'wrote',
            'written', 'writing', 'sit', 'sat', 'sitting', 'stand', 'stood',
            'standing', 'lose', 'lost', 'losing', 'pay', 'paid', 'paying',
            'meet', 'met', 'meeting', 'include', 'included', 'including',
            'continue', 'continued', 'continuing', 'set', 'setting', 'learn',
            'learned', 'learning', 'change', 'changed', 'changing', 'lead',
            'led', 'leading', 'understand', 'understood', 'understanding',
            'watch', 'watched', 'watching', 'follow', 'followed', 'following',
            'stop', 'stopped', 'stopping', 'create', 'created', 'creating',
            'speak', 'spoke', 'spoken', 'speaking', 'read', 'reading', 'allow',
            'allowed', 'allowing', 'add', 'added', 'adding', 'spend', 'spent',
            'spending', 'grow', 'grew', 'grown', 'growing', 'open', 'opened',
            'opening', 'walk', 'walked', 'walking', 'win', 'won', 'winning',
            'offer', 'offered', 'offering', 'remember', 'remembered',
            'remembering', 'love', 'loved', 'loving', 'consider', 'considered',
            'considering', 'appear', 'appeared', 'appearing', 'buy', 'bought',
            'buying', 'wait', 'waited', 'waiting', 'serve', 'served', 'serving',
            'die', 'died', 'dying', 'send', 'sent', 'sending', 'expect',
            'expected', 'expecting', 'build', 'built', 'building', 'stay',
            'stayed', 'staying', 'fall', 'fell', 'fallen', 'falling', 'cut',
            'cutting', 'reach', 'reached', 'reaching', 'kill', 'killed',
            'killing', 'remain', 'remained', 'remaining'
        }
        
        # Add spaCy stop words if available
        if STOP_WORDS:
            basic_stop_words.update(STOP_WORDS)
        
        return basic_stop_words
    
    def _load_diplomatic_terms(self) -> Set[str]:
        """Load diplomatic and international relations terms"""
        return {
            # Countries and regions
            'afghanistan', 'albania', 'algeria', 'andorra', 'angola', 'argentina',
            'armenia', 'australia', 'austria', 'azerbaijan', 'bahamas', 'bahrain',
            'bangladesh', 'barbados', 'belarus', 'belgium', 'belize', 'benin',
            'bhutan', 'bolivia', 'bosnia', 'herzegovina', 'botswana', 'brazil',
            'brunei', 'bulgaria', 'burkina', 'faso', 'burundi', 'cambodia',
            'cameroon', 'canada', 'cape', 'verde', 'central', 'african', 'republic',
            'chad', 'chile', 'china', 'colombia', 'comoros', 'congo', 'costa',
            'rica', 'croatia', 'cuba', 'cyprus', 'czech', 'republic', 'denmark',
            'djibouti', 'dominica', 'dominican', 'republic', 'ecuador', 'egypt',
            'el', 'salvador', 'equatorial', 'guinea', 'eritrea', 'estonia',
            'eswatini', 'ethiopia', 'fiji', 'finland', 'france', 'gabon',
            'gambia', 'georgia', 'germany', 'ghana', 'greece', 'grenada',
            'guatemala', 'guinea', 'guyana', 'haiti', 'honduras', 'hungary',
            'iceland', 'india', 'indonesia', 'iran', 'iraq', 'ireland', 'israel',
            'italy', 'ivory', 'coast', 'jamaica', 'japan', 'jordan', 'kazakhstan',
            'kenya', 'kiribati', 'kuwait', 'kyrgyzstan', 'laos', 'latvia',
            'lebanon', 'lesotho', 'liberia', 'libya', 'liechtenstein', 'lithuania',
            'luxembourg', 'madagascar', 'malawi', 'malaysia', 'maldives', 'mali',
            'malta', 'marshall', 'islands', 'mauritania', 'mauritius', 'mexico',
            'micronesia', 'moldova', 'monaco', 'mongolia', 'montenegro', 'morocco',
            'mozambique', 'myanmar', 'namibia', 'nauru', 'nepal', 'netherlands',
            'new', 'zealand', 'nicaragua', 'niger', 'nigeria', 'north', 'korea',
            'north', 'macedonia', 'norway', 'oman', 'pakistan', 'palau', 'panama',
            'papua', 'new', 'guinea', 'paraguay', 'peru', 'philippines', 'poland',
            'portugal', 'qatar', 'romania', 'russia', 'rwanda', 'saint', 'kitts',
            'nevis', 'saint', 'lucia', 'saint', 'vincent', 'grenadines', 'samoa',
            'san', 'marino', 'sao', 'tome', 'principe', 'saudi', 'arabia',
            'senegal', 'serbia', 'seychelles', 'sierra', 'leone', 'singapore',
            'slovakia', 'slovenia', 'solomon', 'islands', 'somalia', 'south',
            'africa', 'south', 'korea', 'south', 'sudan', 'spain', 'sri', 'lanka',
            'sudan', 'suriname', 'sweden', 'switzerland', 'syria', 'taiwan',
            'tajikistan', 'tanzania', 'thailand', 'timor', 'leste', 'togo',
            'tonga', 'trinidad', 'tobago', 'tunisia', 'turkey', 'turkmenistan',
            'tuvalu', 'uganda', 'ukraine', 'united', 'arab', 'emirates',
            'united', 'kingdom', 'united', 'states', 'uruguay', 'uzbekistan',
            'vanuatu', 'vatican', 'city', 'venezuela', 'vietnam', 'yemen',
            'zambia', 'zimbabwe',
            
            # International organizations
            'united', 'nations', 'security', 'council', 'general', 'assembly',
            'economic', 'social', 'council', 'trusteeship', 'council',
            'international', 'court', 'justice', 'secretariat', 'unesco',
            'unicef', 'who', 'world', 'health', 'organization', 'world', 'bank',
            'international', 'monetary', 'fund', 'imf', 'world', 'trade',
            'organization', 'wto', 'nato', 'north', 'atlantic', 'treaty',
            'organization', 'european', 'union', 'african', 'union', 'asean',
            'association', 'southeast', 'asian', 'nations', 'organization',
            'american', 'states', 'oas', 'arab', 'league', 'commonwealth',
            'nations', 'g7', 'g8', 'g20', 'brics', 'opec', 'organization',
            'petroleum', 'exporting', 'countries',
            
            # Diplomatic terms
            'ambassador', 'embassy', 'consulate', 'diplomat', 'diplomatic',
            'immunity', 'treaty', 'agreement', 'convention', 'protocol',
            'memorandum', 'understanding', 'bilateral', 'multilateral',
            'negotiation', 'mediation', 'arbitration', 'sanctions', 'embargo',
            'resolution', 'declaration', 'communique', 'summit', 'conference',
            'dialogue', 'cooperation', 'partnership', 'alliance', 'coalition',
            'peacekeeping', 'peacebuilding', 'humanitarian', 'intervention',
            'sovereignty', 'territorial', 'integrity', 'self', 'determination',
            'human', 'rights', 'democracy', 'governance', 'rule', 'law',
            'international', 'law', 'customary', 'law', 'jus', 'cogens',
            'vienna', 'convention', 'diplomatic', 'relations', 'consular',
            'relations', 'state', 'responsibility', 'recognition', 'succession',
            'extradition', 'asylum', 'refugee', 'migration', 'border',
            'maritime', 'boundary', 'exclusive', 'economic', 'zone',
            'continental', 'shelf', 'territorial', 'waters', 'high', 'seas',
            'climate', 'change', 'environment', 'sustainable', 'development',
            'millennium', 'development', 'goals', 'sustainable', 'development',
            'goals', 'agenda', '2030', 'paris', 'agreement', 'kyoto', 'protocol',
            'nuclear', 'non', 'proliferation', 'disarmament', 'arms', 'control',
            'weapons', 'mass', 'destruction', 'chemical', 'weapons', 'biological',
            'weapons', 'landmines', 'cluster', 'munitions', 'small', 'arms',
            'light', 'weapons', 'terrorism', 'counter', 'terrorism', 'organized',
            'crime', 'trafficking', 'corruption', 'money', 'laundering',
            'cybersecurity', 'cyber', 'warfare', 'space', 'law', 'maritime',
            'law', 'aviation', 'law', 'trade', 'law', 'investment', 'law',
            'intellectual', 'property', 'dispute', 'settlement', 'world',
            'court', 'international', 'criminal', 'court', 'icc', 'international',
            'tribunal', 'law', 'sea', 'itlos'
        }
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract important keywords from text"""
        if not text:
            return []
        
        # Use spaCy if available for better keyword extraction
        if self.nlp:
            return self._extract_keywords_spacy(text, max_keywords)
        else:
            return self._extract_keywords_basic(text, max_keywords)
    
    def _extract_keywords_spacy(self, text: str, max_keywords: int) -> List[str]:
        """Extract keywords using spaCy NLP"""
        try:
            doc = self.nlp(text)
            keywords = set()
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT', 'LAW', 'PRODUCT']:
                    clean_entity = self._clean_keyword(ent.text)
                    if clean_entity and len(clean_entity) > 2:
                        keywords.add(clean_entity.lower())
            
            # Extract important nouns and adjectives
            for token in doc:
                if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                    not token.is_stop and 
                    not token.is_punct and 
                    len(token.text) > 2):
                    
                    clean_token = self._clean_keyword(token.lemma_)
                    if clean_token and clean_token.lower() not in self.stop_words:
                        keywords.add(clean_token.lower())
            
            # Add diplomatic terms found in text
            text_lower = text.lower()
            for term in self.diplomatic_terms:
                if term in text_lower:
                    keywords.add(term)
            
            # Convert to list and sort by importance (length as proxy)
            keyword_list = list(keywords)
            keyword_list.sort(key=len, reverse=True)
            
            return keyword_list[:max_keywords]
            
        except Exception as e:
            logger.warning(f"spaCy keyword extraction failed: {str(e)}. Falling back to basic method.")
            return self._extract_keywords_basic(text, max_keywords)
    
    def _extract_keywords_basic(self, text: str, max_keywords: int) -> List[str]:
        """Basic keyword extraction without NLP libraries"""
        # Clean and tokenize text
        text = self._clean_text_basic(text)
        words = text.lower().split()
        
        # Filter words
        filtered_words = []
        for word in words:
            clean_word = self._clean_keyword(word)
            if (clean_word and 
                len(clean_word) > 2 and 
                clean_word not in self.stop_words and
                not clean_word.isdigit()):
                filtered_words.append(clean_word)
        
        # Count word frequency
        word_counts = Counter(filtered_words)
        
        # Add diplomatic terms found in text
        text_lower = text.lower()
        for term in self.diplomatic_terms:
            if term in text_lower:
                word_counts[term] = word_counts.get(term, 0) + 5  # Boost diplomatic terms
        
        # Get most common words
        most_common = word_counts.most_common(max_keywords)
        return [word for word, count in most_common]
    
    def _clean_text_basic(self, text: str) -> str:
        """Basic text cleaning"""
        # Remove special characters but keep spaces and basic punctuation
        text = re.sub(r'[^\w\s.-]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _clean_keyword(self, keyword: str) -> str:
        """Clean individual keyword"""
        if not keyword:
            return ""
        
        # Remove punctuation and extra whitespace
        keyword = keyword.strip(string.punctuation + string.whitespace)
        # Remove numbers and special characters
        keyword = re.sub(r'[^\w\s-]', '', keyword)
        # Normalize whitespace
        keyword = re.sub(r'\s+', ' ', keyword)
        
        return keyword.strip()
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],  # Geopolitical entities (countries, cities, states)
            'EVENT': [],
            'LAW': [],
            'DATE': [],
            'MONEY': []
        }
        
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in entities:
                        clean_entity = self._clean_keyword(ent.text)
                        if clean_entity and clean_entity not in entities[ent.label_]:
                            entities[ent.label_].append(clean_entity)
            except Exception as e:
                logger.warning(f"Entity extraction failed: {str(e)}")
        
        return entities
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """Get basic text statistics"""
        if not text:
            return {}
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'avg_words_per_sentence': len(words) / max(len(sentences), 1),
            'avg_chars_per_word': len(text) / max(len(words), 1)
        }
    
    def is_diplomatic_content(self, text: str) -> bool:
        """Check if text contains diplomatic/international relations content"""
        text_lower = text.lower()
        diplomatic_indicators = 0
        
        # Count diplomatic terms
        for term in self.diplomatic_terms:
            if term in text_lower:
                diplomatic_indicators += 1
        
        # Check for diplomatic patterns
        diplomatic_patterns = [
            r'\b(ambassador|embassy|consulate)\b',
            r'\b(treaty|agreement|convention|protocol)\b',
            r'\b(united nations|security council|general assembly)\b',
            r'\b(bilateral|multilateral|diplomatic)\b',
            r'\b(resolution|declaration|summit|conference)\b'
        ]
        
        for pattern in diplomatic_patterns:
            if re.search(pattern, text_lower):
                diplomatic_indicators += 2
        
        # Return True if we found enough diplomatic indicators
        return diplomatic_indicators >= 3