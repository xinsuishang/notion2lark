# notion2lark

---

**目的：** 同步 notion 日历到本地日历

**原因：** notion 计划和管理基于 database 虽然强大但日程无法统一管理

**方式：** 同步 notion database 到 飞书日历，再通过飞书日历的 calDav 同步给系统自带日历

**实现：**
1. 轮询指定的 database，获取最近更新的数据
2. 仅有 title 及 Date 字段才处理
3. 本地缓存对应的 pageId（唯一id） 及 lastEditTime（版本号）
4. 解析关键字段，创建/更新飞书日程
   1. 新增：notion 中没有日程id
   2. 更新：版本号不一致
5. 邀请指定用户加入飞书日程（仅飞书中没有日程id时）
6. 回写日程 id 到 notion（仅飞书中没有日程id时）

**缺陷：**
1. 无法删除日历
2. 重启后会更新一次所有的日程
3. 删除之后如果取消了日程，恢复页面后无法创建日程

**原因：**
1. 本地没有 `飞书日程id` 对应 `notion database page id` 的关系
2. 版本号在内存中维护
3. 回写了id，认为是更新，日程已取消，无法更新

**解决方案：**
1. 写个删除日程的接口和页面，删除页面时手动删除（略蠢）
2. 增加存储（文件、mysql等，甚至 notion），维护关系、版本号等信息，定时检查所有去做删除
3. 增加逻辑：查询日程对应状态

**其它：**
1. 飞书接口比较慢（1s+）
   1. 毕竟白嫖的，可能本身就有限制
   2. 2B接口，性能要求没那么高
2. calDav 轮询
   1. 本地日历更新没那么及时

**依赖：**

[python](https://www.python.org/)

[飞书 api](https://open.feishu.cn/document/home/index)

[notion api](https://developers.notion.com/)

[xinsuishang/lark](https://github.com/xinsuishang/lark)

[xinsuishang/notion](https://github.com/xinsuishang/notion)