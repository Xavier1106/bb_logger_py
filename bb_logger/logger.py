import logging
import logging.handlers
import os
import sys
import opentracing
import time
import copy
import json
from bb_logger.bb_handler.save_file_handler import SafeFileHandler

folder = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ''))
sys.path.append(folder)


def format_console_msg(name, source_msg, level, msg_type):
    msg = dict()
    msg['msg'] = source_msg
    msg['_APP_'] = name
    msg['_LEVEL_'] = level
    msg['_TYPE_'] = msg_type
    return msg


class Logger:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance_'):
            cls._instance_ = super().__new__(cls)
            cls._file_ = kwargs.get('file', True)
            cls._name_ = kwargs.get('name', 'default')
            if cls._file_:
                cls()._init_logger_(**kwargs)
        return cls._instance_

    def _init_logger_(self, **kwargs):
        path = kwargs['path'] if 'path' in kwargs else './'
        if not os.path.exists(path):
            os.mkdir(path)
        file = path + '/' + self._name_

        service = kwargs['service'] if 'service' in kwargs else True
        trace = kwargs['trace'] if 'trace' in kwargs else False
        audit = kwargs['audit'] if 'audit' in kwargs else False
        format = kwargs['format'] if 'format' in kwargs else '%(asctime)s - %(levelname)s - ' + name + ': %(message)s'
        level = kwargs['level'] if 'level' in kwargs else logging.INFO
        backupCount = kwargs['backupCount'] if 'backupCount' in kwargs else 0

        if service is True:
            self._create_logger_('service', file + '.log', level, format, backupCount)
        if trace is True:
            self._create_logger_('trace', file + '.trace.log', level, format, backupCount)
        if audit is True:
            self._create_logger_('audit', file + '.audit.log', level, format, backupCount)
        return

    def _create_logger_(self, type, file, level, format, backupCount):
        if type == 'service':
            self._service_ = logging.getLogger(type)
        elif type == 'trace':
            self._trace_ = logging.getLogger(type)
        elif type == 'audit':
            self._audit_ = logging.getLogger(type)

        logger_format = format
        if type == 'audit':
            logger_format = '%(message)s'

        handler = SafeFileHandler(file, backupCount=backupCount, encoding='utf8')
        formatter = logging.Formatter(logger_format)
        handler.setFormatter(formatter)
        self.addHandler(type, handler)
        self.setLevel(type, level)

    def _print_log_(self, func, message):
        func(message)
        return

    def _print_console_(self, message):
        print(message)
        return

    def _get_ot_(self, span=None, ls_tracer=None):
        ot = {}
        if span and ls_tracer:
            span.finish()
            ls_tracer.inject(span.context, opentracing.Format.TEXT_MAP, ot)

            ot_info = {
                'ot-traceid': ot['ot-tracer-traceid'],
                'ot-spanid': ot['ot-tracer-spanid'],
                'ot-parent-spanid':  str(hex(span.parent_id))[2:] if span.parent_id is not None else '',
                'ot-starttime': span.start_time,
                'ot-duration': span.duration,
            }
            return ot_info
        else:
            return None


    @classmethod
    def addHandler(cls, name, handler):
        if name == 'service':
            cls()._service_.addHandler(handler)
        elif name == 'trace':
            cls()._trace_.addHandler(handler)
        elif name == 'audit':
            cls()._audit_.addHandler(handler)

    @classmethod
    def setLevel(cls, name, level):
        if name == 'service':
            cls()._service_.setLevel(level)
        elif name == 'trace':
            cls()._trace_.setLevel(level)
        elif name == 'audit':
            cls()._audit_.setLevel(level)

    def service_to_file(self, service_info, level):
        func_map = {
            'info': self._service_.info,
            'warning': self._service_.warning,
            'debug': self._service_.debug,
            'error': self._service_.error,
            'exception': self._service_.exception,
            'critical': self._service_.critical
        }
        self._print_log_(func_map[level], service_info)
        return

    @classmethod
    def service(cls, service_info, level='info'):
        if cls()._file_:
            cls().service_to_file(service_info, level)
        else:
            msg = format_console_msg(cls()._name_, service_info, level, 'general')
            cls()._print_console_(msg)
        return

    def trace_to_file(self, trace_info, span, ls_tracer, level):
        ot = self._get_ot_(span, ls_tracer)
        ot_info = ''
        if ot:
            ot_info = 'ot-traceid:%s ot-parent-spanid:%s ot-spanid:%s ot-starttime:%s ot-duration:%s ' \
                            %(ot['ot-traceid'],
                            ot['ot-parent-spanid'],
                            ot['ot-spanid'],
                            ot['ot-starttime'],
                            ot['ot-duration'])
        else:
            ot_info = 'span or ls_tracer is wrong!! Please check it.'

        func_map = {
            'info': self._trace_.info,
            'warning': self._trace_.warning,
            'debug': self._trace_.debug,
            'error': self._trace_.error,
            'exception': self._trace_.exception,
            'critical': self._trace_.critical
        }
        traceMessage = ot_info + ' ' + trace_info
        self._print_log_(func_map[level], traceMessage)
        return

    @classmethod
    def trace(cls, trace_info, span=None, ls_tracer=None, level='info'):
        if cls()._file_:
            cls().trace_to_file(trace_info, span, ls_tracer, level)
        else:
            msg = format_console_msg(cls()._name_, trace_info, level, 'event')
            cls()._print_console_(msg)
        return

    def audit_to_file(self, audit_info, level):
        func_map = {
            'info': self._audit_.info,
            'warning': self._audit_.warning,
            'debug': self._audit_.debug,
            'error': self._audit_.error,
            'exception': self._audit_.exception,
            'critical': self._audit_.critical
        }
        # audit log format (dict type)
        dicts = copy.deepcopy(audit_info)
        dicts['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        dicts['service'] = self._name_
        message = json.dumps(dicts, ensure_ascii=False)
        self._print_log_(func_map[level], message)
        return

    @classmethod
    def audit(cls, audit_info, level='info'):
        if cls()._file_:
            cls().audit_to_file(audit_info, level)
        else:
            msg = format_console_msg(cls()._name_, audit_info, level, 'audit')
            cls()._print_console_(msg)
        return


def main():
    # example
    format = '%(asctime)s %(levelname)s demo: %(message)s'  # for service log, audit and tracing 为内部强制格式
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

    """
        path: 日志目录， default: 当前目录
        name: app name, default: default
        service:  启用日常日志，defalut: True
        trace: 启用trace日志, default: False
        format: 日志格式化，默认格式 '%(asctime)s %(levelname)s name %(message)s' 
            ex: 2018-04-23 11:42:45,468 INFO demoApp: test bb logger
        level: logging level  default: info
        file: True|False (False, log to console)
    """
    args = {
        'path': path,
        'name': name,
        'service': True,
        'trace': True,
        'audit': True,
        'format': format,
        'level': logging.INFO,
        'file': False
    }
    Logger(**args)
    Logger.service('test bb logger', 'info')
    Logger.trace('trace bb logger')
    Logger.audit(dict(content='测试'))


if __name__ == '__main__':
    main()
