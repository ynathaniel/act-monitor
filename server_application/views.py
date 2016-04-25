from flask import Flask, jsonify, render_template, request, redirect, session

import json
from collections import Counter
from functools import wraps
from time import sleep

from database_actions.db_manager import DBManager
from database_actions.db_task import DBTask
from database_actions import USER_MANAGEMENT_OBJECT_NAME, ALERT_RULES_OBJECT_NAME, ALERT_FINDS_OBJECT_NAME, DEFAULT_OBJECT_NAMES



def stop_backend(db_manager):
    """
    NAME
        stop_backend - stops the backend to close all the resources safely
    SYNOPSIS
        stop_backend(db_manager)
            db_manager      -> DBManager instance to close
    DESCRIPTION
        close the db_manager instance - safely close all threads and resources
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    """
    db_manager.close()


def start_backend():
    """
    NAME
        start_backend - starts the DatabaseManager and Flask application
    SYNOPSIS
        start_backend()
    DESCRIPTION
        This starts the program by creating:
            Instance of Flask
                All of its routes
            Instance of DBManager
    RETURNS
        db_manager      -> Instance of DBManager to that is finished with
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    """
    db_manager = DBManager()
    app = Flask(__name__)

    app.secret_key = 'ActivityMonitor key'

    '''
    NAME
        is_authenticated - Checks if a Flask session is allowed into the system
    SYNOPSIS
        is_authenticated(func)
            func            -> function to perform if authenticated
    DESCRIPTION
        This function is called before a route function to verify the requesting session is authenticated.
        If the session is authenticated:
            go to the function corresponding with the request path
        Else:
            redirect the request to the login page (allows user to login)
    RETURNS
        decorated_function  -> results of the condition. The decorated function allows access to route function
            or redirects to '/login/'
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    '''
    def is_authenticated(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect("/login/")
            return func(*args, **kwargs)

        return decorated_function

    ###########
    # Rendered HTML JINJA2 Pages
    ###########

    '''
    NAME
        login - Flask route for the login page
    SYNOPSIS
        login()
    DESCRIPTION
        Receives multiple request types heading to the login page
        If request type is "GET":
            If session is authenticated:
                redirect to index/dashboard page
            else:
                return the JINJA2 template for the login page - allow the user to login
        else:
            if session is authenticated:
                return "success" status
            else:
                review request body for username and password
                attempt to login with credentials based on users in the database
                if successful login:
                    redirect to index/dashboard page
                else:
                    return error
    RETURNS
        Either a JSON object or a rendered JINJA2 template representing status of login attempt
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    '''
    @app.route("/login/", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == 'POST':
            if session.get('logged_in'):
                return jsonify({"status": "success"})

            data = request.get_json(force=True)
            where_data = {
                "email": str(data.get("email")),
                "password": str(data.get("password"))
            }
            column_data = ["name"]

            matching_user = select_data(USER_MANAGEMENT_OBJECT_NAME, where_data=where_data, column_data=column_data)
            if len(matching_user) == 0:
                return jsonify({"status": "fail"})
            else:
                session['logged_in'] = True
                session['user_name'] = matching_user[0].get("name")
                return jsonify({"status": "success"})
        else:
            if session.get('logged_in'):
                return redirect("/")

        return render_template('login.html', error=error)

    '''
    NAME
        logout - Flask route for the logout page
    SYNOPSIS
        logout()
    DESCRIPTION
        Receives multiple request types heading to the login page
        If session is logged in:
            log the session out
        redirect to '/login/'
    RETURNS
        redirect request to '/login/'
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    '''
    @app.route("/logout/", methods=["GET", "POST"])
    @is_authenticated
    def logout():
        session['logged_in'] = False
        sleep(0.5)
        return redirect("/login/")

    '''
    NAME
        get_index - Flask route for the index page
    SYNOPSIS
        get_index()
    DESCRIPTION
        Gathers data from custom objects and from the database to display in the dashboard
    RETURNS
        rendered JINJA2 template of the index/dashboard page
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    '''
    @app.route("/", methods=["GET"])
    @is_authenticated
    def get_index():
        all_object_names = []
        for name in db_manager.get_object_names():
            if name in DEFAULT_OBJECT_NAMES:
                continue
            all_object_names.append(str(name).replace("_", " "))

        labels = []
        values = []
        if len(all_object_names) > 0:
            labels, values = select_graph_data(all_object_names[0])

        data = {"name": "Dashboard",
                "user_name": session.get("user_name"),
                "cache": db_manager.recent_cache,
                "object_names": all_object_names,
                "graph_labels": labels,
                "graph_values": values,
                "alerts_count": db_manager.utils.dynamic_objects[ALERT_FINDS_OBJECT_NAME].get("count")
                }

        return render_template("index.html", data=data)

    '''
    NAME
        get_all_trackers - Flask route for the all trackers page
    SYNOPSIS
        get_all_trackers()
    DESCRIPTION
        Gathers data from custom objects to display in the table format about all of the available APIs
    RETURNS
        rendered JINJA2 template of the all trackers page
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    '''
    @app.route("/trackers/", methods=["GET"])
    @is_authenticated
    def get_all_trackers():
        data = {
            "name": "All Trackers",
            "user_name": session.get("user_name"),
            "trackers": []
        }
        for object_name, values in db_manager.utils.dynamic_objects.iteritems():
            if object_name in DEFAULT_OBJECT_NAMES:
                continue

            data["trackers"].append({
                "name": object_name,
                "count": values["count"],
                "api": values["api"]
            })
        return render_template("all_trackers.html", data=data)

    '''
    NAME
        get_new_tracker_form - Flask route for the new tracker form page
    SYNOPSIS
        get_new_tracker_form()
    DESCRIPTION
        Renders the new tracker form page
    RETURNS
        rendered JINJA2 template of the new tracker form page
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    '''
    @app.route("/trackers/new/", methods=["GET"])
    @is_authenticated
    def get_new_tracker_form():
        data = {"name": "New Tracker",
                "user_name": session.get("user_name"),}
        return render_template("new_tracker.html", data=data)

    '''
    NAME
        get_tracker_profile - Flask route for the tracker profile page
    SYNOPSIS
        get_tracker_profile(tracker_api)
            tracker_api     -> the name of the object/tracker api to present
    DESCRIPTION
        Collects data about the parameter tracker.
            Data includes tracker columns (and types) and 5 rows from the tracker table
        Render a JINJA2 template of the tracker profile page for the paramater tracker
    RETURNS
        rendered JINJA2 template of the tracker profile page
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    '''
    @app.route("/trackers/profile/<tracker_api>", methods=["GET"])
    @is_authenticated
    def get_tracker_profile(tracker_api):
        tracker_name = None

        # get object name from object api
        for object_name, object_props in db_manager.utils.dynamic_objects.iteritems():
            if object_props.get("api") == tracker_api:
                tracker_name = object_name

        # make sure tracker is found and registered in the system
        if tracker_name is None:
            data = {"name": "Not Found"}
            return render_template("not_found.html", data=data), 404

        # get all column names and types of the api
        object_columns = {}
        object_columns_example_request = {}
        for item in db_manager.get_columns_in_table(tracker_api):
            col_name = str(item.get("name"))
            col_type = str(item.get("type"))

            # skip all of the predefined (default) table properties
            if col_name == "_timestamp_modified":
                continue
            if col_name[0] == "_":
                object_columns[col_name] = col_type.replace("()", "").split(" ")[0]
            else:
                object_columns[col_name] = col_type.replace("()", "").split(" ")[0]
                object_columns_example_request[col_name] = col_type.replace("()", "").split(" ")[0]

        # get all results from the tracker's table
        tracker_data = select_data(object_name=tracker_name,
                                   where_data={},
                                   column_data=object_columns.keys(),
                                   limit=7,
                                   offset=0)

        # generate data to be inserted into the profile page
        data = {
            "name": tracker_name,
            "user_name": session.get("user_name"),
            "json_module": json,
            "url": "https://customer.actmonitor.com/api/tracking/insert/{0}".format(tracker_api),
            "columns": object_columns,
            "example_columns": object_columns_example_request,
            "tracker_data": tracker_data
        }
        return render_template("tracker_profile.html", data=data)

    '''
    NAME
        get_user_management - Flask route for the user management page
    SYNOPSIS
        get_user_management(tracker_api)
    DESCRIPTION
        Collects data about the parameter tracker.
            Data includes tracker columns (and types) and 5 rows from the tracker table
        Render a JINJA2 template of the tracker profile page for the paramater tracker
    RETURNS
        rendered JINJA2 template of the user management page
    AUTHOR
        Yoav Nathaniel
    DATE
        4/11/2016
    '''
    @app.route("/user-management/", methods=["GET"])
    @is_authenticated
    def get_user_management():
        users_data = select_data(object_name=USER_MANAGEMENT_OBJECT_NAME,
                                 where_data={"hidden_from_ui": False},
                                 column_data=["name", "email", "is_admin"],
                                 limit=0,
                                 offset=0)

        data = {"name": "User Management",
                "user_name": session.get("user_name"),
                "users": users_data}

        return render_template("user_management.html", data=data)

    '''
    NAME
        get_alerts_page - Flask route for the all alerts page
    SYNOPSIS
        get_alerts_page()
    DESCRIPTION
        Collects data from all alert rules and alert findings
            This data will be rendered and displayed in 2 tables
    RETURNS
        rendered JINJA2 template of the alerts page
    AUTHOR
        Yoav Nathaniel
    DATE
        4/15/2016
    '''
    @app.route("/alerts/", methods=["GET"])
    @is_authenticated
    def get_alerts_page():
        rule_data = select_data(object_name="_Alert_Rules",
                                   where_data={},
                                   column_data=["_id", "name", "object_name", "column_name", "column_value"],
                                   limit=7,
                                   offset=0)

        alert_data = select_data(object_name="_Alert_Finds",
                                   where_data={},
                                   column_data=["_id", "rule_name", "object_name", "column_name", "found_value"],
                                   limit=7,
                                   offset=0)

        data = {
            "name": "Alerts",
            "user_name": session.get("user_name"),
            "rules": rule_data,
            "alerts": alert_data
        }
        return render_template("alerts.html", data=data)

    '''
    NAME
        page_not_found - Flask route for 404 (not found) error
    SYNOPSIS
        page_not_found()
    DESCRIPTION
        this route will be displayed when an unrecognized URL path is requested
    RETURNS
        rendered JINJA2 template of the alerts page
    AUTHOR
        Yoav Nathaniel
    DATE
        4/15/2016
    '''
    @app.errorhandler(404)
    @is_authenticated
    def page_not_found(e):
        data = {
            "name": "Not Found",
            "user_name": session.get("user_name"),}
        return render_template('not_found.html', data=data), 404

    ###########
    # APIs
    ###########

    '''
    NAME
        get_all_objects - Flask route for API to get all dynamic object names
    SYNOPSIS
        get_all_objects()
    DESCRIPTION
        API only accepting GET requests
        Provides a list of all dynamic object names in JSON format
    RETURNS
        names of dynamic objects in the following format:
            { "object_names": [ "name1", "name2" ] }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/15/2016
    '''
    @app.route("/api/tracking/monitored-names", methods=["GET"])
    @is_authenticated
    def get_all_objects():
        all_object_names = []
        for name in db_manager.get_object_names():
            if name == "Dynamic_Apis":
                # continue
                pass
            all_object_names.append(str(name).replace("_", " "))

        return jsonify({"object_names": all_object_names})

    '''
    NAME
        create_api - Flask route for API to create a new dynamic object
    SYNOPSIS
        create_api()
    DESCRIPTION
        API only accepting POST requests
        Allows authenticated users to create a dynamic object
            This also creates a new database table and a new class

        Request body looks like the following:
            {
                "name": object_name,
                "properties": [
                    {
                        "name": property_name,
                        "type": table_column_type,
                        "nullable": True/False,
                        "unique": True/False
                    }
                ]
            }
    RETURNS
        JSON object with status of dynamic object creation.
    AUTHOR
        Yoav Nathaniel
    DATE
        4/17/2016
    '''
    @app.route("/api/tracking/create", methods=["POST"])
    @is_authenticated
    def create_api():
        # convert POSTed data
        data = request.get_json(force=True)

        # extract needed variables
        object_name = data.get("name")
        object_properties = data.get("properties")
        api_url = object_name.lower().replace(" ", "_").replace("-", "_")

        if object_name[0] == "_":
            return jsonify({
                "status": "fail",
                "status_description": "Invalid tracker name! Cannot begin with '_'."
            })

        # make sure not duplicating another object
        names_of_existing_objects = db_manager.utils.dynamic_objects.keys()
        if any(name.lower() == api_url for name in names_of_existing_objects):
            return jsonify({
                "status": "fail",
                "status_description": "Attempted to duplicate a tracker!"
            })

        # not duplicating! create a new task to create object
        db_manager.create_task("create", object_name, properties=object_properties, api_url=api_url)
        return jsonify({"status": "success"})

    '''
    NAME
        drop_api - Flask route for API to delete a dynamic object
    SYNOPSIS
        drop_api()
    DESCRIPTION
        API only accepting POST requests
        Allows authenticated users to delete a dynamic object
            This also deletes the objects's database table and class
    RETURNS
        { "status": "success" }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/17/2016
    '''
    @app.route("/api/tracking/drop", methods=["POST"])
    @is_authenticated
    def drop_api():
        # convert POSTed data
        data = request.get_json(force=True)

        object_name = data.get("name")

        db_manager.create_task("drop", object_name)
        return jsonify({"status": "success"})

    '''
    NAME
        insert_data_api - Flask route for API to insert data to a dynamic object
    SYNOPSIS
        insert_data_api(object_name)
            object_name     -> name of object to insert/append to
    DESCRIPTION
        API only accepting POST requests
        Allows authenticated users to insert data to a dynamic object
            adds another row to the table
    RETURNS
        { "status": "success" }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/19/2016
    '''
    @app.route("/api/tracking/insert/<object_name>", methods=["POST"])
    def insert_data_api(object_name):
        data = request.get_json(force=True)
        return insert_data(object_name, new_data=data)

    '''
    NAME
        insert_new_user_api - Flask route for API to register a new user
    SYNOPSIS
        insert_new_user_api()
    DESCRIPTION
        API only accepting POST requests
        Allows authenticated users to add another user to the system
            Another user can now access the system
        Request body should be of the following format:
            {
                "email": "example@email.com",
                "name": "John Smith",
                "password": "1234",
                "is_admin": false
            }
    RETURNS
        If successful
            { "status": "success" }
        else
            { "status": "fail", "status_description": reason }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/19/2016
    '''
    @app.route("/api/user-management/create-user", methods=["POST"])
    @is_authenticated
    def insert_new_user_api():
        # convert POSTed data
        data = request.get_json(force=True)

        if not data.get("email"):
            return jsonify({"status": "fail", "status_description": "The new user's email address is missing."})

        data['hidden_from_ui'] = False

        users_data = select_data(object_name=USER_MANAGEMENT_OBJECT_NAME,
                                 where_data={},
                                 column_data=["email"],
                                 limit=0,
                                 offset=0)

        if any(data.get("email") == x.get("email") for x in users_data):
            print "Duplicate"
            return jsonify({"status": "fail", "status_description": "Each user's email address must be unique."})

        db_manager.create_task("insert", USER_MANAGEMENT_OBJECT_NAME, insert_data=data)

        return jsonify({"status": "success"})

    '''
    NAME
        delete_data_api - Flask route for API to delete data from a dynamic object
    SYNOPSIS
        delete_data_api(object_name)
            object_name     -> name of object to delete data from
    DESCRIPTION
        API only accepting POST requests
        Allows authenticated users to remove data from a dynamic object
            deletes rows from the object's table
        Request body should be of the following format (criteria for sql WHERE):
            {
                "_id": 2
            }
    RETURNS
        { "status": "success" }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/19/2016
    '''
    @app.route("/api/tracking/delete/<object_name>", methods=["POST"])
    @is_authenticated
    def delete_data_api(object_name):
        data = request.get_json(force=True)
        return delete_data(object_name, which_data=data)

    '''
    NAME
        delete_user_api - Flask route for API to delete a registered user from the system
    SYNOPSIS
        delete_user_api()
    DESCRIPTION
        API only accepting POST requests
        Allows authenticated users to remove access for a registered user
            deletes registered user from table
        Request body should be of the following format (criteria for sql WHERE):
            {
                "email": "example@email.com"
            }
    RETURNS
        { "status": "success" }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/19/2016
    '''
    @app.route("/api/user-management/delete-user", methods=["POST"])
    @is_authenticated
    def delete_user_api():
        data = request.get_json(force=True)

        if not data.get("email"):
            return jsonify({"status": "fail", "status_description": "Missing parameters to remove user"})

        db_manager.create_task("delete", USER_MANAGEMENT_OBJECT_NAME, where_data={"email": data.get("email")},
                               limit=0, offset=0)

        return jsonify({"status": "success"})

    '''
    NAME
        update_data_api - Flask route for API to update data for a dynamic object
    SYNOPSIS
        update_data_api(object_name)
            object_name     -> name of object to delete data from
    DESCRIPTION
        API only accepting POST requests
        Allows authenticated users to update rows for a specific object
        Request body should be of the following format:
            {
                "where": {
                    "_id": 1
                },
                "update": {
                    "name": "Duck"
                },
                "offset": 5 (default is 0),
                "limit": 2 (default is 0 - means no limit)
            }
    RETURNS
        { "status": "success" }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/19/2016
    '''
    @app.route("/api/tracking/update/<object_name>", methods=["POST"])
    @is_authenticated
    def update_data_api(object_name):
        data = request.get_json(force=True)
        return update_data(object_name, where_data=data.get("where", {}), updated_values=data.get("update"),
                           limit=data.get("limit", 0), offset=data.get("offset", 0))

    '''
    NAME
        select_data_api - Flask route for API to select data from a dynamic object
    SYNOPSIS
        select_data_api()
    DESCRIPTION
        API only accepting GET requests
        Allows authenticated users to select rows from a specific object
        Request body should be of the following format:
            {
                "object_name": "Login Events",
                "where_data": {
                    "_id": 1
                },
            }
    RETURNS
        { "status": "success" }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/19/2016
    '''
    @app.route("/api/tracking/select", methods=["GET"])
    @is_authenticated
    def select_data_api():
        object_name = request.args.get("object_name")
        where_data = request.args.get("where_data", {})

        column_data = request.args.get("column_data").split(",")
        column_data = map(lambda x: str(x), column_data)

        limit = request.args.get("limit", 0)
        offset = request.args.get("offset", 0)

        data_to_return = select_data(object_name=object_name,
                                     where_data=where_data,
                                     column_data=column_data,
                                     limit=limit,
                                     offset=offset)

        print data_to_return
        return jsonify(page_data=data_to_return)

    '''
    NAME
        select_graph_data_api - Flask route for API to select graph data from a dynamic object
    SYNOPSIS
        select_graph_data_api()
    DESCRIPTION
        API only accepting GET requests
        Allows authenticated users to select graph data from a specific object
        Graph data consists is the count of rows per some day.
        Request body should be of the following format:
            {
                "object_name": "Login Events"
            }
    RETURNS
        {
            "labels": [ "label1", "label2" ],
            "values": [ int_value1, int_value2 ]
        }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    '''
    @app.route("/api/dashboard/graph", methods=["GET"])
    @is_authenticated
    def select_graph_data_api():
        object_name = request.args.get("object_name")
        labels, values = select_graph_data(object_name)
        return jsonify({"labels": labels, "values": values})

    '''
    NAME
        select_all_users_emails - Flask route for API to select the email addresses of all registered users
    SYNOPSIS
        select_all_users_emails()
    DESCRIPTION
        API only accepting GET requests
        Allows authenticated users to select graph data from a specific object

        Retrieves a list of objects containing the email addresses of all registered users
            users that can access the UI of the system
    RETURNS
        [
            {
                "email": "example@email.com"
            }
        ]
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    '''
    @app.route("/api/user-management/all-users", methods=["GET"])
    @is_authenticated
    def select_all_users_emails():
        users_data = select_data(object_name=USER_MANAGEMENT_OBJECT_NAME,
                                 where_data={},
                                 column_data=["email"],
                                 limit=0,
                                 offset=0)

        return jsonify(users_data)

    ###########
    # Database Action Helper Functions
    ###########

    '''
    NAME
        insert_data - general function to insert some data into some object
    SYNOPSIS
        insert_data(object_name, new_data)
            object_name     -> name of dynamic object to insert to
            new_data        -> dictionary containing a new row to append to a table
    DESCRIPTION
        Creates a database task to insert some rows into some table

        This function is asyncronous
    RETURNS
        {
            "status": "success"
        }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    '''
    def insert_data(object_name, new_data):
        db_manager.create_task("insert", object_name, insert_data=new_data)
        return jsonify({"status": "success"})

    '''
    NAME
        delete_data - general function to delete some data from some object
    SYNOPSIS
        delete_data(object_name, which_data)
            object_name     -> name of dynamic object to delete from
            which_data      -> dictionary containing data to filter rows to delete
    DESCRIPTION
        Creates a database task to delete some rows from some table

        This function is asynchronous

        Can be selective by the which_data parameter. Similar to the sql 'WHERE'
    RETURNS
        {
            "status": "success"
        }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    '''
    def delete_data(object_name, which_data):
        db_manager.create_task("delete", object_name, where_data=which_data)
        return jsonify({"status": "success"})

    '''
    NAME
        update_data - general function to update some data for some object
    SYNOPSIS
        update_data(object_name, where_data, updated_values, limit, offset)
            object_name     -> name of dynamic object to update
            where_data      -> dictionary containing data to filter rows to update
            updated_values  -> dictionary containing data to update with
            limit           -> limit on the number of rows to update - 0 means no limit
            offset          -> number of row to start SQL with - typically should be 0
    DESCRIPTION
        Creates a database task to update some rows for some table

        This function is asynchronous

        Can be selective by the where_data parameter. Similar to the sql 'WHERE'
    RETURNS
        {
            "status": "success"
        }
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    '''
    def update_data(object_name, where_data, updated_values, limit, offset):
        db_manager.create_task("update", object_name, where_data=where_data, update_data=updated_values, limit=limit)
        return jsonify({"status": "success"})

    '''
    NAME
        select_data - general function to select some data from some object
    SYNOPSIS
        select_data(object_name, where_data, column_data, limit, offset, order_by, sort_order)
            object_name     -> name of dynamic object to select from
            where_data      -> dictionary containing data to filter rows to select (default is None/{})
            column_data     -> list specifying rows to select (default is None/[])
            limit           -> limit on the number of rows to update - 0 means no limit (default is 0)
            offset          -> number of row to start SQL with - typically should be 0 (default is 0)
            order_by        -> string column in the table to order results by (default is "_id")
            sort_order      -> True = ascending, False = descending
    DESCRIPTION
        Performs a database task to update some rows for some table

        This function is synchronous

        Can be selective by the where_data parameter. Similar to the sql 'WHERE'
    RETURNS
        [
            {
                row 1
            },
            {
                row 2
            }
        ]
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    '''
    def select_data(object_name, where_data=None, column_data=None, limit=0, offset=0, order_by="_id", sort_order=True):
        if where_data is None:
            where_data = {}
        if column_data is None:
            column_data = []
        return db_manager.pool.action.create_new_action(DBTask(action_type="select",
                                                               object_name=object_name,
                                                               where_data=where_data,
                                                               select_data=column_data,
                                                               limit=limit,
                                                               offset=offset,
                                                               order_by=order_by,
                                                               sort_order=sort_order))

    ###########
    # General Helper Functions
    ###########

    '''
    NAME
        select_graph_data - general helper function to select graph data
    SYNOPSIS
        select_graph_data(object_name)
            object_name     -> name of dynamic object to insert to
    DESCRIPTION
        Retrieves the dates and count/date from some object
    RETURNS
        labels      -> list of dates
        values      -> list of values/counts corresponding to the dates
    AUTHOR
        Yoav Nathaniel
    DATE
        4/24/2016
    '''
    def select_graph_data(object_name):
        first_object_data = select_data(object_name=object_name,
                                        column_data=["_timestamp_created"],
                                        order_by="_timestamp_created",
                                        sort_order=True)
        first_object_data = map(lambda one_row: one_row["_timestamp_created"].strftime("%Y-%m-%d"), first_object_data)
        c = Counter(first_object_data)
        labels = sorted(list(set(first_object_data)))
        values = map(lambda one_label: c[one_label], labels)
        return labels, values

    app.run(host='0.0.0.0', port=5010, debug=True)


    return db_manager
