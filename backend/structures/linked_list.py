class ListNode:
    def __init__(self, role: str, content: str):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.next = None
        self.prev = None

class DoublyLinkedList:
    """
    Doubly Linked List to store conversation history.
    Allows O(1) insertion at the end and easy traversal.
    """
    def __init__(self, max_size=10):
        self.head = None
        self.tail = None
        self.size = 0
        self.max_size = max_size

    def append(self, role: str, content: str):
        new_node = ListNode(role, content)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        
        self.size += 1
        if self.size > self.max_size:
            self.remove_head()

    def remove_head(self):
        if not self.head:
            return
        if self.head == self.tail:
            self.head = None
            self.tail = None
        else:
            self.head = self.head.next
            self.head.prev = None
        self.size -= 1

    def to_list(self):
        """Convert to list of dicts for API consumption"""
        history = []
        current = self.head
        while current:
            history.append({"role": current.role, "content": current.content})
            current = current.next
        return history
