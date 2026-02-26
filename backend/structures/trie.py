class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.response_category = None  # e.g., "crisis", "anxiety", "depression"

class Trie:
    """
    Trie (Prefix Tree) implementation for efficient keyword matching.
    Time Complexity: O(L) where L is the length of the word being searched.
    Space Complexity: O(N * L) where N is the number of words.
    """
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, category: str):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.response_category = category

    def search(self, text: str):
        """
        Scans a text to see if it contains any keywords from the Trie.
        Returns the category of the first match found, or None.
        """
        words = text.lower().split()
        for word in words:
            node = self.root
            for char in word:
                if char in node.children:
                    node = node.children[char]
                else:
                    node = None
                    break
            
            if node and node.is_end_of_word:
                return node.response_category
        return None
