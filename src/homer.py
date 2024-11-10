import discord
from discord.ext import commands

import os
import time

class Homer(commands.Bot):
    def __init__ (self, *args, **kwargs):
        try:
            self.mc_dir = kwargs.pop('mc_dir')
            self.mc_screen = kwargs.pop('mc_screen')
        except KeyError:
            raise
        self.log = os.path.join(self.mc_dir, 'logs', 'screenlog.0')
        super().__init__(*args, **kwargs)

    def pass_console(self, console):
        '''
        Pass a command to the minecraft console
        and return its output
        '''
        flush = lambda t: \
                f'screen -S {self.mc_screen} -p 0 -X '\
                'colon "logfile flush {t}^M"'
        os.system(flush(0)) # Force screen to write output to file
        cmd = 'screen -S {} -p 0 -X stuff "`printf "{}\r"`"'\
            .format(self.mc_screen, console)
        os.system(cmd)
        time.sleep(0.5)
        os.system(flush(10)) # Restore default screen flush time
        with open(self.log, 'rb') as log:
            ret = self.__fetch_log(console, log)
        # Consider some post-processing to clean up screen escapes
        # Assume start with >[2K\n
        ret = ret[5:]
        return ret

    def __fetch_log(self, console, log):
        '''
        Find last instance of console command in latest.log
        and grab Minecraft's output
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

        
intents = discord.Intents.default()
intents.message_content = True
homer = Homer('/', intents=intents,
              mc_dir='/home/noah/minecraft',
              mc_screen='minecraft')

@homer.command()
async def console(ctx, *, arg):
    try:
        ret = homer.pass_console(arg)
        await ctx.send('Server response:\n```' + ret + '```')
    except Exception as e:
        await ctx.send(f'Server threw exception: `{e}`')

