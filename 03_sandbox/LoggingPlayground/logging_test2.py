import logging

loglevel='DEBUG'

numeric_level = getattr(logging, loglevel.upper(), None)

print 'Numeric level = ' + str(numeric_level)

if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

logging.basicConfig(filename='example.log', level=numeric_level, filemode='w')

logging.debug('This message should go in the log file.')
logging.info('So should this.')
logging.warning('And this, too.')
logging.error('This is the error, my only friend the error.')

loglevels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

for level in loglevels:
    num_level = getattr(logging, level.upper(), None)

    if not isinstance(num_level, int):
        raise ValueError('Invalid log level: %s' % level)

    print "Log level: " + str(level) + ", numeric value = " + str(num_level)