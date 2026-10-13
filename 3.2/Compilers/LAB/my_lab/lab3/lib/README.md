# JUnit 依赖库

本目录用于存放 JUnit 测试框架的 JAR 文件。

## 下载 JUnit 4

请从以下地址下载 JUnit 4 的 JAR 文件：

1. **junit-4.13.2.jar**: https://repo1.maven.org/maven2/junit/junit/4.13.2/junit-4.13.2.jar
2. **hamcrest-core-1.3.jar**: https://repo1.maven.org/maven2/org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar

## 安装步骤

1. 将下载的两个 JAR 文件放入此 `lib` 目录
2. 确保文件名为：
   - `junit-4.13.2.jar`
   - `hamcrest-core-1.3.jar`

## 目录结构

```
lib/
├── README.md           (本文件)
├── junit-4.13.2.jar    (需要下载)
└── hamcrest-core-1.3.jar (需要下载)
```

## 使用方法

编译测试类：
```bash
javac -cp ".;lib/junit-4.13.2.jar;lib/hamcrest-core-1.3.jar" src/ParserTest.java
```

运行测试：
```bash
java -cp ".;bin;lib/junit-4.13.2.jar;lib/hamcrest-core-1.3.jar" org.junit.runner.JUnitCore ParserTest
```

或者使用提供的 `test.bat` 脚本。