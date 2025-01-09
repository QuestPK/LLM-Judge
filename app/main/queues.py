from pprint import pprint
from queue import Queue

class QueueManager:
    def __init__(self):
        self.queues = []
        self.current_queue = 0

    def display_all_items(self):
        for queue in self.queues:
            queue_data = list(queue.queue)

            print("Queue: \n")
            for item in queue_data:
                pprint(item)


    def get_total_queues(self) -> int:
        return len(self.queues)
    
    def get_n_items_from_queue(self, queue: Queue, n: int = 2):
            counter = 0
            items = []

            while(counter < n):
                if queue.empty():
                    break

                items.append(queue.get())
                counter += 1

            return items
    
    def get_items_to_process(self) -> list[dict]:
        if len(self.queues) == 0:
            return []
        
        elif len(self.queues) == 1:
            q = self.queues[0]
            return self.get_n_items_from_queue(q)
        
        elif len(self.queues) > 1:
            q = self.queues[self.current_queue]
            items = self.get_n_items_from_queue(q)
            self.current_queue = (self.current_queue + 1) % len(self.queues)
        
        self.delete_empty_queues()
        self.reset_counter()
        return items
    
    def insert(self, queue: Queue):
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
        if self.current_queue >= len(self.queues):
            self.current_queue = 0

    def delete_empty_queues(self):
        self.queues = [q for q in self.queues if not q.empty()]

    def delete_queue(self, queue_object: Queue):
        self.queues.remove(queue_object)


queue_manager = QueueManager()