class TemplateDynamicObject(object):
    """
    NAME
        TemplateDynamicObject - a template class of a dynamic object
    VARIABLES
        variables for this class are dynamic - cannot be determined
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """

    """
    NAME
        __init__ - constructor to set the variables for this instance
    SYNOPSIS
        __init__(self, **kwargs)
            self        -> the instance of the class
            **kwargs    -> pythonic way to dynamically add named arguments to a function
    DESCRIPTION
        The constructor sets up the class variables

        Inserts the named arguments into the instance's dictionary
    RETURNS
        None
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            self.__dict__[name] = value

    """
    NAME
        __getattr__ - override default function to retrieve an object's attribute
    SYNOPSIS
        __getattr__(self, item)
            self    -> the instance of the class
            item    -> a string name of class attribute
    DESCRIPTION
        Overrides default __getattr__ function (all python objects have this)
        Gets the attribute directly from the instance's dictionary
    RETURNS
        value of the requested attribute
    AUTHOR
        Yoav Nathaniel
    DATE
        4/25/2016
    """
    def __getattr__(self, item):
        return self.__dict__[item]
