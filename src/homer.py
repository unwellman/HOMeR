import discord
from discord.ext import commands

import os
import time
from functools import wraps

class Homer (commands.Bot):
    def __init__ (self, *args, **kwargs):
        self.admins = []
        try:
            self.mc_dir = kwargs.pop('mc_dir')
            self.mc_screen = kwargs.pop('mc_screen')
        except KeyError:
            raise
        self.log = os.path.join(self.mc_dir, 'logs', 'screenlog.0')
        super().__init__(*args, **kwargs)

    def set_admin (self, admin):
        '''
        Provide Discord UUID to grant permission for
        particularly dangerous commands
        '''
        self.admins.append(admin)

    def admin_only (self, func):
        @wraps(func)
        async def run (*args, **kwargs):
            # discord.py guarantees ctx argument first
            author_id = args[0].author.id
            if author_id not in self.admins:
                msg = 'You do not have permission to run this command!'
                await args[0].send(msg)
            else:
                return await func(*args, **kwargs)
        return run

    def pass_console (self, console):
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
        ret = self.fetch_console(console)
        # Consider some post-processing to clean up screen escapes
        # Assume start with >[2K\n
        ret = ret[5:]
        return ret

    def fetch_console (self, console):
        '''
        Find last instance of console command in latest.log
        and grab Minecraft's output
        '''
        with open(self.log, 'rb') as log:
            return self.__fetch_log(console, log)

    def __fetch_log (self, console, log):
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
@homer.admin_only
async def console (ctx, *, arg):
    try:
        ret = homer.pass_console(arg)
        await ctx.send('Server response:\n```' + ret + '```')
    except Exception as e:
        await ctx.send(f'Server threw exception: `{e}`')

@homer.command()
async def say (ctx, *, arg):
    name = ctx.author.display_name
    con = f'say [DISCORD - {name}] {arg}'
    try:
        ret = homer.pass_console(con)
        await ctx.send('Sent message:\n```' + ret + '```')
    except Exception as e:
        await ctx.send(f'Server threw exception: `{e}`')

@homer.command()
async def list (ctx, *, arg):
    try:
        ret = homer.pass_console('list')
        await ctx.send(f'```{ret}```')
    except Exception as e:
        await ctx.send('Server threw exception: `{e}`')
