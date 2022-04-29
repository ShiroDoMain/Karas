import aiohttp
import asyncio


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url="ws://localhost:8080/all",headers={"verifyKey":"nothing","qq":str(1838745732)}) as ws:
            res = await ws.receive_json()
            sessKey = res["data"]["session"]
            print(res)
            res = await session.post("http://localhost:8080/uploadVoice",data={"sessionKey":sessKey,"type":"group","voice":open("test.amr","rb")})
            res = await res.json()
            # await ws.send_json({
            #     "syncId": 123, 
            #     'command': 'sendGroupMessage',
            #     'content':{
            #         'sessionKey': sessKey,
            #         'group': 933414599,
            #          'messageChain': [
            #              {'type': 'Image', 'url': res.get("url")}
            #              ]
            #              }
            #     })
            # res = await ws.receive_json()
            print(res)

asyncio.run(main())
