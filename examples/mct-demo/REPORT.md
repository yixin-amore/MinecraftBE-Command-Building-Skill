# 试运行报告（本地，不提交 GitHub）

## 1. mct 工具链

```text
selfcheck_env.py        ✅ 环境完整
DSL 示例               7 条链 / 91 条命令
cbc 布局               99 个命令方块 / 8 个区块
verify_mcworld          ✅ 通过
mcworld_to_structure    94 KB, 3558 方块, 99 个命令方块
```

产物：

- `trial/demo.mcworld`
- `trial/demo.mcstructure`
- `trial/demo-spec.json`

## 2. CHelper 语法 oracle

网易 1.21.50 cpack，跳过 `{RESET}` 占位：

```text
87 条命令
84 通过
3 报错
```

3 条都是：

```text
gamerule commandblockoutput false
gamerule sendcommandfeedback false
gamerule showcoordinates true
```

CHelper 的该版本没有展开 `gamerule` 规则枚举，属于 oracle 的枚举盲区；
不是 DSL 生成的语法错误。后续在 oracle 中把 `gamerule` 列为**动态枚举白名单**，只检查命令结构。

## 3. Frostcrown 压力测试

对现有 432 条命令跑同一 oracle：

```text
191 通过 / 241 报错
```

报错集中在：

- `effect ... infinite`：CHelper 要求整数，但基岩命令允许 `infinite`（oracle 语法/版本差异）
- `fill ... packed_ice 0 replace ice`：旧方块状态写法，1.21.50 数据不认
- 其余多为选择器 / 参数类型差异

结论：**CHelper 是语法提示器，不是语义裁判**。FMBE 的 carrier、绑定、命中仍要我们自己的类型系统校验。

## 4. 当前结论

- mct 的 DSL → spec → 链布局 → 结构文件路线，试运行成功。
- CHelper 可做本地语法 oracle，但必须处理动态枚举/版本差异。
- FMBE 模型层、NXS 适配层还没接入；需要模型 IR 和 NXS 样例。
- BDX / 网易租赁服导入还没接；目前只验证到 `.mcstructure`。
- 未提交 GitHub。
