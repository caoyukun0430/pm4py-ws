import sqlite3

from pm4pyws.configuration import Configuration
from pm4pyws.handlers.parquet.parquet import ParquetHandler
from pm4pyws.handlers.xes.xes import XesHandler
from pm4pyws.log_manager.interface.log_manager import LogHandler

import time


class BasicLogSessionHandler(LogHandler):
    def __init__(self, ex):
        # path to the database
        self.database_path = "event_logs.db"

        self.handlers = {}
        self.session_handlers = {}

        self.objects_memory = {}
        self.objects_timestamp = {}

        self.user_management = None

        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()
        curs_logs.execute("DELETE FROM EVENT_LOGS WHERE IS_TEMPORARY = 1")
        conn_logs.commit()

        LogHandler.__init__(self, ex)

    def set_user_management(self, um):
        """
        Sets the user management

        Parameters
        ------------
        um
            User management
        """
        self.user_management = um

    def remove_unneeded_sessions(self, all_sessions):
        """
        Remove expired sessions

        Parameters
        ------------
        all_sessions
            All valid sessions
        """
        shk = list(self.session_handlers.keys())
        for session in shk:
            if session not in all_sessions and (not str(session) == "null" and not str(session) == "None"):
                print("removing handler for " + str(session))
                del self.session_handlers[session]

    def get_handlers(self):
        """
        Gets the current set of handlers

        Returns
        -----------
        handlers
            Handlers
        """
        return self.handlers

    def get_handler_for_process_and_session(self, process, session):
        """
        Gets an handler for a given process and session

        Parameters
        -------------
        process
            Process
        session
            Session

        Returns
        -------------
        handler
            Handler
        """
        if process in self.handlers:
            if session not in self.session_handlers:
                self.session_handlers[session] = {}
            if process not in self.session_handlers[session]:
                self.session_handlers[session][process] = self.handlers[process]
            # print(LogsHandlers.session_handlers[session][process].filters_chain)
            return self.session_handlers[session][process]
        return None

    def set_handler_for_process_and_session(self, process, session, handler):
        """
        Sets the handler for the current process and session

        Parameters
        -------------
        process
            Process
        session
            Session
        handler
            Handler
        """
        if process in self.handlers:
            if session not in self.session_handlers:
                self.session_handlers[session] = {}
            self.session_handlers[session][process] = handler

    def check_is_admin(self, user):
        """
        Checks if the user is an administrator

        Parameters
        -------------
        user
            User

        Returns
        -------------
        boolean
            Boolean value
        """
        if Configuration.enable_session:
            conn_logs = sqlite3.connect(self.database_path)
            curs_logs = conn_logs.cursor()
            curs_logs.execute("SELECT USER_ID FROM ADMINS WHERE USER_ID = ? AND USER_ID = ?", (user, user))
            results = curs_logs.fetchone()
            if results is not None:
                return True
            return False
        return True

    def manage_upload(self, user, basename, filepath, is_temporary=False):
        """
        Manages an event log that is uploaded

        Parameters
        ------------
        user
            Current user
        basename
            Name of the log
        filepath
            Log path
        """

        if filepath.endswith(".parquet"):
            self.handlers[basename] = ParquetHandler()
            self.handlers[basename].build_from_path(filepath)
        elif filepath.endswith(".csv"):
            self.handlers[basename] = ParquetHandler()
            self.handlers[basename].build_from_csv(filepath)
        else:
            self.handlers[basename] = XesHandler()
            self.handlers[basename].build_from_path(filepath)
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()
        if is_temporary:
            curs_logs.execute("INSERT INTO EVENT_LOGS VALUES (?,?,1,0,1)", (basename, filepath))
        else:
            curs_logs.execute("INSERT INTO EVENT_LOGS VALUES (?,?,0,1,1)", (basename, filepath))
        curs_logs.execute("INSERT INTO USER_LOG_VISIBILITY VALUES (?,?)", (user, basename))
        curs_logs.execute("INSERT INTO USER_LOG_DOWNLOADABLE VALUES (?,?)", (user, basename))
        curs_logs.execute("INSERT INTO USER_LOG_REMOVAL VALUES (?,?)", (user, basename))
        conn_logs.commit()
        conn_logs.close()

    def check_user_log_visibility(self, user, process):
        """
        Checks if the user has visibility on the given process

        Parameters
        -------------
        user
            User
        process
            Process
        """
        if Configuration.enable_session:
            conn_logs = sqlite3.connect(self.database_path)
            curs_logs = conn_logs.cursor()
            curs_logs.execute("SELECT USER_ID FROM USER_LOG_VISIBILITY WHERE USER_ID = ? AND LOG_NAME = ?",
                              (user, process))
            results = curs_logs.fetchone()
            if results is not None:
                return True
            return self.check_is_admin(user)
        return True

    def check_user_enabled_upload(self, user):
        """
        Checks if the user is enabled to upload a log

        Parameters
        ------------
        user
            User

        Returns
        ------------
        boolean
            Boolean value
        """
        if Configuration.enable_session:
            conn_logs = sqlite3.connect(self.database_path)
            curs_logs = conn_logs.cursor()
            curs_logs.execute("SELECT USER_ID FROM USER_UPLOADABLE WHERE USER_ID = ? AND USER_ID = ?", (user, user))
            results = curs_logs.fetchone()
            if results is not None:
                return True
            return self.check_is_admin(user)
        return True

    def check_user_enabled_download(self, user, process):
        """
        Checks if the user is enabled to download a log

        Parameters
        ------------
        user
            User
        process
            Process

        Returns
        ------------
        boolean
            Boolean value
        """
        if Configuration.enable_session:
            conn_logs = sqlite3.connect(self.database_path)
            curs_logs = conn_logs.cursor()
            curs_logs.execute("SELECT USER_ID FROM USER_LOG_DOWNLOADABLE WHERE USER_ID = ? AND LOG_NAME = ?",
                              (user, process))
            results = curs_logs.fetchone()
            if results is not None:
                return True
            return self.check_is_admin(user)
        return True

    def load_log_static(self, log_name, file_path, parameters=None):
        """
        Loads an event log inside the known handlers

        Parameters
        ------------
        log_name
            Log name
        file_path
            Full path (in the services machine) to the log
        parameters
            Possible parameters
        """
        if log_name not in self.handlers:
            if file_path.endswith(".parquet"):
                self.handlers[log_name] = ParquetHandler()
                self.handlers[log_name].build_from_path(file_path, parameters=parameters)
            elif file_path.endswith(".csv"):
                self.handlers[log_name] = ParquetHandler()
                self.handlers[log_name].build_from_csv(file_path, parameters=parameters)
            elif file_path.endswith(".xes") or file_path.endswith(".xes.gz"):
                self.handlers[log_name] = XesHandler()
                self.handlers[log_name].build_from_path(file_path, parameters=parameters)

    def save_object_memory(self, key, value):
        """
        Saves an object into the objects memory

        Parameters
        ------------
        key
            Key
        value
            Value
        """
        self.objects_memory[key] = value
        self.objects_timestamp[key] = time.time()

    def get_object_memory(self, key):
        """
        Gets an object from the objects memory

        Parameters
        ------------
        key
            Key
        value
            Value
        """
        if key in self.objects_memory:
            return self.objects_memory[key]
        return None

    def get_user_eventlog_vis_down_remov(self):
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        users = self.user_management.get_all_users()

        admin_list = []
        user_log_vis = {}
        all_logs = set()

        cur = curs_logs.execute("SELECT LOG_NAME, LOG_NAME FROM EVENT_LOGS")
        for res in cur.fetchall():
            all_logs.add(str(res[0]))

        cur = curs_logs.execute("SELECT USER_ID, USER_ID FROM ADMINS")
        for res in cur.fetchall():
            admin_list.append(str(res[0]))

        for user in users:
            if user not in user_log_vis:
                user_log_vis[user] = {}

        cur = curs_logs.execute("SELECT USER_ID, USER_ID FROM OTHER_USERS")
        for res in cur.fetchall():
            user = str(res[0])
            if user not in user_log_vis:
                user_log_vis[user] = {}

        cur = curs_logs.execute("SELECT USER_ID, LOG_NAME FROM USER_LOG_VISIBILITY")
        for res in cur.fetchall():
            user = str(res[0])
            log = str(res[1])
            if user not in user_log_vis:
                user_log_vis[user] = {}
            if log not in user_log_vis[user]:
                user_log_vis[user][log] = {"visibility": False, "downloadable": False, "removable": False}
            user_log_vis[user][log]["visibility"] = True

        cur = curs_logs.execute("SELECT USER_ID, LOG_NAME FROM USER_LOG_DOWNLOADABLE")
        for res in cur.fetchall():
            user = str(res[0])
            log = str(res[1])
            if user not in user_log_vis:
                user_log_vis[user] = {}
            if log not in user_log_vis[user]:
                user_log_vis[user][log] = {"visibility": False, "downloadable": False, "removable": False}
            user_log_vis[user][log]["downloadable"] = True

        cur = curs_logs.execute("SELECT USER_ID, LOG_NAME FROM USER_LOG_REMOVAL")
        for res in cur.fetchall():
            user = str(res[0])
            log = str(res[1])
            if user not in user_log_vis:
                user_log_vis[user] = {}
            if log not in user_log_vis[user]:
                user_log_vis[user][log] = {"visibility": False, "downloadable": False, "removable": False}
            user_log_vis[user][log]["removable"] = True

        # remove admins
        for adm in admin_list:
            if adm in user_log_vis:
                del user_log_vis[adm]

        for user in user_log_vis:
            for log in all_logs:
                if log not in user_log_vis[user]:
                    user_log_vis[user][log] = {"visibility": False, "downloadable": False, "removable": False}

        sorted_users = sorted(list(user_log_vis.keys()))
        sorted_logs = sorted(list(all_logs))

        conn_logs.close()

        return sorted_users, sorted_logs, user_log_vis

    def add_user_eventlog_visibility(self, user, event_log):
        print("start add_user_eventlog_visibility "+str(user)+" "+str(event_log))
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        curs_logs.execute("DELETE FROM USER_LOG_VISIBILITY WHERE USER_ID = ? AND LOG_NAME = ?", (user, event_log))
        curs_logs.execute("INSERT INTO USER_LOG_VISIBILITY VALUES (?,?)", (user, event_log))

        conn_logs.commit()
        conn_logs.close()

        print("end add_user_eventlog_visibility "+str(user)+" "+str(event_log))


    def remove_user_eventlog_visibility(self, user, event_log):
        print("start remove_user_eventlog_visibility "+str(user)+" "+str(event_log))
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        curs_logs.execute("DELETE FROM USER_LOG_VISIBILITY WHERE USER_ID = ? AND LOG_NAME = ?", (user, event_log))

        conn_logs.commit()
        conn_logs.close()
        print("end remove_user_eventlog_visibility "+str(user)+" "+str(event_log))

    def add_user_eventlog_downloadable(self, user, event_log):
        print("start add_user_eventlog_downloadable "+str(user)+" "+str(event_log))
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        curs_logs.execute("DELETE FROM USER_LOG_DOWNLOADABLE WHERE USER_ID = ? AND LOG_NAME = ?", (user, event_log))
        curs_logs.execute("INSERT INTO USER_LOG_DOWNLOADABLE VALUES (?,?)", (user, event_log))

        conn_logs.commit()
        conn_logs.close()

        print("end add_user_eventlog_downloadable "+str(user)+" "+str(event_log))

    def remove_user_eventlog_downloadable(self, user, event_log):
        print("start remove_user_eventlog_downloadable "+str(user)+" "+str(event_log))
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        curs_logs.execute("DELETE FROM USER_LOG_DOWNLOADABLE WHERE USER_ID = ? AND LOG_NAME = ?", (user, event_log))

        conn_logs.commit()
        conn_logs.close()

        print("end remove_user_eventlog_downloadable "+str(user)+" "+str(event_log))

    def add_user_eventlog_removable(self, user, event_log):
        print("start add_user_eventlog_removable "+str(user)+" "+str(event_log))
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        curs_logs.execute("DELETE FROM USER_LOG_REMOVAL WHERE USER_ID = ? AND LOG_NAME = ?", (user, event_log))
        curs_logs.execute("INSERT INTO USER_LOG_REMOVAL VALUES (?,?)", (user, event_log))

        conn_logs.commit()
        conn_logs.close()

        print("end add_user_eventlog_removable "+str(user)+" "+str(event_log))

    def remove_user_eventlog_removable(self, user, event_log):
        print("start remove_user_eventlog_removable "+str(user)+" "+str(event_log))
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        curs_logs.execute("DELETE FROM USER_LOG_REMOVAL WHERE USER_ID = ? AND LOG_NAME = ?", (user, event_log))

        conn_logs.commit()
        conn_logs.close()

        print("end remove_user_eventlog_removable "+str(user)+" "+str(event_log))

    def check_log_is_removable(self, log):
        res = False
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        curs_logs.execute("SELECT * FROM EVENT_LOGS WHERE LOG_NAME = ? AND LOG_NAME = ? AND CAN_REMOVED = 1",(log, log))

        cur = curs_logs.fetchall()

        if cur is not None:
            for r in cur:
                res = True
                break

        conn_logs.commit()
        conn_logs.close()

        return res

    def can_delete(self, user, log):
        res = False
        is_admin = self.check_is_admin(user)
        is_removable = self.check_log_is_removable(log)

        if not is_removable:
            return False

        if is_admin:
            res = True

        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        curs_logs.execute("SELECT * FROM USER_LOG_REMOVAL WHERE USER_ID = ? AND LOG_NAME = ?", (user, log))

        cur = curs_logs.fetchall()

        if cur is not None:
            for r in cur:
                res = True
                break

        conn_logs.commit()
        conn_logs.close()

        return res

    def delete_log(self, log):
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()

        curs_logs.execute("DELETE FROM EVENT_LOGS WHERE LOG_NAME = ? AND LOG_NAME = ?", (log,log))
        curs_logs.execute("DELETE FROM USER_LOG_VISIBILITY WHERE LOG_NAME = ? AND LOG_NAME = ?", (log,log))
        curs_logs.execute("DELETE FROM USER_LOG_REMOVAL WHERE LOG_NAME = ? AND LOG_NAME = ?", (log,log))
        curs_logs.execute("DELETE FROM USER_LOG_DOWNLOADABLE WHERE LOG_NAME = ? AND LOG_NAME = ?", (log,log))

        conn_logs.commit()
        conn_logs.close()

        del self.handlers[log]
        for session in self.session_handlers:
            if log in self.session_handlers[session]:
                del self.session_handlers[session][log]

