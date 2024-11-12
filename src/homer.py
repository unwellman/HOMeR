import discord
from discord.ext import commands

import os
import time
from functools import wraps

from log import Log

class Homer (commands.Bot):
    def __init__ (self, *args, **kwargs):
        self.admins = []
        try:
            self.mc_dir = kwargs.pop('mc_dir')
            self.mc_screen = kwargs.pop('mc_screen')
        except KeyError:
            raise
        fp = os.path.join(self.mc_dir, 'logs', 'screenlog.0')
        self.log = Log(fp)
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

    def force_flush (self):
        flush = lambda t: \
                f'screen -S {self.mc_screen} -p 0 -X '\
                'colon "logfile flush {t}^M"'
        os.system(flush(0)) # Force screen to write output to file
        time.sleep(0.5)
        os.system(flush(10)) # Restore default screen flush time

    def pass_console (self, console):
        '''
        Pass a command to the minecraft console
        and return its output
        '''
        cmd = 'screen -S {} -p 0 -X stuff "`printf "{}\r"`"'\
            .format(self.mc_screen, console)
        os.system(cmd)
        
        self.force_flush()
        ret = self.log.console_output(console)
        # Consider some post-processing to clean up screen escapes
        # Assume start with >[2K\n
        ret = ret[5:]
        return ret
        
intents = discord.Intents.default()
intents.message_content = True
homer = Homer('/', intents=intents,
              mc_dir='/home/noah/minecraft',
              mc_screen='minecraft')

@homer.command()
@homer.admin_only
async def console (ctx, *, arg):
    '''
    DEVELOPER ONLY: Send any console command to the server
    '''
    try:
        ret = homer.pass_console(arg)
        await ctx.send('Server response:\n```' + ret + '```')
    except Exception as e:
        await ctx.send(f'Server threw exception: `{e}`')

@homer.command()
async def say (ctx, *, arg):
    '''
    Send a chat message to the server. Prefixed with [DISCORD: <your username>]
    '''
    name = ctx.author.display_name
    con = f'say [\e[0;32mDISCORD: \e[0m{name}] {arg}'
    try:
        ret = homer.pass_console(con)
        await ctx.send('Sent message:\n```' + ret + '```')
    except Exception as e:
        await ctx.send(f'Server threw exception: `{e}`')

@homer.command()
async def list (ctx):
    '''
    List online players
    '''
    try:
        ret = homer.pass_console('list')
        await ctx.send(f'```{ret}```')
    except Exception as e:
        await ctx.send('Server threw exception: `{e}`')


