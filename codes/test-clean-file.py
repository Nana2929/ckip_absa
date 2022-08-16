outlog = './my-absa-log.log'
import logging, os
logging.basicConfig(filename = outlog,
        filemode='w',
        level=logging.INFO,
        format='%(asctime)s.[%(levelname)s] %(message)s',
        datefmt='%H:%M:%S')

logging.info('==content喵喵')
logging.info('做事！')
with open(outlog, 'r+') as fh:
    readstring = fh.readlines()
    print('first read:')
    print(''.join(readstring))
    fh.truncate(0)
    fh.seek(0)
    
logging.info('喵喵content==')
logging.info('睡覺！')




print('second read:')
with open(outlog, 'r+') as fh:
    readstring = fh.readlines()
    print(''.join(readstring))
    fh.truncate(0)
    fh.seek(0)
# with open(outlog, 'w') as fh:
#     pass
