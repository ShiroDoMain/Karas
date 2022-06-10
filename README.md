<div align="center">
    <h1>Karas</h1><br>
<p>这是一个基于<a href="https://github.com/project-mirai/mirai-api-http">mirai-api-http</a>的轻量级，高性能qq消息处理与发送框架  </p>
</div>

##  Version  
![Mirai-API-API-Version](https://img.shields.io/badge/mirai--http--api-2.5.0-brightgreen.svg?style=plastic)
![python-Version](https://img.shields.io/badge/python->=3.7-brightgreen.svg?style=plastic)
![karas-Version](https://img.shields.io/badge/karas-0.1.6-brightgreen.svg?style=plastic)    
## 使用  
- 使用pip安装本项目  
```shell script
pip3 install karas_py
```  
- 一个群聊复读机实例:  
(async)
```python
from karas.box import Yurine,MessageChain,Group
yurine = Yurine(
    host="localhost",
    port=8080,
    qq=114514,
    verifyKey="1919810"
)

@yurine.listen("GroupMessage")
async def gm_event(group:Group, message: MessageChain):
    # async send message
    await yurine.sendGroup(group, message)

yurine.run_forever()
```  
(sync send message)
```python
from karas.box import Yurine,MessageChain,Group, Plain
yurine = Yurine(
    host="localhost",
    port=8080,
    qq=114514,
    verifyKey="1919810"
).start()

yurine.sendFriend(1808107177, [Plain("Hello World)])
```

## Notice  
该框架目前处于开发中状态，如果您在使用过程中发现了bug或者您有好的建议，请尽情提出您的[issues](https://github.com/ShiroDoMain/Karas/issues/new)