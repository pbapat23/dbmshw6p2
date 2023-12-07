from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
from prettytable import PrettyTable
import re

'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    """
    TODO: Part 1
    """
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    print(username)
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    if not is_strong_password(password):
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error_:", e)
    finally:
        cm.close_connection()
    return False


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    if not is_strong_password(password):
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def is_strong_password(password):
    if len(password) < 8:
        print("Password must be at least 8 characters")
        return False

    u = False
    l = False

    for char in password:
        if char.isupper():
            u = True
        elif char.islower():
            l = True

    if u is True and l is True:
        pass
    else:
        print("Password must have both uppercase and lowercase letters.")
        return False

    if not any(char.isdigit() for char in password):
        print("Password must have at least one digit.")
        return False

    if not any(char in '!@#?' for char in password):
        print("Password must include at least one special character from !, @, #, ?")
        return False

    return True



def login_patient(tokens):
    """
    TODO: Part 1
    """
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    """
    TODO: Part 2
    """

    global current_patient
    global current_caregiver

    if len(tokens) != 4:
        print("Please try again!")
        return

    if current_patient is None and current_caregiver is None:
        print("Please login first!")
        return

    month = int(tokens[1])
    day = int(tokens[2])
    year = int(tokens[3])

    try:
        date = datetime.datetime(year, month, day)
        query1 = "SELECT C.Username FROM Caregivers C, Availabilities A WHERE C.Username = A.Username AND A.Time = (%d) ORDER BY C.Username"
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        cursor.execute(query1, date)

        temp = []
        table1 = PrettyTable(['Caregivers'])
        for i in cursor:
            list__ = [str(i[0])]
            temp = list__
            table1.add_row(list__)

        if len(temp) == 0:
            print("No caregivers available on that date!")
            return
        print(table1)

    except:
        print("Please try again!")
        return

    finally:
        cm.close_connection()

    try:
        query2 = "SELECT name, doses FROM Vaccines"
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        cursor.execute(query2)

        table2 = PrettyTable(['Vaccine', 'Doses'])
        for i in cursor:
            list_ = [str(i[0]), str(i[1])]
            table2.add_row(list_)
        print(table2)

    except Exception as e:
        # print(e)
        print("Please try again!")
        return

    finally:
        cm.close_connection()


def reserve(tokens):
    """
    TODO: Part 2
    """
    global current_patient
    if current_patient is None:
        print("Please login as a patient!")
        return

    if len(tokens) != 5:
        print("Please try again!")
        return

    month = int(tokens[1])
    day = int(tokens[2])
    year = int(tokens[3])

    vaccine_name = tokens[4]

    date = datetime.datetime(year, month, day)

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    query1 = "SELECT Username FROM Availabilities WHERE Time = (%s) ORDER BY Username"
    try:
        cursor.execute(query1, date)
        result1 = cursor.fetchone()
    except:
        print("Please try again!")
        raise
    finally:
        cm.close_connection()

    if result1 is None:
        print("No Caregiver is available!")
        return


    query2 = "SELECT Name, Doses FROM Vaccines WHERE Name = (%s)"

    try:
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        cursor.execute(query2, vaccine_name)
        result2 = cursor.fetchone()
    except:
        print("Please try again!")
        return
    finally:
        cm.close_connection()

    if result2 is None:
        print("That Vaccine is currently unavailable! Please choose a different one.")
        return

    elif result2[1] == 0:
        print("Not enough available doses!")
        return

    try:
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM Appointments")
        current_max = cursor.fetchone()
        if current_max[0] is None:
            a_id = 1
        else:
            a_id = current_max[0] + 1
    except pymssql.Error as e:
        # print(e)
        print("Error occurred when generating appointment id")
        raise
    finally:
        cm.close_connection()

    print("Appointment ID:", a_id, "Caregiver Username:", result1[0])

    try:
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        args = (a_id, date, result1[0], current_patient.username, result2[0])
        # print(result2)
        cursor.execute("INSERT INTO Appointments (id, Time, caregiver, patient, vaccine) VALUES (%s, %s, %s, %s, %s)",
                       args)
        conn.commit()
    except Exception as e:
        # print("%%%%%%%%%%")
        print(e)
        print("Please try again!")
        raise
    finally:
        cm.close_connection()

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM Availabilities WHERE Time = (%d) AND Username = (%s)", (date, result1[0]))
        conn.commit()
    except Exception as e:
        # print('-------')
        print(e)
        print("Please try again!")
        raise
    finally:
        cm.close_connection()

    try:
        v_obj = Vaccine(vaccine_name, 0)
        v_obj.get()
        v_obj.decrease_available_doses(1)
    except Exception as e:
        # print('::::::')
        # print(e)
        print("Please try again!")
        quit()
    finally:
        cm.close_connection()


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    if len(tokens) != 2:
        print("Please try again!")
        return

    global current_patient
    global current_caregiver

    if current_patient is None and current_caregiver is None:
        print("Please login first!")
        return

    if current_patient:
        try:
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Appointments WHERE id = (%d)", tokens[1])
            result = cursor.fetchone()
            if result is None:
                print('You do not have an appointment with that appointment id')
                return
            elif result[3] != current_patient.username:
                print('You are not allowed to delete an appointment that isnt yours :))')
                return
            else:
                cg = result[2]
                date = result[1]
                vaccine_name = result[4]
                conn.commit()
        except Exception as e:
            # print('-------')
            # print(e)
            print("Please try again!")
            raise
        finally:
            cm.close_connection()

        try:
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Appointments WHERE id = (%d)", tokens[1])
            conn.commit()
        except Exception as e:
            # print('-------')
            # print(e)
            print("Please try again!")
            # Rolling back
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO FROM Appointments (%s)", result)
            raise
        finally:
            cm.close_connection()

        try:
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Availabilities VALUES (%s, %s)", (date, cg))
            conn.commit()
        except Exception as e:
            # print('-------')
            # print(e)
            print("Please try again!")
            # Rolling back
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO FROM Appointments (%s)", result)
            raise
        finally:
            cm.close_connection()

        try:
            v_obj = Vaccine(vaccine_name, 0)
            v_obj.get()
            v_obj.increase_available_doses(1)
        except Exception as e:
            # print('::::::')
            # print(e)
            print("Please try again!")
            # Rolling back
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO FROM Appointments (%s)", result)
            quit()
        finally:
            cm.close_connection()
            print("Done!")

    else:
        try:
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Appointments WHERE id = (%d)", tokens[1])
            result = cursor.fetchone()
            if result is None:
                print('You do not have an appointment with that appointment id')
                return
            elif result[2] != current_caregiver.username:
                print('You are not allowed to delete an appointment that isnt yours :))')
                return
            else:
                cg = result[2]
                date = result[1]
                vaccine_name = result[4]
                conn.commit()
        except Exception as e:
            # print('-------')
            # print(e)
            print("Please try again!")
            raise
        finally:
            cm.close_connection()

        try:
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Appointments WHERE id = (%d)", tokens[1])
            conn.commit()
        except Exception as e:
            # print('jbjkbjknj')
            # print(e)
            print("Please try again!")
            raise
        finally:
            cm.close_connection()

        try:
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Availabilities VALUES (%s, %s)", (date, cg))
            conn.commit()
        except Exception as e:
            # print('-------')
            # print(e)
            print("Please try again!")
            #Rolling back
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO FROM Appointments (%s)", result)
            raise
        finally:
            cm.close_connection()

        try:
            v_obj = Vaccine(vaccine_name, 0)
            v_obj.get()
            v_obj.increase_available_doses(1)
        except Exception as e:
            # print('::::::')
            # print(e)
            print("Please try again!")
            # Rolling back
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO FROM Appointments (%s)", result)
            quit()
        finally:
            print("Done!")
            cm.close_connection()


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    '''
    TODO: Part 2
    '''
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    if len(tokens) != 1:
        print("Please try again!")
        return

    try:
        if current_caregiver:
            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT id, patient, vaccine, time FROM Appointments WHERE caregiver = (%s) ORDER BY id", current_caregiver.username)
                table1 = PrettyTable(['Appointment ID', 'Patient Name', 'Vaccine', 'time'])
                for i in cursor:
                    list_ = [str(i[0]), str(i[1]), str(i[2]), str(i[3])]
                    table1.add_row(list_)
                print(table1)
            except:
                print("Please try again!")
                raise
            finally:
                cm.close_connection()
        else:
            if current_patient:
                cm = ConnectionManager()
                conn = cm.create_connection()
                cursor = conn.cursor()

                try:
                    cursor.execute("SELECT id, caregiver, vaccine, time FROM Appointments WHERE patient = (%s) ORDER BY id", current_patient.username)

                    table1 = PrettyTable(['Appointment ID', 'Caregiver Name', 'Vaccine', 'Time'])
                    for i in cursor:
                        list_ = [str(i[0]), str(i[1]), str(i[2]), str(i[3])]
                        table1.add_row(list_)
                    print(table1)

                except Exception as e:
                    print("Please try again!")
                    raise
                finally:
                    cm.close_connection()

    except:
        print("Please try again!")
        return


def logout(tokens):
    """
    TODO: Part 2
    """
    if len(tokens) != 1:
        print("Please try again!")
        return

    global current_caregiver
    global current_patient

    if current_caregiver == None and current_patient == None:
        print("Please login first")
        return
    else:
        current_caregiver = None
        current_patient = None
        print("Successfully logged out!")

def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    #I have explicitly asked for MM, DD, YYYY seperately to provide a better, error-free user experience. Otherwise, Users may assume different date formats!
    print("> search_caregiver_schedule <MM> <DD> <YYYY>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <MM> <DD> <YYYY> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
