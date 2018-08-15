import mysql.connector
import datetime
import os
import time

from Notifier.notify import sendnotification_replication_errors_fixed, sendnotification_replication_errors_nfixed
from Utilities.utility import build_error_report, log_error, log_debug, log_warn, log_info


class ReplicationChecker(object):
    def __init__(self, project_directory, lag_interval, lag_duration, user,
                 password, config, host='local', port=3308):
        """
        A MySQL Replication Checker
        :param project_directory: The project directory path
        :param lag_interval: Lag interval in seconds
        :param lag_duration: Lag duration in seconds
        :param user: mysql user
        :param password: mysql password
        :param host: mysql host
        :param port: mysql port
        :return: None
        """
        self.project_directory = project_directory
        self.lag_interval = lag_interval
        self.lag_duration = lag_duration
        self.user = user
        self.password = password
        self.config = config
        self.host = host
        self.port = port
        self.notifiers = []
        self.messages = []

        self.LAG_LOCK = os.path.join(self.project_directory, 'lag.lock')
        self.WARNING_LOCK = os.path.join(self.project_directory, 'warning.lock')
        self.DANGER_LOCK = os.path.join(self.project_directory, 'danger.lock')

    def add_notifier(self, notifier):
        self.notifiers.append(notifier)

    def check_replication(self, server_type):
        if 'master' in server_type:
            self.check()

    def check(self):
        try:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )

            cursor = cnx.cursor()
            query = 'SHOW SLAVE STATUS;'

            something = cursor.execute(query)
            replication_status_row = cursor.fetchall()[0]
            last_error_no = replication_status_row[18]
            last_error = replication_status_row[19]
            seconds_behind_master = replication_status_row[32]
            slave_sql_running_state = replication_status_row[44]

            log_info('Last Error No: ' + str(last_error_no))
            log_info('Last Error: ' + str(last_error_no))
            log_info('Seconds behind master: ' + str(seconds_behind_master))
            log_info(
                'slave_sql_running_state: ' + str(slave_sql_running_state))

            if last_error_no != 0:
                self.raise_replication_error(last_error,
                                             slave_sql_running_state)
            elif seconds_behind_master >= self.lag_interval:
                self.track_lag(slave_sql_running_state, seconds_behind_master)
            else:
                self.confirm_normality()

        except Exception as error:
            self.raise_exception(error)

        if self.messages:
            self.trigger_notifications()

    def raise_replication_error(self, last_error, slave_sql_running_state):
        self.messages.append({
            'status': 'danger',
            'short_message': 'Replication Error',
            'long_message': last_error + 'Current state: %s'
                            % slave_sql_running_state,
            'time_string':
                datetime.datetime.now().isoformat()
        })

        self.write_lock('danger')

    def clear_replication_errors(self):
        stop_slave_query = 'STOP SLAVE;'
        skip_counter_query = 'set global sql_slave_skip_counter = 1;)'
        start_slave_query = 'START SLAVE;'
        slave_status_query = 'SHOW SLAVE STATUS;'
        total_errors = 0
        errors = dict()

        more_errors = True

        try:
            # Log in as the replication user
            log_info('Replication: Loggin in as Replication User')
            cnx = mysql.connector.connect(
                user=self.config['replication']['user'],
                password=self.config['replication']['password'],
                host=self.host,
                port=self.port
            )
            log_info('Replication: Successfully Logged in as Replication User')
        except Exception as error:
            log_error("Replication: Error logging in as Replication User on host: " + self.host + ': ' + str(error))
            sendnotification_replication_errors_nfixed(self.config, 'Potential Errors present in Replication.'
                                                                    ' Unable to resolve issue(s).')
        while more_errors:
            try:
                log_info('Replication: Performing \"Status\" on slave')
                # Get the status of the replication slave
                cursor = cnx.cursor()
                cursor.execute(slave_status_query)
                replication_status_row = cursor.fetchall()[0]
                replication_error_code = str(replication_status_row[18])
                replication_error_str = str(replication_status_row[19])

                # If there are errors, lets try to resolve them
                if int(replication_error_code) != 0:
                    log_error('Replication: Error detected: ' + replication_error_str)
                    errors[replication_error_code] = replication_error_str
                    total_errors = total_errors + 1

                    # lets skip the error and try to resolve the hang up
                    cursor.execute(stop_slave_query)
                    cursor.execute(skip_counter_query)
                    cursor.execute(start_slave_query)

                # Lets check for anymore errors that may be holding us up
                cursor.execute(slave_status_query)
                replication_status_row = cursor.fetchall()[0]
                replication_error_code = str(replication_status_row[18])
                if int(replication_error_code) == 0:
                    more_errors = False
                    log_info("Replication: No more errors detected")
                    sendnotification_replication_errors_fixed(self.config,
                                                              build_error_report(errors, total_errors, True),
                                                              replication_error_code)
            except Exception as error:
                self.raise_exception(error)
                log_error("Replication: Error preventing all replication issues to be resolve. "
                          "Some or none of these issues were resolved:\t" + error)
                sendnotification_replication_errors_nfixed(self.config, 'Potential Errors present in Replication.'
                                                                        ' Unable to resolve issue(s).')

    def track_lag(self, slave_sql_running_state, seconds_behind_master):
        log_debug('There is a lag of more than 300 seconds')
        if os.path.isfile(self.LAG_LOCK):
            if not os.path.isfile(self.WARNING_LOCK):
                with open(self.LAG_LOCK, 'r') as f:
                    timestamp = int(f.read())
                    current_timestamp = int(time.time())
                    difference = current_timestamp - timestamp
                    if difference >= self.lag_duration:
                        self.raise_lag_warning(slave_sql_running_state,
                                               seconds_behind_master)
                    else:
                        log_debug(
                            "Hasn't been lagging for more "
                            "than 5 minutes. Still Cool.")
        else:
            self.write_lock('lag')

    def raise_lag_warning(self, slave_sql_running_state, seconds_behind_master):
        self.messages.append({
            'status': 'warning',
            'short_message': 'Replication Lag',
            'long_message':
                'The replica is lagging more than %s seconds'
                'behind master for longer than %s seconds. Current state: %s. '
                'Current lag: %s seconds.'
                % (str(self.lag_interval), str(self.lag_duration),
                   slave_sql_running_state, seconds_behind_master),
            'time_string':
                datetime.datetime.now().isoformat()
        })

        self.write_lock('warning')
        log_warn('The lag has lasted longer than 5 minutes.')

    def confirm_normality(self):
        if os.path.isfile(self.DANGER_LOCK) or os.path.isfile(
                self.WARNING_LOCK):
            self.messages.append({
                'status': 'good',
                'short_message': 'Everything is back to normal',
                'long_message':
                    'Nothing to complain about.',
                'time_string':
                    datetime.datetime.now().isoformat()
            })

        self.clear_locks()
        log_info('Everything is OK!')

    def raise_exception(self, error):
        self.messages.append({
            'status': 'danger',
            'short_message': 'Exception',
            'long_message': str(error),
            'time_string': datetime.datetime.now().isoformat()
        })

        self.write_lock('danger')

    def clear_locks(self):
        if os.path.isfile(self.DANGER_LOCK):
            os.remove(self.DANGER_LOCK)
        if os.path.isfile(self.LAG_LOCK):
            os.remove(self.LAG_LOCK)
        if os.path.isfile(self.WARNING_LOCK):
            os.remove(self.WARNING_LOCK)

    def write_lock(self, status):
        file_path = os.path.join(self.project_directory, status + '.lock')
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as f:
                f.write(str(int(time.time())))

    def trigger_notifications(self):
        for notifier in self.notifiers:
            for message in self.messages:
                notifier.notify(message['status'], message['short_message'],
                                message['long_message'], message['time_string'])

        self.messages = []
