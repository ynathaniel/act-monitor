from threading import Thread, RLock
from time import sleep


class DBWorker(Thread):
    """
    NAME
        DBWorker - a thread class that performs 1 DBTask at a time
    VARIABLES
        worker_name         -> Thread name - used for printing/logging purposes
        daemon              -> indicated if this thread is shut down when the main thread shuts down (default is False)
        current_task        -> DBTask instance currently assigned for this worker to execute
        current_task_lock   -> RLock instance to make sure all actions on current_task are thread safe
        exit_event          -> Event instance to tell the worker it's time to shut down safely
        utils               -> DBUtils instance containing variables and objects needed through the system
        actioner            -> DBAction instance that actually performs all database actions
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    daemon = False
    current_task_lock = RLock()
    current_task = None

    """
    NAME
        __init__ - constructor to set the variables for the instance
    SYNOPSIS
        __init__(self, worker_name, exit_event, utils, actioner)
            self            -> the instance of the class
            worker_name     -> Thread name
            exit_event      -> Event that indicates when it's time to shut off the thread safely
            utils           -> DBUtils to be used for reaching 'global' tools
            actioner        -> DBAction to execute database actions
    DESCRIPTION
        The constructor sets up the class variables
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __init__(self, worker_name, exit_event, utils, actioner):
        Thread.__init__(self, name=worker_name)
        self.exit_event = exit_event
        self.utils = utils
        self.actioner = actioner

    """
    NAME
        run - waits for and performs DBTask instances
    SYNOPSIS
        run(self)
            self -> the instance of the class
    DESCRIPTION
        default function called after thread is started

        While exit_event is not set:
            if a task is assigned:
                1. perform the task using actioner
                    if any exceptions occur, print exception and move on
                2. make the worker available - remove task
            else:
                sleep 150 milliseconds and restart loop

        Once exit_event is set:
            stop thread
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def run(self):
        while True:
            if self.exit_event.isSet():
                self.utils.printer.push("{0} is exiting now.".format(self.getName()))
                break

            if self.__is_available__():
                sleep(0.15)
            else:
                # self.utils.printer.push("{0} just got busy".format(self.getName()))
                try:
                    self.actioner.create_new_action(self.current_task)
                except Exception as e:
                    print e
                self.__make_available__()

    """
    NAME
        add_task - enables an external object to assign the current task
    SYNOPSIS
        add_task(self, db_task_to_do)
            self            -> the instance of the class
            db_task_to_do   -> DBTask instance to assign to the worker
    DESCRIPTION
        This function should be called by DBPool to assign a pending task to a worker

        Only assigns a task if the worker is available
    RETURNS
        If task was assigned successfully, returns True
        else, returns False
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def add_task(self, db_task_to_do):
        if self.__is_available__():
            self.current_task = db_task_to_do
            return True
        else:
            return False

    """
    NAME
        __is_available__ - thread-safe function to check if the worker is working on some task
    SYNOPSIS
        __is_available__(self)
            self    -> the instance of the class
    DESCRIPTION
        This function is thread safe

        Checks if a current_task exists (there is a task already assigned to this worker)
    RETURNS
        If current_task is None, returns True
        else, returns False
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __is_available__(self):
        with self.current_task_lock:
            if self.current_task is None:
                return True
            else:
                return False

    """
    NAME
        __make_available__ - thread-safe function to make the worker available for a future task
    SYNOPSIS
        __make_available__(self)
            self    -> the instance of the class
    DESCRIPTION
        This function is thread safe

        Sets current_task to None to indicate this thread is not working on any tasks
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __make_available__(self):
        with self.current_task_lock:
            self.current_task = None