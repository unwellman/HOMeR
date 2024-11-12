from functools import wraps
import os
import time

class Log:
    '''
    Data structure for getting Minecraft logs
    '''
    def __init__ (self, fp):
        self.log = fp

    def filemethod (method):
        '''
        Safely run a method that accesses log file and closes log file
        Requires that file be the first argument after self
        '''
        @wraps(method)
        def run (self, *args, **kwargs):
            with open(self.log, 'rb') as file:
                return method(self, file, *args, **kwargs)
        return run

    @filemethod
    def console_output (self, log, console):
        '''
        Searches for a console command and tries to return its output
        '''
        search = '>' + console
        search = search.encode(encoding='utf-8')
        if '\n'.encode(encoding='utf-8') in search:
            raise ValueError('Multiline commands not supported')
        log.seek(0, 2) # Jump to EOF
        i = log.tell()
        step = len(search) - 1
        # Decrement step to guarantee that the cursor lands inside search
        log.seek(i - step)
        buf = log.read(step)
        i = log.tell()
        while search not in buf:
            if i < 2*step:
                raise IndexError('Could not find search pattern in file')
            log.seek(i - 2*step) #Jump before last read section
            buf = log.read(step) + buf #Prepend to buffer
            i = log.tell() #Prepare to jump again
        # At this point, the cursor is inside the search pattern
        line = log.readline() # Throw away the line with the command
        ret = ''.encode(encoding='utf-8')
        while not line.startswith('>'.encode(encoding='utf-8')):
            line = log.readline()
            ret += line
        return ret.decode(encoding='utf-8')


