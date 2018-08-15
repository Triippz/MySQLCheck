import logging
import datetime


def build_error_report (error_dict, total_errors, is_resolved):
    report_str = 'Error Report:\n\n'
    for error in error_dict:
        report_str += 'Error Code: ' + error + '\tDetails: ' + error.get(error) + '\n'

    report_str += '\nTotal Errors: ' + str(total_errors)
    report_str += '\nReplication Hangup Resolved: ' + str(is_resolved)

    return report_str


def log_error (message):
    print('ERROR:' + datetime.datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S %p:\t' + message))
    logging.error(datetime.datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S %p:\t' + message))


def log_warn (message):
    print('WARNING:' + datetime.datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S %p:\t' + message))
    logging.warning(datetime.datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S %p:\t' + message))


def log_info (message):
    print('INFO:' + datetime.datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S %p:\t' + message))
    logging.info(datetime.datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S %p:\t' + message))


def log_debug (message):
    print('DEBUG:' + datetime.datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S %p:\t' + message))
    logging.debug(datetime.datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S %p:\t' + message))
