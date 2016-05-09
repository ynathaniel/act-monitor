from datetime import datetime
from threading import Event
from time import sleep

from sqlalchemy.engine import create_engine
from sqlalchemy.schema import CreateSchema

from ActMonitor.server_application.database_actions import CONN_URL, DB_SCHEMA, DEFAULT_OBJECT_NAMES, \
    USER_MANAGEMENT_OBJECT_NAME, USER_MANAGEMENT_PROPERTIES, DYNAMIC_API_OBJECT_NAME, DYNAMIC_API_PROPERTIES, \
    ALERT_RULES_OBJECT_NAME, ALERT_RULES_PROPERTIES, ALERT_FINDS_OBJECT_NAME, ALERT_FINDS_PROPERTIES
from db_pool import DBPool
from db_task import DBTask
from db_utils import DBUtils

CACHE_SIZE = 15


class DBManager:
    """
    NAME
        DBManager - manager that oversees all DB tasks and tools along with make sure the DB is set up and ready
    VARIABLES
        utils           -> DBUtils instance that carries most of the 'global' tools
        pool_event      -> Event instance to indicate when pool should exit safely
        pool            -> DBPool instance to create and manage DBWorker instances
        recent_cache    -> list of recent events - each event is of the following format:
            {
                "object_name": name of dynamic object,
                "timestamp": datetime the table row/event was created
            }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """

    utils = DBUtils(create_engine(CONN_URL, echo=False))
    pool_event = Event()
    pool = DBPool(pool_event, utils)
    pool.start()

    """
    NAME
        __init__ - constructor to verify the database is set up and ready
    SYNOPSIS
        __init__(self)
            self    -> the instance of the class
    DESCRIPTION
        The constructor verifies all required tables exist along with predefined data (such as master user)

        Makes sure recent_cache and object counts are set up and prepared for quick access
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __init__(self):
        self.__verify_schema_exists()
        self.__verify_dynamic_api_table_exists()
        self.__verify_users_table_exists()
        self.__verify_alert_tables_exists()
        self.recent_cache = self.__create_recent_cache()
        self.__verify_object_counts()

    """
    NAME
        __verify_schema_exists - verifies the predefined DB Schema exists
    SYNOPSIS
        __verify_schema_exists(self)
            self    -> the instance of the class
    DESCRIPTION
        If the predefined schema does not exist in the database, create the schema
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __verify_schema_exists(self):
        # verify the schema DB_SCHEMA exists in the postgres database
        # if it does not exist, create it and check again
        works = False
        while not works:
            all_schemas = self.utils.insp.get_schema_names()
            if DB_SCHEMA in all_schemas:
                self.utils.printer.push("'" + DB_SCHEMA + "' schema exists in postgres")
                works = True
            else:
                self.utils.printer.push("'" + DB_SCHEMA + "' schema does not exist in postgres")
                self.utils.printer.push("creating schema now..")
                self.__create_schema()
                sleep(2)

    """
    NAME
        __create_schema - creates the schema
    SYNOPSIS
        __create_schema(self)
            self    -> the instance of the class
    DESCRIPTION
        creates a new connection to create a new schema in the database
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __create_schema(self):
        # command to create a new schema in the postgres database
        with self.utils.engine as conn:
            conn.execute(CreateSchema(DB_SCHEMA))

    """
    NAME
        __verify_dynamic_api_table_exists - verifies the dynamic_api object exists as a dynamic object
    SYNOPSIS
        __verify_dynamic_api_table_exists(self)
            self    -> the instance of the class
    DESCRIPTION
        If the dynamic_api object does not exist in dynamic_objects, create the dynamic object
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __verify_dynamic_api_table_exists(self):
        if DYNAMIC_API_OBJECT_NAME not in self.utils.dynamic_objects:
            self.create_task("create", DYNAMIC_API_OBJECT_NAME, properties=DYNAMIC_API_PROPERTIES)

    """
    NAME
        __verify_users_table_exists - verifies the user management object exists as a dynamic object
    SYNOPSIS
        __verify_users_table_exists(self)
            self    -> the instance of the class
    DESCRIPTION
        If the user management object does not exist in dynamic_objects:
            1. create the dynamic object
            2. add a default master user
                email: ynathaniel@gmail.com
                pass: 1234
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __verify_users_table_exists(self):
        if USER_MANAGEMENT_OBJECT_NAME not in self.utils.dynamic_objects:
            self.create_task("create", USER_MANAGEMENT_OBJECT_NAME, properties=USER_MANAGEMENT_PROPERTIES)
            sleep(3)
            self.create_task("insert", USER_MANAGEMENT_OBJECT_NAME, insert_data={
                "name": unicode("Yoav - Master"),
                "username": unicode("ynathaniel"),
                "email": unicode("ynathaniel@gmail.com"),
                "password": unicode("1234"),
                "hidden_from_ui": True,
                "is_admin": True
            })

    """
    NAME
        __verify_alert_tables_exists - verifies the 2 alert objects exist as dynamic objects
    SYNOPSIS
        __verify_alert_tables_exists(self)
            self    -> the instance of the class
    DESCRIPTION
        Create any of the following dynamic objects if they don't exist as dynamic objects:
            alert rules
            alert finds
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __verify_alert_tables_exists(self):
        if ALERT_RULES_OBJECT_NAME not in self.utils.dynamic_objects:
            self.create_task("create", ALERT_RULES_OBJECT_NAME, properties=ALERT_RULES_PROPERTIES)

        if ALERT_FINDS_OBJECT_NAME not in self.utils.dynamic_objects:
            self.create_task("create", ALERT_FINDS_OBJECT_NAME, properties=ALERT_FINDS_PROPERTIES)

    """
    NAME
        __create_recent_cache - creates a recent events cache based on the last rows of all dynamic objects
    SYNOPSIS
        __create_recent_cache(self)
            self    -> the instance of the class
    DESCRIPTION
        Creates a list of all recent events from all non-default dynamic_objects
            each event is of the following format:
                {
                    "object_name": name of dynamic object,
                    "timestamp": datetime the table row/event was created
                }
        Crop the list to get the latest N events
            N = CACHE_SIZE (global variable)
    RETURNS
        List of latest N events
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __create_recent_cache(self):
        sleep(3)
        all_events = []
        for object_name, object_details in self.utils.dynamic_objects.iteritems():
            if object_name in DEFAULT_OBJECT_NAMES:
                continue

            events = self.pool.action.create_new_action((DBTask(action_type="select",
                                                                object_name=object_name,
                                                                select_data=["_timestamp_created"],
                                                                limit=15,
                                                                sort_by="_timestamp_created",
                                                                sort_order=False)))
            for e in events:
                all_events.append({
                    "object_name": object_name,
                    "timestamp": e.get("_timestamp_created")
                })

        latest_events = sorted(all_events, key=lambda k: k['timestamp'])
        latest_events.reverse()
        return latest_events[:CACHE_SIZE]

    """
    NAME
        __verify_object_counts - performs a double check on all dynamic objects to verify all dynamic objects have a
                                    row count
    SYNOPSIS
        __verify_object_counts(self)
            self    -> the instance of the class
    DESCRIPTION
        For all dynamic objects:
            If default attempt failed to find row count of the object's database table:
                check row count of table AGAIN
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __verify_object_counts(self):
        for object_name, props in self.utils.dynamic_objects.iteritems():
            if props.get("count") == -1:
                self.create_task("update_count", object_name)

    """
    NAME
        get_table_names_in_schema - gets the names of all the tables in the DB schema
    SYNOPSIS
        get_table_names_in_schema(self)
            self    -> the instance of the class
    DESCRIPTION
        uses SQLAlchemy inspector to extract table names from schema
    RETURNS
        list of table names
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def get_table_names_in_schema(self):
        return self.utils.insp.get_table_names(schema=DB_SCHEMA)

    """
    NAME
        get_columns_in_table - gets all the columns in a DB table
    SYNOPSIS
        get_columns_in_table(self, table)
            self    -> the instance of the class
            table   -> string name of a table
    DESCRIPTION
        uses SQLAlchemy inspector to extract table columns
    RETURNS
        list of table columns
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def get_columns_in_table(self, table):
        return self.utils.insp.get_columns(table_name=table, schema=DB_SCHEMA)

    """
    NAME
        get_object_names - gets the names of all of the recorded dynamic_objects
    SYNOPSIS
        get_object_names(self)
            self    -> the instance of the class
    DESCRIPTION
        gets the names of all of the recorded dynamic_objects
    RETURNS
        list of dynamic_object names
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def get_object_names(self):
        self.utils.printer.push(self.utils.dynamic_objects.keys())
        return self.utils.dynamic_objects.keys()

    """
    NAME
        create_task - creates a new DBTask to execute
    SYNOPSIS
        create_task(self, action_type, object_name, **kwargs)
            self            -> the instance of the class
            action_type     -> type of action to perform on the database
            object_name     -> name of dynamic_object to perform this action on
            **kwargs        -> additional named arguments needed to perform the requested type of action
    DESCRIPTION
        Creates and enqueues a new DBTask instance to the DBTaskList

        If action_type == "insert":
            add action as an event to self.recent_cache
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def create_task(self, action_type, object_name, **kwargs):
        # action_type
        #   create, drop, insert, delete, update, or select
        if action_type == "insert":
            if object_name[0] != "_":
                self.recent_cache.insert(0, {
                    "timestamp": datetime.now(),
                    "object_name": object_name
                })
                self.recent_cache = self.recent_cache[:CACHE_SIZE]

        new_task = DBTask(action_type, object_name, **kwargs)
        self.utils.printer.push("Creating new task: {0}".format(new_task))
        self.utils.tasks.push(new_task)

    """
    NAME
        close - safely closes the DBManager instance
    SYNOPSIS
        close(self)
            self    -> the instance of the class
    DESCRIPTION
        1. Set the pool_event to signal DBPool to safely exit
        2. Flush any remaining strings left to print in DBPrinter
        3. Record any pending tasks so they can be recovered next time DBManager starts up
            Note: pending tasks are actually recovered when DBUtils starts up - technically around the same time
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def close(self):
        self.pool_event.set()
        self.utils.printer.push("DBManager is exiting now")
        self.utils.printer.pop()
        self.utils.record_remaining_tasks()
