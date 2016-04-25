from threading import Thread, Event
from time import sleep
from datetime import datetime

from db_worker import DBWorker
from db_action import DBAction

NUMBER_OF_WORKERS = 3


class DBPool(Thread):
    """
    NAME
        DBPool - a thread class that assigns DBWorker instances with tasks from the DBTaskList
    VARIABLES
        workers         -> list of dictionaries containing DBWorker instances and time last task was assigned
        workers_stuck   -> list of stuck DBWorkers
        workers_event   -> Event instance that allows the worker to know it's time to exit
        exit_event      -> Event instance indicating when DBPool should exit
        utils           -> DBUtils instance with the general 'global' tools
        daemon          -> thread variable (default is False) indicating this thread does not shut down with main thread
        action          -> DBAction instance to perform all actions on the database
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """

    workers = []
    workers_stuck = []
    workers_event = Event()

    """
    NAME
        __init__ - constructor to set the variables for this instance
    SYNOPSIS
        __init__(self, exit_event, utils)
            self            -> the instance of the class
            exit_event      -> Event that indicates when it's time to shut off the thread safely
            utils           -> DBUtils to be used for reaching 'global' tools
    DESCRIPTION
        The constructor sets up the class variables
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __init__(self, exit_event, utils):
        Thread.__init__(self)

        self.daemon = False

        self.exit_event = exit_event
        self.utils = utils
        self.action = DBAction(utils)

    """
    NAME
        run - waits and dequeues DBTasks from DBTaskList later to assign to a DBWorker
    SYNOPSIS
        run(self)
            self -> the instance of the class
    DESCRIPTION
        default function called after thread is started

        sets up N DBWorker instances
            N = NUMBER_OF_WORKERS (global variable)


        While exit_event is not set:
            if tasks queue is empty:
                1. sleep 150 milliseconds
                2. verify no workers are stuck
            else:
                1. dequeue the first task in the list (FIFO algorithm)
                2. attempt to assign the task to a worker
                    if found an available worker:
                        1. assign task to worker
                        2. record the tme task was assigned
                    else:
                        1. sleep 50 milliseconds
                        2. verify no workers are stuck

        Once exit_event is set:
            1. set workers_event - tell DBWorkers to exit safely
            2. stop thread
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def run(self):
        self.__set_up_workers(NUMBER_OF_WORKERS)

        while True:
            if self.exit_event.isSet():
                self.utils.printer.push("DBPool is exiting now.")
                self.workers_event.set()
                break

            if self.utils.tasks.get_size() == 0:
                sleep(0.15)
                for worker in self.workers:
                    if not worker.get("thread").__is_available__():
                        self.__is_worker_stuck(worker)
            else:
                task_to_assign = self.utils.tasks.pop()

                if task_to_assign is None:
                    continue

                task_assigned = False
                while not task_assigned:
                    for worker in self.workers:
                        if worker.get("thread").add_task(task_to_assign):
                            task_assigned = True
                            worker["time_assigned"] = datetime.now()
                            break
                        else:
                            if not worker.get("thread").__is_available__():
                                self.__is_worker_stuck(worker)
                    if not task_assigned:
                        sleep(0.05)

    """
    NAME
        __set_up_workers - creates DBWorker instances for this class to manage
    SYNOPSIS
        __set_up_workers(self, num_of_workers)
            self            -> the instance of the class
            num_of_workers  -> the number of workers to create
    DESCRIPTION
        creates N additional workers for this class to manage
            N = num_of_workers
            * additional - does not overwrite or interfere with any existing workers

        for i in num_of_workers:
            1. set up DBWorker instance
            2. create dictionary with the following format:
                {
                    "thread": DBWorker Instance,
                    "time_assigned": None
                }
            3. add dictionary to self.workers (list of managed workers)
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __set_up_workers(self, num_of_workers):
        for i in range(num_of_workers):
            worker_name = "DBWorker{0}".format(len(self.workers))
            worker = DBWorker(worker_name, self.workers_event, self.utils, self.action)
            worker.start()

            self.workers.append({
                "thread": worker,
                "time_assigned": None
            })

    """
    NAME
        __is_worker_stuck - checks if a worker is stuck on some task
    SYNOPSIS
        __is_worker_stuck(self, stuck_worker)
            self            -> the instance of the class
            stuck_worker    -> a potentially stuck worker
    DESCRIPTION
        if stuck_worker has worked on the assigned task for over 3 seconds:
            1. add stuck_worker to the list of stuck_workers
            2. remove stuck_worker from the list of manage workers
            3. create a new worker (I'll refer to it as new_worker)
            4. assign the task from stuck_worker to new_worker
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __is_worker_stuck(self, stuck_worker):
        if (datetime.now() - stuck_worker.get("time_assigned")).total_seconds() > 3:
            self.workers_stuck.append(stuck_worker)
            self.workers.remove(stuck_worker)
            self.__set_up_workers(1)

            stuck_task = stuck_worker["thread"].current_task
            self.workers[-1]["thread"].add_task(stuck_task)
            self.workers[-1]["time_assigned"] = datetime.now()

            self.utils.printer.push("Removed Stuck Worker - {0}".format(stuck_worker["thread"].name))