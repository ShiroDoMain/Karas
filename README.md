<div style="text-align: center">
    <h1>Karas</h1><br>
<p>这是一个基于<a href="https://github.com/project-mirai/mirai-api-http">mirai-api-http</a>的轻量级，高性能qq消息处理与发送框架  </p>
</div>

##  Version  
![Mirai-API-API-Version](https://img.shields.io/badge/mirai--http--api->=2.5.0-brightgreen.svg?style=plastic)
![python-Version](https://img.shields.io/badge/python->=3.7-brightgreen.svg?style=plastic)
![karas-Version](https://img.shields.io/badge/karas-0.2.11-brightgreen.svg?style=plastic)    
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

yurine.sendFriend(1808107177, [Plain("Hello World")])

yurine.close()
```

## 实例
[ATRI](https://github.com/ShiroDoMain/ATRI-qqbot)使用了该框架开发，Bot的qq为1977987864  

## Notice  
该框架目前处于开发中状态，如果您在使用过程中发现了bug或者您有好的建议，请尽情提出您的[issues](https://github.com/ShiroDoMain/Karas/issues/new)

## 开源
该框架遵循AGPL-3.0协议开源，
```
iTXTech Mirai Console Loader
Copyright (C) 2020-2022 iTX Technologies

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```


## 鸣谢  
本项目使用了[JetBrains](https://www.jetbrains.com/?from=karas)的工具[PyCharm](https://www.jetbrains.com/pycharm/?from=karas)开发  
感谢JetBrains公司为开源项目提供的授权和支持  
![https://www.jetbrains.com/?from=karas](https://avatars.githubusercontent.com/u/878437?s=200&v=4)

