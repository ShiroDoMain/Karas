<div align="center">
    <h1>Karas</h1><br>
这是一个基于<a href="https://github.com、project-mirai/mirai-api-http">mirai-api-http</a>的qq机器人框架  
</div>
  
## 使用  
- 首先你需要安装requirements中的依赖  
```shell script
pip3 install -r requirements.txt
```  
- 一个群聊复读机实例:  
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
    await yurine.sendGroup(group, message)

yurine.run_forever()
```

## Notice  
该框架目前处于开发中状态，如果您在使用过程中发现了bug或者您有好的建议，请尽情提出您的[issues](https://github.com/ShiroDoMain/Karas/issues/new)