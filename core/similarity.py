import re
import math
from collections import Counter

# A small subset of common english stop words to ignore during similarity comparison
STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
    "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't",
    'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't",
    # Specific to our platform to prevent them from overly weighting results
    'book', 'books', 'lore', 'archives', 'history', 'culture', 'read', 'post', 'author'
}

def _tokenize(text):
    """Convert text to lowercase words, removing punctuation."""
    if not text:
        return []
    # Find all alphanumeric sequences
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out stopwords and ultra-short words
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]

def _get_tf(tokens):
    """Compute Term Frequency (TF) for a document."""
    tf_dict = Counter(tokens)
    total_words = len(tokens)
    if total_words > 0:
        for word in tf_dict:
            # simple normalized TF
            tf_dict[word] = tf_dict[word] / float(total_words)
    return tf_dict

def get_similar_items(target_text, queryset, limit=3, text_field='title'):
    """
    Lightweight, pure-Python TF-IDF similarity calculation. 
    Ideal for servers with 1GB RAM by avoiding bulky NLP libraries.
    
    :param target_text: The source text (e.g., Archive title + description)
    :param queryset: Django QuerySet of objects to compare against (e.g., Books, Lore)
    :param limit: Number of top matches to return
    :param text_field: The attribute name on the objects to compare (or a callable taking the object)
    """
    if not target_text or not queryset:
        return []

    target_tokens = _tokenize(target_text)
    if not target_tokens:
        # If target text is mostly stop words, fallback to no recommendations rather than random
        return []

    target_tf = _get_tf(target_tokens)
    
    # Pre-fetch elements from DB (assuming the queryset is small enough, e.g. < 5000 rows. 
    # For a 1GB RAM server, scanning a few thousand strings in memory takes milliseconds)
    items = list(queryset)
    if not items:
        return []

    # Calculate TF for all items
    item_tfs = []
    # Calculate Document Frequency (DF) across the corpus (the items being compared)
    df_dict = Counter()
    
    for item in items:
        # Extract text based on string attribute or callable (e.g., lambda obj: obj.title + " " + obj.description)
        if callable(text_field):
            text = text_field(item)
        else:
            text = getattr(item, text_field, '')
            
        tokens = _tokenize(text)
        tf = _get_tf(tokens)
        
        # Increase DF for each unique word found in this document
        for word in tf.keys():
            df_dict[word] += 1
            
        item_tfs.append((item, tf))

    N = len(items) + 1 # +1 for the target document itself
    
    # Update DF with words from our target document
    for word in target_tf.keys():
        df_dict[word] += 1
        
    # Calculate IDF for all seen words
    idf_dict = {}
    for word, df in df_dict.items():
        # +1 smoothing to avoid division by zero
        idf_dict[word] = math.log10(N / float(df + 1))

    # Helper function to compute Cosine Similarity between two TF-IDF vectors
    def compute_cosine_similarity(tf1, tf2, idf):
        # We only need to iterate over the intersection of words to find dot product
        common_words = set(tf1.keys()).intersection(set(tf2.keys()))
        
        dot_product = 0.0
        for word in common_words:
            weight1 = tf1[word] * idf[word]
            weight2 = tf2[word] * idf[word]
            dot_product += (weight1 * weight2)
            
        if dot_product == 0:
            return 0.0
            
        # Compute magnitudes
        mag1 = sum((tf1[w] * idf[w])**2 for w in tf1.keys())
        mag2 = sum((tf2[w] * idf[w])**2 for w in tf2.keys())
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
            
        return dot_product / (math.sqrt(mag1) * math.sqrt(mag2))

    # Calculate scores
    scored_items = []
    for item, tf in item_tfs:
        score = compute_cosine_similarity(target_tf, tf, idf_dict)
        if score > 0.01: # Threshold to filter out pure noise
            scored_items.append((score, item))

    # Sort descending by score
    scored_items.sort(key=lambda x: x[0], reverse=True)
    
    # Return top N items
    return [item for score, item in scored_items[:limit]]
