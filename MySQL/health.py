import mysql.connector
import subprocess
from platform import system as system_name  # Returns the system/OS name
from subprocess import call as system_call  # Execute a shell command

from Utilities.utility import log_warn, log_info, log_error


def pinghost(host):
    try:
        output = str(subprocess.Popen(["ping.exe", host], stdout=subprocess.PIPE).communicate()[0])
        if 'unreachable' in output:
            log_error('!!!!!' + host + ' is unreachable!!!!!')
            return False
        else:
            log_info(host + ' is online')
            return True
    except Exception as error:
        log_warn('Current Machine is not running Windows-based OS: ' + str(error))
        # Ping command count option as function of OS
        param = '-n' if system_name().lower() == 'windows' else '-c'
        # Building the command. Ex: "ping -c 1 phlamtecdb-a"
        command = ['ping', param, '1', host]
        # Pinging
        if system_call(command) == 0:
            log_info(host + ' is online')
            return True
        else:
            log_error('!!!!!' + host + ' is OFFLINE!!!!!')
            return False


def healthcheck(host, port, instance_name, user, password):
    try:
        mysql_connection = mysql.connector.connect(host=host, port=port, user=user, password=password,
                                                   connection_timeout=10)
        mysql_connection.is_connected()
        log_info(host + ' ' + instance_name + ' INSTANCE, IS UP')
        return 0
    except Exception as error:
        log_error('!!!!!' + host + ' ' + instance_name + ' INSTANCE, IS DOWN!!!!!:\t' + str(error))

        return -1
