import asyncio
import websockets

danmu_pool = []
comment_pool = []
"""
this is a list containing the connected clients
"""


class danmu:
    def __init__(self, time, con):
        self.time = time
        self.content = con

# class Comment:
#     def __init__(self,con,time):
#         self.content=con
#         self.time=time
# ♉
async def reply(websocket):
    """
        receive the danmaku and send it to every client
    """
    global danmu_pool
    while True:
        receive = await websocket.recv()
        t = receive.split('♉')
        if t[0] == '0':  # get
            for i in danmu_pool:
                if int(i.time) == int(t[1]):
                    await websocket.send(i.content)
        elif t[0] == '1':
            danmu_pool.append(danmu(t[1], t[2]))
        elif t[0]=='2':
            comment_pool.append(t[1])
        else:#send comment
            comments=''
            for comment in comment_pool:
                comments=comments+'♉'+comment
            await websocket.send(comments)
        # for connect in websocket_pool:  # traverse the clients, send danmaku to everyone
        #     await connect.send(receive)


async def serve(websocket, path):
    # websocket_pool.append(websocket)  # add client to list
    await reply(websocket)


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(
            websockets.serve(serve, 'localhost', 8765))
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass
