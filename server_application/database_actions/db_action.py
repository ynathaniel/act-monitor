from datetime import datetime
from threading import RLock, current_thread
from time import sleep

from sqlalchemy import *
from sqlalchemy import types
from sqlalchemy.orm import mapper

from ActMonitor.server_application import DB_SCHEMA, DYNAMIC_API_OBJECT_NAME, ALERT_RULES_OBJECT_NAME, ALERT_FINDS_OBJECT_NAME, DEFAULT_OBJECT_NAMES
from db_task import DBTask
from template_dynamic_object import TemplateDynamicObject


class DBAction:
    """
    NAME
        DBAction - responsible for performing ORM actions on the dynamic_objects
    VARIABLES
        member_vars_lock    -> RLock instance to make sure creating/dropping tables is thread-safe
        utils               -> DBUtils instance that carries most of the 'global' tools
        session             -> SQLAlchemy scoped sessionto perform an action
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """

    member_vars_lock = RLock()

    """
    NAME
        __init__ - constructor to set variables and load dynamic objects
    SYNOPSIS
        __init__(self, utils)
            self    -> the instance of the class
            utils   -> DBUtils instance that carries most of the 'global' tools
    DESCRIPTION
        initialize the instance and load dynamic objects
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __init__(self, utils):
        self.utils = utils

        self.__load_objects__()

    """
    NAME
        __load_objects__ - loads all dynamic_objects existing in the database
    SYNOPSIS
        __load_objects__(self)
            self    -> the instance of the class
    DESCRIPTION
        1. retrieves all existing tables
        2. for all default tables found in step 1, create a dynamic object
        3. if dynamic_api table was found in step 1, create a custom dynamic object for each row in dynamic_api table
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __load_objects__(self):
        # get list of all tables in the database
        self.utils.metadata.reflect(bind=self.utils.engine, schema=DB_SCHEMA)
        existing_tables = dict(self.utils.metadata.tables)

        # create the Dynamic Api object to begin mapping
        found_dynamic_api_table = False
        for table_name, table in existing_tables.iteritems():
            for default_object_name in DEFAULT_OBJECT_NAMES:
                if default_object_name.lower() in table_name:
                    self.__create_dynamic_object__(default_object_name, object_table=table)
                    if default_object_name == DYNAMIC_API_OBJECT_NAME:
                        found_dynamic_api_table = True

        if not found_dynamic_api_table:
            return

        print self.utils.dynamic_objects.keys()

        # get the rest of the objects
        existing_objects = self.create_new_action(DBTask(action_type="select",
                                                     object_name=DYNAMIC_API_OBJECT_NAME,
                                                     select_data=["object_name", "api_url"]))
        print existing_objects
        for exst_obj in list(existing_objects):
            object_api = exst_obj.get("api_url")
            object_table = existing_tables.get("{0}.{1}".format(DB_SCHEMA, object_api))
            object_name = str(exst_obj.get("object_name"))
            self.__create_dynamic_object__(object_name, object_table=object_table)

    """
    NAME
        create_new_action - routes dynamic object actions to their respective functions
    SYNOPSIS
        create_new_action(self, db_task)
            self    -> the instance of the class
            db_task -> DBTask instance of the task to perform
    DESCRIPTION
        This function acts as a router based on db_task.action (the action type).
        Currently, these are the supported actions:
            create - create a new dynamic object (includes a new class and a new DB table)
            drop - delete a dynamic object (includes deleting class and dropping DB table)
            insert - inserts data to some dynamic object (insert rows to table)
            delete - delete data from some dynamic object (delete rows from table)
            update - update data for some dynamic object (update rows from table)
            select - select data from some dynamic object (select rows from table)
            update_count - update the cached row count of some dynamic object (SELECT count(*) from SOME_TABLE)
        Unsupported action types will raise an exception

        All actions (except "create") perform the following:
            1. gather metadata about dynamic object (class, table, lock)
            2. use dynamic object's lock to make sure only 1 thread acts on an object at a time
            3. generate a DB session
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def create_new_action(self, db_task):
        if db_task.action == "create":
            # kwargs.get("properties")
            #   [ { "name": property name, "type": any db data type } ]
            #
            # db data types:
            #   Unicode(255), String, Float, Integer
            self.__create_dynamic_object__(db_task.object_name, properties=db_task.additional_args.get("properties"),
                               api_url=db_task.additional_args.get("api_url"))

        else:
            object_class, object_table, object_lock = self.__get_dynamic_object_properties__(db_task.object_name)

            with object_lock:
                self.__begin_dynamic_action__()

                if db_task.action == "drop":
                    self.__drop_dynamic_object__(db_task.object_name, object_table)
                else:
                    if db_task.action == "insert":
                        # kwargs.get("insert_data")
                        #   one: { all object properties and values to insert }
                        #   many: [ { all object properties and values to insert } ]
                        insert_data = db_task.additional_args.get("insert_data", {})
                        self.__insert_record__(object_name=db_task.object_name,
                                               object_class=object_class,
                                               insert_data=insert_data)
                    elif db_task.action == "delete":
                        # kwargs.get("where_data")
                        #   { some object properties and values for delete filter }
                        # kwargs.get("limit")
                        #   number of rows to delete
                        # kwargs.get("offset")
                        #   offset of where to start query
                        where_data = db_task.additional_args.get("where_data", {})
                        limit = db_task.additional_args.get("limit", 0)
                        offset = db_task.additional_args.get("offset", 0)
                        self.__delete_record__(object_name=db_task.object_name,
                                               object_class=object_class,
                                               where_data=where_data,
                                               limit=limit,
                                               offset=offset)
                    elif db_task.action == "update":
                        # kwargs.get("where_data")
                        #   { some object properties and values for delete filter }
                        # kwargs.get("update_data")
                        #   { some object properties and values to update }
                        # kwargs.get("limit")
                        #   number of rows to update
                        # kwargs.get("offset")
                        #   offset of where to start query
                        where_data = db_task.additional_args.get("where_data", {})
                        update_data = db_task.additional_args.get("update_data", {})
                        limit = db_task.additional_args.get("limit", 0)
                        offset = db_task.additional_args.get("offset", 0)
                        self.__update_record__(object_name=db_task.object_name,
                                               object_class=object_class,
                                               where_data=where_data,
                                               update_data=update_data,
                                               limit=limit,
                                               offset=offset)
                    elif db_task.action == "select":
                        # where_data
                        #   { property_to_filter_by: value_to_filter_by }
                        # kwargs.get("select_data")
                        #   [ some object properties to retrieve ]
                        # kwargs.get("limit")
                        #   number of rows to retrieve
                        # kwargs.get("offset")
                        #   offset of where to start query
                        # kwargs.get("sort_by")
                        #   column/property to sort by (default is "_id")
                        # kwargs.get("sort_order")
                        #   True if ascending (default), False if descending
                        where_data = db_task.additional_args.get("where_data", {})
                        select_data = db_task.additional_args.get("select_data", [])
                        limit = db_task.additional_args.get("limit", 0)
                        offset = db_task.additional_args.get("offset", 0)
                        sort_by = db_task.additional_args.get("sort_by", "_id")
                        sort_order = db_task.additional_args.get("sort_order", True)
                        data = self.__select_record__(object_name=db_task.object_name,
                                                      object_class=object_class,
                                                      where_data=where_data,
                                                      select_data=select_data,
                                                      limit=limit,
                                                      offset=offset,
                                                      sort_by=sort_by,
                                                      sort_order=sort_order)
                        self.__end_dynamic_action__()
                        return data

                    elif db_task.action == "update_count":
                        while self.utils.dynamic_objects[db_task.object_name]["count"] == -1:
                            self.__update_count__(db_task.object_name, object_class)
                        self.__end_dynamic_action__()

                    else:
                        self.__end_dynamic_action__()
                        raise ValueError("Action type invalid: {0}".format(db_task.action_type))

                self.__end_dynamic_action__()

    """
    NAME
        __get_dynamic_object_properties__ - retrieves matadata of dynamic object
    SYNOPSIS
        __get_dynamic_object_properties__(self, object_name)
            self        -> the instance of the class
            object_name -> string name of dynamic object
    DESCRIPTION
        If object_name is not a name of an existing dynamic object, raise ValueError

        Gather the dynamic object's metadata and return it
    RETURNS
        dynamic object's class, dynamic object's table, dynamic object's lock
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __get_dynamic_object_properties__(self, object_name):
        if object_name in self.utils.dynamic_objects:
            dynamic_object = self.utils.dynamic_objects.get(object_name)

            dynamic_class = dynamic_object.get("class")
            dynamic_table = dynamic_object.get("table")
            dynamic_lock = dynamic_object.get("lock")

            return dynamic_class, dynamic_table, dynamic_lock
        else:
            raise ValueError("Unrecognized object name: {0}".format(object_name))

    ####
    # actions on dynamic objects
    ####

    """
    NAME
        __drop_dynamic_object__ - delete a dynamic object
    SYNOPSIS
        __drop_dynamic_object__(self, object_name, object_table)
            self            -> the instance of the class
            object_name     -> string name of dynamic object
            object_table    -> SQLAlchemy Table of the dynamic object
    DESCRIPTION
        1. delete dynamic object's API from dynamic api table
            removes this api from the system
        2. drop database table (if exists)
        3. delete dynamic object from the list of dynamic_objects
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __drop_dynamic_object__(self, object_name, object_table):
        self.utils.printer.push("{0} - Dynamic table '{1}' dropped.".format(current_thread().name, object_name))

        # get rid of the api first
        self.__delete_dynamic_api__(object_name)

        with self.member_vars_lock:
            self.utils.metadata.drop_all(tables=[object_table], checkfirst=True)
            # object_table.drop(self.utils.engine)
            self.utils.metadata.reflect(bind=self.utils.engine, schema=DB_SCHEMA)

        del self.utils.dynamic_objects[object_name]

    """
    NAME
        __create_dynamic_object__ - create a dynamic object
    SYNOPSIS
        __create_dynamic_object__(self, object_name, properties=None, object_table=None, api_url=None)
            self            -> the instance of the class
            object_name     -> string name of dynamic object
            properties      -> list of column specifications to include in DB table (optional)
            object_table    -> SQLAlchemy Table of the dynamic object (optional)
            api_url         -> string API name of dynamic object - also the name of the table (optional)
    DESCRIPTION
        This function has 2 use cases:
            1. correlate an existing table with a new object (should only happen on start up)
                required arguments: object_table

            2. create a new table for a new object
                required arguments: properties and api_url
                requires to NOT specify object_table

                if any required arguments are missing/None, raise ValueError

        In both use cases:
            1. an object class is recorded
            2. a dynamic object object is recorded

    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __create_dynamic_object__(self, object_name, properties=None, object_table=None, api_url=None):
        object_class = self.__create_dynamic_class__(object_name)
        table_name = object_name.lower()

        is_new_table = False

        if object_table is None:
            if properties is None:
                raise ValueError("Attempt to create new table '{0}' without properties.".format(table_name))
            elif api_url is None and not object_name in DEFAULT_OBJECT_NAMES:
                raise ValueError("Attempt to create new table '{0}' without api_url.".format(table_name))
            else:
                if not object_name in DEFAULT_OBJECT_NAMES:
                    self.__add_dynamic_api__(object_name, api_url)
                else:
                    api_url = table_name

                object_table = self.__create_dynamic_table__(api_url, properties)
                is_new_table = True

        self.__record_dynamic_object__(object_name, object_class, object_table, is_new_table)

        with self.member_vars_lock:
            self.utils.metadata.reflect(bind=self.utils.engine, schema=DB_SCHEMA)

    """
    NAME
        __create_dynamic_class__ - create a class for the dynamic object
    SYNOPSIS
        __create_dynamic_class__(self, object_name)
            self            -> the instance of the class
            object_name     -> string name of dynamic object
    DESCRIPTION
        Creates a new class for the dynamic object using TemplateDynamicObject class
    RETURNS
        New class for the dynamic object
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __create_dynamic_class__(self, object_name):
        new_object = type(object_name, (TemplateDynamicObject, ), {})
        return new_object

    """
    NAME
        __create_dynamic_table__ - create a DB table for the dynamic object
    SYNOPSIS
        __create_dynamic_table__(self, table_name, table_columns)
            self            -> the instance of the class
            table_name      -> string name of the DB table
            table_columns   -> list of table columns. Each column should have the following format
                {
                    "name": string column name,
                    "type": string column type - check get_sql_column(column_type) for supported types,
                    "nullable": bool if column can have null value (default is True),
                    "unique": bool if column must have a unique value (default is False),
                    "default": default value of column
                }
    DESCRIPTION
        Creates a new DB table with the columns specified - thread-safe
    RETURNS
        SQLAlchemy Table instance of dynamic object
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __create_dynamic_table__(self, table_name, table_columns):
        new_table = Table(table_name, self.utils.metadata, Column("_id", Integer, primary_key=True),
                          Column("_timestamp_created", DateTime, nullable=False),
                          Column("_timestamp_modified", DateTime, nullable=False),
                          *(Column(col.get("name"), get_sql_column(col.get("type")),
                                nullable=col.get("nullable", True), unique=col.get("unique", False),
                                default=col.get("default")) for col in table_columns), schema=DB_SCHEMA)

        with self.member_vars_lock:
            self.utils.metadata.create_all()

        return new_table

    """
    NAME
        __record_dynamic_object__ - record a new dynamic object and map class to table
    SYNOPSIS
        __record_dynamic_object__(self, object_name, object_class, object_table, is_new_table)
            self            -> the instance of the class
            object_name     -> string name of the dynamic object
            object_class    -> class representing the dynamic object
            object_table    -> existing SQLAlchemy Table of the dynamic object
            is_new_table    -> boolean value of use case
                True if this table was just created
                False if using an existing table
    DESCRIPTION
        Add dynamic object as key to the dictionary of dynamic_objects with a dictionary value containing:
            class, table, api_url/table name, lock, row count

        Map the class to the table so they correlate - new class instances create new rows

        If is_new_table == False:
            create and enqueue a DBTask to update the count of the table
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __record_dynamic_object__(self, object_name, object_class, object_table, is_new_table):
        self.utils.dynamic_objects[object_name] = {
            "class": object_class,
            "table": object_table,
            "api": object_name.lower().replace(" ", "_").replace("-", "_"),
            "lock": RLock(),
            "count": -1
        }

        mapper(object_class, object_table)
        sleep(0.1)

        if is_new_table:
            self.utils.dynamic_objects[object_name]["count"] = 0
        else:
            self.utils.tasks.push(DBTask("update_count", object_name))

    """
    NAME
        __add_dynamic_api__ - add the new object to the dynamic_api table
    SYNOPSIS
        __add_dynamic_api__(self, object_name, api_url)
            self            -> the instance of the class
            object_name     -> string name of the dynamic object
            api_url         -> string url name of object
    DESCRIPTION
        Inserts object name and api_url of new dynamic object to dynamic_api table

        Allows to keep track of the dynamic object on future runs of the program
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __add_dynamic_api__(self, object_name, api_url):
        api_data = {
            "object_name": object_name,
            "api_url": api_url
        }

        new_task = DBTask("insert", DYNAMIC_API_OBJECT_NAME, insert_data=api_data)
        self.create_new_action(new_task)

    """
    NAME
        __delete_dynamic_api__ - delete a dynamic object from the dynamic_api table
    SYNOPSIS
        __delete_dynamic_api__(self, object_name, api_url)
            self            -> the instance of the class
            object_name     -> string name of the dynamic object
    DESCRIPTION
        Deletes row containing the object name of the dynamic object

        Stops to keep track of the dynamic object on future runs of the program
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __delete_dynamic_api__(self, object_name):
        where_data = {
            "object_name": object_name
        }
        limit = 1

        new_task = DBTask("delete", DYNAMIC_API_OBJECT_NAME, where_data=where_data, limit=limit)
        self.create_new_action(new_task)

    ####
    # actions on records
    ####

    """
    NAME
        __insert_record__ - insert new rows to a table
    SYNOPSIS
        __insert_record__(self, object_name, object_class, insert_data)
            self            -> the instance of the class
            object_name     -> string name of the dynamic object
            object_class    -> class representing the dynamic object
            insert_data     -> 2 options
                1. dictionary of columns as keys and values as values
                2. list of dictionaries from option 1
    DESCRIPTION
        Flexible insert that allows to add one or multiple rows to a table

        By default - no matter what columns entered - timestamps of creation and modification are
            ALSO included in the new rows

        For each row inserted
            increase count of dynamic object
            if object is not a default object
                check to see if row matches any alert rule
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __insert_record__(self, object_name, object_class, insert_data):
        # insert_data
        #   if just one row
        #       { property_to_add: value_to_add }
        #   if more than one row
        #       [ { property_to_add: value_to_add } ]
        if type(insert_data) is dict:
            self.utils.printer.push(["Inserting to '{0}' 1 new record now.".format(object_name),
                                     "\t{0}".format(insert_data)
                                     ])

            # add timestamp to new rows
            insert_data['_timestamp_created'] = datetime.now()
            insert_data['_timestamp_modified'] = datetime.now()

            new_object_instance = object_class(**insert_data)
            self.session.add(new_object_instance)

            if object_name[0] != "_":
                self.__check_if_to_create_alert(object_name, insert_data)

            self.utils.dynamic_objects[object_name]["count"] += 1
        else:
            insert_count = len(insert_data)
            self.utils.printer.push(["Inserting to '{0}' {1} new records now.".format(object_name, insert_count),
                                     "\t{0}".format(insert_data)
                                     ])
            for new_record in insert_data:

                # add timestamp to new records
                new_record['_timestamp_created'] = datetime.now()
                new_record['_timestamp_modified'] = datetime.now()

                new_object_instance = object_class(**new_record)
                self.session.add(new_object_instance)

                if object_name[0] != "_":
                    self.__check_if_to_create_alert(object_name, new_record)

            self.utils.dynamic_objects[object_name]["count"] += insert_count

    """
    NAME
        __delete_record__ - delete rows from a table
    SYNOPSIS
        __delete_record__(self, object_name, object_class, where_data, limit, offset)
            self            -> the instance of the class
            object_name     -> string name of the dynamic object
            object_class    -> class representing the dynamic object
            where_data      -> a dictionary indicating how to filter rows to delete
            limit           -> max number of rows to delete (0 means all rows)
            offset          -> at which row number to start this query (0 is typical)
    DESCRIPTION
        Deletes filtered rows from a table

        Reduces count of dynamic object by the number of rows deleted
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __delete_record__(self, object_name, object_class, where_data, limit, offset):
        # where_data
        #   { property_to_filter_by: value_to_filter_by }
        self.utils.printer.push(["{0} - Deleting from '{0}' {1} record(s) from offset {3}."
                                    .format(current_thread().name, object_name, __limit_string__(limit), offset),
                                 "\tDelete data: {0}".format(where_data)
                                ])

        if limit == 0:
            # all results from offset
            res = self.session.query(object_class).filter_by(**where_data).offset(offset).all()
        else:
            # limit results from offset
            res = self.session.query(object_class).filter_by(**where_data).offset(offset).limit(limit).all()

        self.utils.dynamic_objects[object_name]["count"] -= len(res)

        for row in res:
            self.session.delete(row)

    """
    NAME
        __update_record__ - update rows from a table
    SYNOPSIS
        __update_record__(self, object_name, object_class, where_data, update_data, limit, offset)
            self            -> the instance of the class
            object_name     -> string name of the dynamic object
            object_class    -> class representing the dynamic object
            where_data      -> a dictionary indicating how to filter rows to delete
            update_data     -> a dictionary indicating which columns should be updated with which values
            limit           -> max number of rows to delete (0 means all rows)
            offset          -> at which row number to start this query (0 is typical)
    DESCRIPTION
        Updates filtered rows in a table
        Also updates the _timestamp_modified column to the current timestamp
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __update_record__(self, object_name, object_class, where_data, update_data, limit, offset):
        # where_data
        #   { property_to_filter_by: value_to_filter_by }
        # select_data
        #   { property_to_update: updated_value }
        self.utils.printer.push(["{0} - Updating '{1}' {2} record(s) from offset {3}."
                                    .format(current_thread().name, object_name, __limit_string__(limit), offset),
                                 "\tWhere data: {0}".format(where_data),
                                 "\tUpdate data: {0}".format(update_data)
                                ])

        if limit < 1:
            # all results from offset
            res = self.session.query(object_class).filter_by(**where_data).offset(offset).all()
        else:
            # limit results from offset
            res = self.session.query(object_class).filter_by(**where_data).offset(offset).limit(limit).all()

        for row in res:
            for attr, value in update_data.iteritems():
                if "timestamp" in attr:
                    continue
                setattr(row, attr, value)
            setattr(row, "_timestamp_modified", datetime.now())

    """
    NAME
        __select_record__ - select rows from a table
    SYNOPSIS
        __select_record__(self, object_name, object_class, where_data, select_data, limit, offset, sort_by, sort_order)
            self            -> the instance of the class
            object_name     -> string name of the dynamic object
            object_class    -> class representing the dynamic object
            where_data      -> a dictionary indicating how to filter rows to delete
            select_data     -> a list of column names to select
            limit           -> max number of rows to delete (0 means all rows)
            offset          -> at which row number to start this query (0 is typical)
            sort_by         -> column/property of dynamic object to sort by (default is _id)
            sort_order      -> boolean of how to sort
                True = Ascending
                False = Descending
    DESCRIPTION
        Selects filtered rows from a table
    RETURNS
        list of dictionaries of columns and values. Each item in the list is 1 row.
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __select_record__(self, object_name, object_class, where_data, select_data, limit, offset, sort_by, sort_order):
        # where_data
        #   { property_to_filter_by: value_to_filter_by }
        # kwargs.get("select_data")
        #   [ some object properties to retrieve ]
        # kwargs.get("limit")
        #   number of rows to retrieve
        # kwargs.get("offset")
        #   offset of where to start query
        # kwargs.get("sort_by")
        #   column/property to sort by
        # kwargs.get("sort_order")
        #   True if ascending (default), False if descending
        self.utils.printer.push(["{0} - Retrieving from '{1}' {2} record(s) from offset {3}."
                                    .format(current_thread().name, object_name, __limit_string__(limit), offset),
                                 "\tWhere data: {0}".format(where_data),
                                 "\tSelect data: {0}".format(select_data)
                                 ])
        query = self.session.query(object_class).filter_by(**where_data)

        if sort_order:
            query = query.order_by(getattr(object_class, sort_by))
        else:
            query = query.order_by(desc(getattr(object_class, sort_by)))

        if limit < 1:
            # all results from offset
            res = query.offset(offset).all()
        else:
            # limit results from offset
            res = query.offset(offset).limit(limit).all()

        selected_data_from_rows = []
        for row in res:
            row_selected_data = {}
            for selected_column in select_data:
                row_selected_data[selected_column] = getattr(row, selected_column)

            selected_data_from_rows.append(row_selected_data)

        return selected_data_from_rows

    """
    NAME
        __update_count__ - updates the row count of a dynamic object
    SYNOPSIS
        __update_count__(self, object_name, object_class)
            self            -> the instance of the class
            object_name     -> string name of the dynamic object
            object_class    -> class representing the dynamic object
    DESCRIPTION
        Updates row count of a dynamic object
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __update_count__(self, object_name, object_class):
        self.utils.printer.push("{0} - Retrieving 'count' from '{1}'".format(current_thread().name, object_name))

        res = int(self.session.query(func.count(object_class._id)).scalar())

        self.utils.dynamic_objects[object_name]["count"] = res

    ###
    # action helpers
    ###

    """
    NAME
        __begin_dynamic_action__ - starts a new database action session
    SYNOPSIS
        __begin_dynamic_action__(self)
            self    -> the instance of the class
    DESCRIPTION
        Starts a new database action session
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __begin_dynamic_action__(self):
        self.session = self.utils.session_class()

    """
    NAME
        __end_dynamic_action__ - commits a database action session
    SYNOPSIS
        __end_dynamic_action__(self)
            self    -> the instance of the class
    DESCRIPTION
        Ends a database action session by committing changes
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __end_dynamic_action__(self):
        self.session.commit()

    """
    NAME
        __check_if_to_create_alert - checks and potentially creates a new alert after reviewing a new row
    SYNOPSIS
        __check_if_to_create_alert(self, object_name, insert_data)
            self        -> the instance of the class
            object_name -> string name of the dynamic object
            insert_data -> dictionary of values inserted in a new row
    DESCRIPTION
        1. collect the last row ID inserted - this is the row recently inserted
        2. collects all alert rules and filter them to use only alert rules belnging to this object_name
        3. for any rule matching insert_data:
            1. create a new alert finding with the row ID (step 1)
            2. enqueue DBTask to insert alert finding to alert_finds table
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __check_if_to_create_alert(self, object_name, insert_data):
        columns_to_select = ["name", "object_name", "column_name", "column_value"]
        alert_rules = self.create_new_action(DBTask("select", ALERT_RULES_OBJECT_NAME, select_data=columns_to_select))

        all_object_ids = self.create_new_action(DBTask("select", object_name, select_data=["_id"]))
        all_object_ids = [row.get("_id") for row in all_object_ids]
        new_id = max(all_object_ids)

        self.utils.printer.push("NEW ALERT CREATION ATTEMPT WITH THIS ID: {0}".format(new_id))

        for rule in alert_rules:
            if rule.get("object_name") == object_name:
                self.utils.printer.push(["INSERT VALUE: {0}".format(type(insert_data.get(rule.get("column_name")))),
                                         "COLUMN VALUE: {0}".format(type(rule.get("column_value")))])
                if str(insert_data.get(rule.get("column_name"))) == str(rule.get("column_value")):
                    new_alert_data = {
                        "rule_name": rule.get("name"),
                        "object_name": object_name,
                        "column_name": rule.get("column_name"),
                        "found_value": insert_data[rule.get("column_name")],
                        "found_id": new_id
                    }
                    self.utils.printer.push("CREATING ALERT!!!")
                    new_alert_task = DBTask("insert", ALERT_FINDS_OBJECT_NAME, insert_data=new_alert_data)

                    self.utils.tasks.push(new_alert_task)


"""
NAME
    __limit_string__ - attempts to convert the limit of an action to a string
