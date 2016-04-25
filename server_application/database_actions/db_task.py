from threading import RLock
import json

class DBTask:
    """
    NAME
        DBTask - a single SQL task to be performed - ex: SELECT name FROM users WHERE age=20
    VARIABLES
        action              -> type of DB action to perform
        object_name         -> name of dynamic object to handle
        additional_args     -> additional arguments needed to perform the action
            each action has different requirements
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    """

    """
    NAME
        __init__ - constructor to set the description of task
    SYNOPSIS
        __init__(self, action_type, object_name, **kwargs)
            self            -> the instance of the class
            action_type     -> type of action to execute
                supports "create", "drop", "select", "insert", "delete", "update", "update_count"
            object_name     -> name of object to deal with
            **kwargs        -> additional arguments - action type specific
    DESCRIPTION
        The class constructor sets up the details of the database action to execute
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    """
    def __init__(self, action_type, object_name, **kwargs):
        self.action = action_type
        self.object_name = str(object_name).title()
        self.additional_args = kwargs

    """
    NAME
        __repr__ - override of the function to print the instance of the object
    SYNOPSIS
        __init__(self)
            self    -> the instance of the class
    DESCRIPTION
        Override the function to print the instance of the object

        returns the dictionary of the instance as a string
    RETURNS
        str(self.__dict__)      -> the __dict__ of the instance converted to string
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    """
    def __repr__(self):
        return str(self.__dict__)


class DBTaskList:
    """
    NAME
        DBTask - a queue of DBTasks that allows synchronous FIFO performance
    VARIABLES
        tasks           -> list of DBTask instances
        list_lock       -> RLock instance used to make queue thread-safe
        can_pop         -> boolean indicating if popping tasks is allowed
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    tasks = []
    list_lock = RLock()
    can_pop = True

    """
    NAME
        push - enqueue a DBTask to the tasks queue
    SYNOPSIS
        push(self, task_to_push)
            self            -> the instance of the class
            task_to_push    -> DBTask to append to the tasks list
    DESCRIPTION
        Verifies task_to_push is an instance of DBTask, then enqueues task_to_push with list_lock
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def push(self, task_to_push):
        self.__verify_task_is_dbtask__(task_to_push)
        with self.list_lock:
            self.tasks.append(task_to_push)

    """
    NAME
        __verify_task_is_dbtask__ - verifies the task is an instance of DBTask
    SYNOPSIS
        __verify_task_is_dbtask__(self, task)
            self    -> the instance of the class
            task    -> object to verify
    DESCRIPTION
        Check if task is an instance of DBTask
        If not, raise error
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __verify_task_is_dbtask__(self, task):
        if not isinstance(task, DBTask):
            raise Exception("Attempt to add task that is not a DBTask. task:\n{0}".format(task))

    """
    NAME
        pop - attempts to dequeue a DBTask
    SYNOPSIS
        pop(self)
            self    -> the instance of the class
    DESCRIPTION
        This function is thread safe

        If
            there are more than 0 tasks left to execute
            AND
            popping tasks is still allowed
        then
                dequeue the first in the list
    RETURNS
        if size of queue > 0 AND can_pop:
            return oldest task on the queue
        else:
            None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def pop(self):
        with self.list_lock:
            if self.can_pop:
                task_to_pop = self.tasks.pop(0)
                return task_to_pop
            else:
                return None

    """
    NAME
        get_size - returns the size of the queue
    SYNOPSIS
        get_size(self)
            self    -> the instance of the class
    DESCRIPTION
        This function is thread safe

        returns the number of pending tasks
    RETURNS
        len(self.tasks)     -> size of task queue
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def get_size(self):
        with self.list_lock:
            num_of_tasks = len(self.tasks)
        return num_of_tasks

    """
    NAME
        no_more_popping - locks the queue so it cannot pop tasks anymore
    SYNOPSIS
        no_more_popping(self)
            self    -> the instance of the class
    DESCRIPTION
        This function is thread safe

        makes self.can_pop False - popping is no longer allowed
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def no_more_popping(self):
        with self.list_lock:
            self.can_pop = False

    """
    NAME
        to_json - get the tasks queue as a dictionary
    SYNOPSIS
        to_json(self)
            self    -> the instance of the class
    DESCRIPTION
        Creates a dictionary with a list of pending tasks
    RETURNS
        {
            "remaining_tasks": [ dict of task1, dict of task2 ]
        }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def to_json(self):
        data = []
        for t in self.tasks:
            data.append(t.__dict__)

        return {"remaining_tasks": data}


if __name__ == "__main__":
    task1 = DBTask("create", "yoav", holiday="christmas")
    task2 = DBTask("drop", "noam", holiday="yom kippur")
    task_list = DBTaskList()
    task_list.push(task1)
    task_list.push(task2)

    with open("file.json", "w") as f:
        f.write(json.dumps(task_list.to_JSON(), indent=4))