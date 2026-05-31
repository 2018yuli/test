<!-- Source: https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/cranelift/docs/index.md -->
<!-- Title: Cranelift documentation index -->

# Cranelift Documentation

# Cranelift 文档

## Miscellaneous documentation pages:

## 其他文档页面：

 - [Cranelift IR](ir.md)
   Cranelift IR is the data structure that most of the compiler operates on.

- [Cranelift IR](ir.md)
   Cranelift IR 是编译器大部分组件所操作的数据结构。

 - [Testing Cranelift](testing.md)
   This page documents Cranelift's testing frameworks.

- [Testing Cranelift](testing.md)
   本页面记录了 Cranelift 的测试框架。

 - [Cranelift compared to LLVM](compare-llvm.md)
   LLVM and Cranelift have similarities and differences.

- [Cranelift compared to LLVM](compare-llvm.md)
   LLVM 和 Cranelift 既有相似之处，也有不同之处。

## Cranelift crate documentation:

## Cranelift crate 文档：

 - [cranelift](https://docs.rs/cranelift)
    This is an umbrella crate that re-exports the codegen and frontend crates,
    to make them easier to use.

- [cranelift](https://docs.rs/cranelift)
    这是一个总括性 crate，会重新导出 codegen 和 frontend crate，
    以便更轻松地使用它们。

 - [cranelift-codegen](https://docs.rs/cranelift-codegen)
    This is the core code generator crate. It takes Cranelift IR as input
    and emits encoded machine instructions, along with symbolic relocations,
    as output.

- [cranelift-codegen](https://docs.rs/cranelift-codegen)
    这是核心代码生成器 crate。它以 Cranelift IR 作为输入，
    并输出编码后的机器指令以及符号重定位。

 - [cranelift-codegen-meta](https://docs.rs/cranelift-codegen-meta)
    This crate contains the meta-language utilities and descriptions used by the
    code generator.

- [cranelift-codegen-meta](https://docs.rs/cranelift-codegen-meta)
    此 crate 包含代码生成器所使用的元语言工具和描述。

 - [cranelift-frontend](https://docs.rs/cranelift-frontend)
    This crate provides utilities for translating code into Cranelift IR.

- [cranelift-frontend](https://docs.rs/cranelift-frontend)
    此 crate 提供用于将代码转换为 Cranelift IR 的实用工具。

 - [cranelift-native](https://docs.rs/cranelift-native)
    This crate performs auto-detection of the host, allowing Cranelift to
    generate code optimized for the machine it's running on.

- [cranelift-native](https://docs.rs/cranelift-native)
    此 crate 会对宿主机进行自动检测，使 Cranelift 能够
    生成针对其运行所在机器优化的代码。

 - [cranelift-reader](https://docs.rs/cranelift-reader)
    This crate translates from Cranelift IR's text format into Cranelift IR
    in in-memory data structures.

- [cranelift-reader](https://docs.rs/cranelift-reader)
    此 crate 将 Cranelift IR 的文本格式转换为内存数据结构中的
    Cranelift IR。

 - [cranelift-module](https://docs.rs/cranelift-module)
    This crate manages compiling multiple functions and data objects
    together.

- [cranelift-module](https://docs.rs/cranelift-module)
    此 crate 负责将多个函数和数据对象一起编译。

 - [cranelift-object](https://docs.rs/cranelift-object)
    This crate provides a object-based backend for `cranelift-module`, which
    emits native object files using the
    [object](https://github.com/gimli-rs/object) library.

- [cranelift-object](https://docs.rs/cranelift-object)
    此 crate 为 `cranelift-module` 提供基于对象文件的后端，
    该后端使用 [object](https://github.com/gimli-rs/object) 库
    生成原生对象文件。

 - [cranelift-jit](https://docs.rs/cranelift-jit)
    This crate provides a JIT backend for `cranelift-module`, which
    emits code and data into memory.

- [cranelift-jit](https://docs.rs/cranelift-jit)
    此 crate 为 `cranelift-module` 提供 JIT 后端，
    该后端将代码和数据生成到内存中。