SYNOPSIS
    __limit_string__(original_limit)
        original_limit      -> an integer limit of the max rows affected by some action
DESCRIPTION
    Attempts to convert the limit of an action to a string if original_limit is 0 or below
RETURNS
    limit as a string or original_limit
AUTHOR
    Yoav Nathaniel
DATE
    4/25/2016
"""
def __limit_string__(original_limit):
    if original_limit < 1:
        return "all"
    else:
        return original_limit


"""
NAME
    get_sql_column - create a DB table for the dynamic object
SYNOPSIS
    get_sql_column(column_type)
        column_type     -> unicode/string name of column type OR actual SQLAlchemy column type
DESCRIPTION
    If column type is string or unicode:
        If column type is supported:
            return the relevant column type
        Else:
            raise ValueError
    Else:
        return parameter as is
RETURNS
    SQLAlchemy Column correlating to parameter
AUTHOR
    Yoav Nathaniel
DATE
    4/25/2016
"""
def get_sql_column(column_type):
    if type(column_type) is unicode or type(column_type) is str:
        if column_type == "String":
            return types.String
        if column_type == "Integer":
            return types.Integer
        if column_type == "Unicode":
            return types.Unicode
        if column_type == "Boolean":
            return types.Boolean
        if column_type == "DateTime":
            return types.DateTime
        if column_type == "Float":
            return types.Float
        else:
            raise ValueError("Received unexpected column type : {0}".format(column_type))
    else:
        return column_type
