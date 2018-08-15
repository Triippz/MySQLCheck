import yaml
import logging
import datetime
import os

from MySQL.health import healthcheck, pinghost
from MySQL.replication import ReplicationChecker
from Notifier.notify import sendnotification
from Utilities.utility import log_info, log_debug

if __name__ == '__main__':
    directory = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    config = yaml.load(
        (open(os.path.join(directory, 'config.yml'), 'r').read()))

    logging.basicConfig(filename=os.path.join(directory, 'replication.log'),
                        level=logging.DEBUG)
    log_info('Monitor Started')

    # Get all the instance names and their port numbers
    log_debug('Gathering instance names from config')
    instances = config['instances']
    ports = dict()
    for instance in instances:
        ports[instance] = config['mysql'][instance]

    # !Check the Instance Status'
    for port in ports:
        log_info('Performing health check on instance: ' + str(port).upper())
        status = healthcheck(config['mysql']['host'], ports.get(port), port,
                             config['mysql']['user'], config['mysql']['password'])
        if status == -1:
            sendnotification(config, datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S %p') + ':\t!!!!!' + config['mysql']['host'] + ':' + str(port).upper() +
                             ' IS DOWN!!!!!')
        else:
            # Lets make sure the Secondary Server is online
            # if its not, we will recieve nothing back, since
            # The slave will be offline
            log_info('Checking if secondary host is online')
            server_status = pinghost(config['mysql']['host_secondary'])
            if not server_status:
                sendnotification(config, datetime.datetime.now().strftime(
                     '%Y-%m-%d %H:%M:%S %p') + ':!!!!!' + config['mysql']['host_secondary'] + ' IS DOWN!!!!!')

            # If the Server is ONLINE, let's check the actual instance to make sure its up
            else:
                log_info('Perfrmoing health change on secondary host instance:' + str(port).upper())
                status = healthcheck(config['mysql']['host_secondary'], ports.get(port), port,
                                     config['mysql']['user'], config['mysql']['password'])
                if status == -1:
                    sendnotification(config, datetime.datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S %p') + ':!!!!!' + config['mysql']['host_secondary'] + ':' + str(port).upper() +
                                     ' IS DOWN!!!!!')
                else:
                    # !CHECK THE REPLICATION STATUS
                    log_info('Checking replication status for: ' + str(port).upper())

                    checker = ReplicationChecker(
                        project_directory=directory,
                        lag_interval=300,
                        lag_duration=1800,
                        user=config['mysql']['user'],
                        password=config['mysql']['password'],
                        config=config,
                        host=config['mysql']['host'],
                        port=ports.get(port)
                    )
                    checker.check_replication(config['server_type'])

    log_info('Monitor Complete')
