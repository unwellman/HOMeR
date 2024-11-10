from homer import homer

def get_tokens(fp):
    src = open(fp, 'r')
    ret_id = src.readline()
    ret_sec = src.readline()
    ret_bot = src.readline()
    return ret_id, ret_sec, ret_bot

if __name__ == '__main__':
    bot_id, app_token, bot_token = get_tokens('token.txt')
    homer.run(bot_token)

