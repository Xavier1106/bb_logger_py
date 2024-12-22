// 安装 bb_logger

//pip install -U git+ssh://git@172.18.0.108/DEV/bb_logger_py.git

from bb_logger.logger import Logger

import logging

format = '%(asctime)s - %(levelname)s - demo: %(message)s'

name = 'demo'

path = './logs'

backupCount = 1

ot = {
    'ot-traceid': '12345678',
    'ot-spanid': '11111111',
    'ot-parent-spanid':  '22222222',
    'ot-starttime': '1234',
    'ot-duration': '5678',
}

// 全局只需初始化一次

Logger(path=path, name=name, service=True, trace=True, audit=True, format=format, level=logging.INFO,
       backupCount=backupCount)

Logger.service('test bb logger', 'info')

Logger.trace(ot, 'trace bb logger')

Logger.audit('audit bb logger')

