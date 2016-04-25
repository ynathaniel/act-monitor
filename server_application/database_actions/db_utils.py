import os
import json

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, scoped_session

from db_task import DBTaskList, DBTask
from db_printer import DBPrinter

REM_TASKS_PATH = "/Users/yoavnathaniel/PycharmProjects/ActivityTrackr/remaining_tasks.json"


class DBUtils:
    """
    NAME
        DBUtils - class for general utilities needed across the entire system - every organization needs a handyman
    VARIABLES
        engine          -> database engine that allows execution/connection to database (sqlalchemy)
        metadata        -> provides the metadata of the database (tables, columns) (sqlalchemy)
        insp            -> overall inspector of the database (similar to metadata) (sqlalchemy)
        session_maker   -> instance of sessionmaker to set defaults for new database sessions (sqlalchemy)
        session_class   -> the class used to generate new scoped session instances (sqlalchmey)
            scoped sessions are required for threads
        tasks           -> DBTaskList instance - basically a queue of DBTask instances
        dynamic_objects -> dictionary containing all dynamic_objects in the system
        printer         -> DBPrinter instance - allows thread-safe printing
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """

    """
    NAME
        __init__ - constructor to set up the variables
    SYNOPSIS
        __init__(self, engine)
            self        -> the instance of the class
            engine      -> instance of Engine (sqlalchmey)
                a database connection that allows direct execution of queries
    DESCRIPTION
        The class constructor sets up the class variables and recovers any remaining tasks from the last time this ran
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __init__(self, engine):
        self.engine = engine
        self.metadata = MetaData(bind=engine)
        self.insp = inspect(engine)
        self.session_maker = sessionmaker(bind=engine)
        self.session_class = scoped_session(self.session_maker)
        self.tasks = DBTaskList()
        self.dynamic_objects = {}

        self.printer = DBPrinter()
        self.printer.daemon = True
        self.printer.start()

        self.__load_remaining_tasks()

    """
    NAME
        __load_remaining_tasks - loads and pushes pending tasks from a file
    SYNOPSIS
        __load_remaining_tasks(self)
            self    -> the instance of the class
    DESCRIPTION
        Allows the recovery of any uncompleted database tasks from the last time this program ran

        Loads uncompleted tasks from REM_TASKS_PATH
        For each uncompleted task, create a new DBTask instance and push it to the DBTaskList

        Removes the file REM_TASKS_PATH so next time this loads, it doesn't RELOAD the same tasks
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __load_remaining_tasks(self):
        if os.path.isfile(REM_TASKS_PATH):
            with open(REM_TASKS_PATH, "r") as f:
                rem_tasks = json.loads(f.read()).get('remaining_tasks', [])
                for rem_t in rem_tasks:
                    new_task = DBTask(rem_t.get("action"), rem_t.get("object_name"), **rem_t.get("additional_args"))
                    self.tasks.push(new_task)

            os.remove(REM_TASKS_PATH)

    """
    NAME
        record_remaining_tasks - saves pending tasks to a file
    SYNOPSIS
        record_remaining_tasks(self)
            self    -> the instance of the class
    DESCRIPTION
        Allows saving any uncompleted database tasks from the current process
            so they can be recovered and executed next time this loads

        This only goes into effect IF there are more than 0 uncompleted tasks

        Saves uncompleted tasks to REM_TASKS_PATH

        1. Lock the DBTaskList so it cannot be popped anymore
        2. convert the DBTaskList to a dictionary
        3. write the dictionary as a JSON in the file
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def record_remaining_tasks(self):
        if self.tasks.get_size() > 0:
            with open(REM_TASKS_PATH, "w") as f:
                self.tasks.no_more_popping()
                f.write(json.dumps(self.tasks.to_json(), indent=4))