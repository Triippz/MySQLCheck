import smtplib
from email.message import EmailMessage
from Utilities.utility import log_info, log_error


def sendnotification(config, subject):
    try:
        distro_list = config['distro_list']

        msg = EmailMessage()
        msg.set_content(subject)
        msg['Subject'] = subject
        msg['From'] = config['smtp_info']['from']
        msg['To'] = ", ".join(distro_list)

        s = smtplib.SMTP(config['smtp_info']['host'], config['smtp_info']['port'])
        s.send_message(msg)
        s.quit()

        log_info('Notification Sent')
    except Exception as error:
        log_error('Error sending notification!: ' + str(error))
    finally:
        return


def sendnotification_replication_errors_fixed(config, body):
    try:
        distro_list = config['distro_list']

        msg = EmailMessage()
        msg.set_content('Error in replication due to statement:\n\n' + body)
        msg['Subject'] = 'Replication Error(s) on host: ' + config['smtp_info']['host'] + ': RESOLVED'
        msg['From'] = config['smtp_info']['from']
        msg['To'] = ", ".join(distro_list)

        s = smtplib.SMTP(config['smtp_info']['host'], config['smtp_info']['port'])
        s.send_message(msg)
        s.quit()

        log_info('Notification Sent')
    except Exception as error:
        log_error('Error sending notification!: ' + str(error))
    finally:
        return


def sendnotification_replication_errors_nfixed(config, body):
    try:
        distro_list = config['distro_list']

        msg = EmailMessage()
        msg.set_content('Error in replication due to statement:\n\n' + body)
        msg['Subject'] = 'Replication Error(s) on host: ' + config['smtp_info']['host'] + ': Unable to Resolve'
        msg['From'] = config['smtp_info']['from']
        msg['To'] = ", ".join(distro_list)

        s = smtplib.SMTP(config['smtp_info']['host'], config['smtp_info']['port'])
        s.send_message(msg)
        s.quit()

        log_info('Notification Sent')
    except Exception as error:
        log_error('Error sending notification!: ' + str(error))
    finally:
        return
