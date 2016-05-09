import ActMonitor.server_application.views

if __name__ == "__main__":
    db_manager = ActMonitor.server_application.views.start_backend()
    ActMonitor.server_application.views.stop_backend(db_manager)


    '''
    from time import sleep
    with db_manager:



        object_name = "students"
        api_url = "students-api-12345"
        object_properties = [
            {
                "name": "student_name",
                "type": String
            },
            {
                "name": "in_school",
                "type": Boolean
            }
        ]

        data_to_insert = [
            {
                "student_name": "Yoav",
                "in_school": True
            },
            {
                "student_name": "Noam",
                "in_school": False
            }
        ]

        data_to_insert2 = {
            "student_name": "Ron",
            "in_school": True
        }

        data_to_delete = {
            "in_school": True
        }

        data_to_update = {
            "in_school": True
        }
        values_to_update = {
            "student_name": "Ma Kore"
        }

        data_to_select = {
            "in_school": True
        }
        columns_to_retrieve = [
            "student_name"
        ]
    '''
    '''
        create_api(api_url, object_name, object_properties)

        insert_data(object_name, data_to_insert)
        insert_data(object_name, data_to_insert2)
        delete_data(object_name, data_to_delete)
        update_data(object_name, data_to_update, values_to_update, limit=1)
        selected_data = select_data(object_name, data_to_select, columns_to_retrieve)
        print "#########"
        print selected_data
        print "#########"
        sleep(30)

        delete_api(object_name)
    '''