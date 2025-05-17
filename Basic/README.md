# Basic Interpreter - 2023 动手指南

#### deadline: 第 13 周 周一 (12.4) 18:30

| 负责助教                                   |
|----------------------------------------|
| [@何彦衡](https://github.com/HenryHe0123) |
| [@王冠杰](https://github.com/Irfnfnkemed) |

##  1. 前言

BASIC 是一门**解释性**编程语言，本次大作业要求你用 C++ 实现这个语言中的一些功能，来完成一个 Minimal 版本的 BASIC 解释器。

**该解释器应具有的功能有：**

- **立即解释**某些语句并运行
- 执行特定控制语句
- 按照**行数升序依次运行**的大程序

**本次大作业的目标：**

- 熟悉派生类的使用
- 锻炼文档的阅读能力
- 初步了解解释器的设计

**关于评测：**

我们进行基本的**鲁棒性检测**和**内存泄漏检测**，但是不进行性能检测，你只需要通过下发的数据点即可。


## 2. 下发文件解释

```plain
├── Basic
│   ├── Basic.cpp
│   ├── Utils
│   │   ├── error.cpp
│   │   ├── error.hpp
│   │   ├── strlib.cpp
│   │   ├── strlib.hpp
│   │   ├── tokenScanner.cpp
│   │   └── tokenScanner.hpp
│   ├── evalstate.cpp
│   ├── evalstate.hpp
│   ├── exp.cpp
│   ├── exp.hpp
│   ├── parser.cpp
│   ├── parser.hpp
│   ├── program.cpp
│   ├── program.hpp
│   ├── statement.cpp
│   └── statement.hpp
├── StanfordCPPLib
├── Test
├── Basic-Demo-64bit
├── CMakeLists.txt
├── .gitignore
├── Minimal BASIC Interpreter - 2023.pdf
├── README.md
└── score.cpp
```

### 2.1 你需要补充代码的部分

```plain
├── Basic
│   ├── Basic.cpp
│   ├── evalstate.cpp
│   ├── evalstate.hpp
│   ├── exp.cpp
│   ├── exp.hpp
│   ├── parser.cpp
│   ├── parser.hpp
│   ├── program.cpp
│   ├── program.hpp
│   ├── statement.cpp
│   └── statement.hpp
```

**注意：**

一般来讲，你只需补充 `Basic/Basic.cpp` `Basic/program.hpp` `Basic/program.cpp` `Basic/statement.hpp` `Basic/statement.cpp` 中的代码即可完成作业要求。当然，你也可以根据自己的需要修改其他文件。同时，你也应该仔细学习使用其他文件。


### 2.2 你需要学习使用的部分

```plain
├── Basic
│   ├── Utils
│   │   ├── error.cpp
│   │   ├── error.hpp
│   │   ├── strlib.cpp
│   │   ├── strlib.hpp
│   │   ├── tokenScanner.cpp
│   │   └── tokenScanner.hpp
```

**注意：**

这部分文件正常情况下你**不应修改**，如确信这部分文件有问题，请找出问题后向助教反馈。

**学习方法：**

`Basic/Utils/strlib.hpp` 和 `Basic/Utils/tokenScanner.hpp` 源于 StanfordCPPLib，是在 StanfordCPPLib 基础上进行过修改的版本，基本排除了由于编译器版本导致的问题，同时也基本修复了原代码的 memory leak 问题，使用方法与 StanfordCPPLib 中对应文件相同，请通过阅读文件中的注释，以及查阅官方文档 [The StanfordCPPLib package](https://cs.stanford.edu/people/eroberts/StanfordCPPLib/doc/index.html) 自行学习。

一般来说，你只需要使用 `Basic/Utils/strlib.hpp` 和 `Basic/Utils/tokenScanner.hpp` 。当然，如果你愿意的话，也可以自己使用 StanfordCPPLib 的其它文件(但请务必在使用前仔细阅读说明，并检查是否会造成内存泄漏)。

`error.hpp` 的使用请参考 [C++ 异常处理 - 菜鸟教程](https://www.runoob.com/cplusplus/cpp-exceptions-handling.html)。请务必熟悉代码中的异常处理方法，包括助教给出的代码。


### 2.3 本地评测方法

```plain
├── Basic-Demo-64bit
├── CMakeLists.txt
├── Test
└── score.cpp
```

**评测数据：**

`Test` 文件中的 100 个数据点，这些文件和oj中测评的数据点是相同的。

**评测原理：**

与标程对拍 （指进行相同输入看输出是否相同）

**标程：**

如果你用的是wsl或linux，请删除`Basic-Demo-64bit_for_mac_to_be_rename`。

如果你用的是mac，请删除`Basic-Demo-64bit`，并将`Basic-Demo-64bit_for_mac_to_be_rename`改名为`Basic-Demo-64bit`。

之后的步骤中我们认为你完成了此操作。

`Basic-Demo-64bit`是标程的可执行文件，你可以用命令行输入`./Basic-Demo-64bit`来运行它，看看BASIC解释器是如何工作的。

【注：

如果你用的不是wsl，而是mac或linux，在运行`./Basic-Demo-64bit`的时候，可能会出现 Permission denied 错误。这时候运行`chmod +x Basic-Demo-64bit`应当可以解决此问题。

如果你在wsl下运行`./Basic-Demo-64bit`的时候出现 Permission denied 错误，可以先运行`chmod +x Basic-Demo-64bit`来修改权限。 】

**评测脚本使用方法：**

编译 `score.cpp`，然后运行编译产生的文件，即可。

e.g. 命令行中输入：

```bash
g++ -o score score.cpp
./score -f
```

即可进行本地测试。

你可以输入 `./score -h` 来查看帮助。


【注意：如果你修改了仓库中给出框架的文件结构，请相应修改`score.cpp`中的`main`函数中的相关文件路径，否则无法正常进行本地测试。】

### 2.4 解释器实现步骤及待实现文件介绍

注意：这是助教实现上的设计建议，你可以完全抛开现有框架自己实现，只需在 code review 时与助教说明即可。

**对于指令的介绍和要求详见 `Minimal BASIC Interpreter - 2023.pdf`**

- #### 读入指令并切片

**目的：** 将指令按照一定规律划分，以便于使用。

**实现方法：** 学习使用 `Basic/Utils/tokenscanner` 来帮助你完成这一步。

**实现位置：** `Basic/Basic.cpp`

- ####  指令合法性检查

**目的：**  检查获得的切片是否满足类型要求以及切片的组合方式是否满足指令格式。

**实现方法：** 学习使用 `Basic/Utils/tokenscanner` 来帮助你完成这一步。

**实现位置：** `Basic/Basic.cpp`

e.g.

```
111         --> a valid integer
1a1         --> an invalid integer
```

```
END         --> a valid END command
END Hahaha  --> an invalid END command
```

- #### 指令存储

**目的：**  用于实现大程序中的跳转指令，指令打印等等。

**实现方法：** 使用数据结构，如 map， set 等，请自行设计。

**实现位置：** `Basic/program.cpp, Basic/program.hpp`

- #### 指令运行

**目的：** 执行指令

**实现方法：** 完成 `Basic/statment.hpp`中的类的设计和实现，在 `Basic/Basic.cpp` 中通过调用 `Basic/statment` 及其子类的 `execute` 函数实现。

**实现位置：** `Basic/statment.cpp, Basic/statment.hpp`

【注：关于表达式的计算：

1.  `Basic/parser.hpp` 对表达式进行正确性检查，并将其解释成一棵表达式树。

2.  `Basic/exp.hpp` 对表达式进行求值。

3.  `Basic/evalstate.hpp` 存储程序运行过程的变量与值。】

## 2.5 关于 OJ 评测

你需要使用git进行版本管理和代码提交。比如，你的git仓库地址是 `Your_profile/Your_repo`，你只需要在OJ的相应页面中输入`https://github.com/Your_profile/Your_repo` 即可进行提交。

**注意，你的可执行文件的名字应为 `code`（如果你修改了Cmake，请务必保证可执行文件名仍为`code`）。**

测评文件内容默认是 Test 文件夹下提供的文件。这些文件和 oj 中测评的数据点是相同的。在这些测试点下，你的程序需要输出与标程相同的结果。

## 2.6 关于 code review

- 请务必保证你完全清楚你在写什么，且**严禁抄袭**。


## 2.7 修改日志

- 2023/11/15 修复 `Basic/parser.cpp` 中无法读入带括号的负数的问题。