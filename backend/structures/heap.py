class MaxHeap:
    def __init__(self):
        self.heap = []

    def parent(self, i):
        return (i - 1) // 2

    def left_child(self, i):
        return 2 * i + 1

    def right_child(self, i):
        return 2 * i + 2

    def insert(self, item):
        """
        Inserts an item into the heap.
        Item should be a dictionary or object with a 'rating' key/attribute.
        """
        self.heap.append(item)
        self._percolate_up(len(self.heap) - 1)

    def extract_max(self):
        """
        Removes and returns the item with the highest rating.
        """
        if not self.heap:
            return None
        
        root = self.heap[0]
        last_item = self.heap.pop()
        
        if self.heap:
            self.heap[0] = last_item
            self._percolate_down(0)
            
        return root

    def _percolate_up(self, i):
        while i > 0 and self.heap[self.parent(i)]['rating'] < self.heap[i]['rating']:
            self.heap[i], self.heap[self.parent(i)] = self.heap[self.parent(i)], self.heap[i]
            i = self.parent(i)

    def _percolate_down(self, i):
        max_index = i
        l = self.left_child(i)
        r = self.right_child(i)

        if l < len(self.heap) and self.heap[l]['rating'] > self.heap[max_index]['rating']:
            max_index = l

        if r < len(self.heap) and self.heap[r]['rating'] > self.heap[max_index]['rating']:
            max_index = r

        if i != max_index:
            self.heap[i], self.heap[max_index] = self.heap[max_index], self.heap[i]
            self._percolate_down(max_index)

    def build_heap(self, items):
        self.heap = items[:]
        for i in range(len(self.heap) // 2 - 1, -1, -1):
            self._percolate_down(i)

    def get_sorted_list(self):
        """
        Returns a sorted list of items (descending order) without modifying the heap.
        """
        # Create a copy to avoid destroying the heap
        temp_heap = MaxHeap()
        temp_heap.heap = self.heap[:]
        sorted_list = []
        while temp_heap.heap:
            sorted_list.append(temp_heap.extract_max())
        return sorted_list
