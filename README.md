# MySQLCheck

A Python project for monitoring Database Servers, MySQL Server Instances and Replication Slave Status'. If anytype of error/issue is found,
an email will be sent out to individuals on a distribution list. 

This project was developed for a specific system with 1-Master and 1-Slave, so you may need to tailor this to your specific
needs. If you don't need to, then the only thing you should ever have to change is the config file. An example has been provided.

This project was also designed to run as a "Windows Task", executed every 'n' number of minutes/seconds/hours/etc. on a Server
running Windows Server 2016, with MySQL 5.7 and 8.0 installed. You may experience issues if you use this for earlier versions, as I have not designed nor tested this for anything older that what is annotated.

The flow of this program is.

1. Load all the instances and their port number's (assuming the master and slave instances have the same ports)
2. Perform a health check of all the instances on the master (host-a)
3. Ensure the slave (secondary host) is online and you can communicate with it
4. Perform a health check of all the instances on the slave.
5. Ensure there are no errors hanging up the replication process for subsequent queries.
   If errors are present, the program will attempt to clear all of the errors, while logging
   specifically what each error was, with its error code.  Once all errors have been cleared,
   a report will be generated and emailed to everyone annotated on the distribution list. Logs will
   contain more specific information on each error.
6. If any errors occur in replication, an email will be generated stating that an error has occured, in a generic way.
