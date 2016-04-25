from threading import Thread, RLock
from time import sleep


class DBPrinter(Thread):
    """
    NAME
        DBPrinter - a thread class that makes sure print calls are performed synchronously
    VARIABLES
        print_queue     -> list of strings pedning print (in chronological order) (FIFO)
        locker          -> RLock object used to make sure print_queue does not get appended while print
                                or by two threads simultaneously
        daemon          -> thread variable (default is True) to make sure this thread shuts down with main thread
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    """
    print_queue = []
    locker = RLock()
    daemon = True

    """
    NAME
        run - prints all data from print_queue every 400 milliseconds
    SYNOPSIS
        run(self)
            self    -> the instance of the class
    DESCRIPTION
        default function called after thread is started

        Every 400 milliseconds it calls self.pop() - synchronously prints out everything in the queue
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    """
    def run(self):
        while True:
            sleep(0.4)
            self.pop()

    """
    NAME
        push - appends data to the print_queue
    SYNOPSIS
        push(self, data_to_print)
            self              -> the instance of the class
            data_to_print     -> can be a string or list of strings
                if string - append to queue
                if list of strings - extend queue
    DESCRIPTION
        The function that's called by external objects when they want to print something synchronously
        This function is synchronous - uses locker
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    """
    def push(self, data_to_print):
        with self.locker:
            if type(data_to_print) is list:
                for item in data_to_print:
                    self.print_queue.append(item)
            else:
                self.print_queue.append(data_to_print)

    """
    NAME
        pop - synchronously prints and empties the print_queue
    SYNOPSIS
        pop(self)
            self    -> the instance of the class
    DESCRIPTION
        The function that's called by self.run() to continually print everything out

        prints all items in print_queue using FIFO method

        This function is synchronous - uses locker
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    """
    def pop(self):
        with self.locker:
            for data in self.print_queue:
                print data

            self.print_queue = []