from pprint import pprint
from queue import Queue
import threading

class QueueManager:
    def __init__(self):
        self.queues = []
        self.current_queue = 0
        self.lock = threading.Lock()

    def display_all_items(self):
        """Display all items in all queues."""
        # with self.lock:
        if self.queues:
            for queue in self.queues:
                queue_data = list(queue.queue)

                print("\nQueue Data: ")
                for item in queue_data:
                    print(item.keys())
        else:
            print("No queues available.")
            
    def get_total_queues(self) -> int:
        """Get the total number of queues."""
        # with self.lock:  # Locking for consistent read
        return len(self.queues)
    
    def get_n_items_from_queue(self, queue: Queue, n: int = 2):
            """Get n items from a queue."""
            print("\nGetting items from queue")

            items = []
            while(len(items) < n and not queue.empty()):
                items.append(queue.get())

            print("Items retrieved")
            print([list(item.keys()) for item in items])
            return items
    
    def get_items_to_process(self) -> list[dict]:
        """Get items to process from the queue manager."""
        # with self.lock:  # Locking the method to prevent race conditions

        print("\nCurrent Queue: ", self.current_queue)
        print("Number of Queues: ", len(self.queues))

        items = []
        if len(self.queues) == 0:
            return items
        
        elif len(self.queues) == 1:
            q = self.queues[0]
            items = self.get_n_items_from_queue(q)
        
        elif len(self.queues) > 1:
            q = self.queues[self.current_queue]
            items = self.get_n_items_from_queue(q)
            self.current_queue = (self.current_queue + 1) % len(self.queues)
        
        # self.delete_empty_queues()
        self.reset_counter()
        return items
    
    def insert(self, queue: Queue):
        """Insert a queue into the queue manager."""
        # with self.lock:  # Ensure atomic insert operation
        self.queues.append(queue)

    def create_and_insert_queries(self, items_list: list[dict]):
        queue = Queue()

        # item -> {"query_id" : {"question": "question string", "baseline": "baseline string", "current": "current string", "summary_accepted": true}}
        for item in items_list:
            query_id = list(item.keys())[0]
        
            for query_id, value in item.items():
                queue.put({query_id: value})
        self.insert(queue)
    
    def reset_counter(self):
        """Reset the current queue counter to 0 if it exceeds the number of queues."""
        # with self.lock:  # Ensures the counter reset is thread-safe
        if self.current_queue >= len(self.queues):
            self.current_queue = 0

    def delete_empty_queues(self):
        """Delete empty queues from the queue manager."""
        # with self.lock:  # Ensure thread-safe deletion of empty queues
        self.queues = [q for q in self.queues if not q.empty()]
        if self.current_queue >= len(self.queues):
            self.current_queue = 0 if self.queues else -1  # Adjust for empty list

    def delete_queue(self, queue_object: Queue):
        self.queues.remove(queue_object)


queue_manager = QueueManager()