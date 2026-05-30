# Comprehensive Learning Resources for Cranelift (Beginner to Advanced)

# Cranelift 综合学习资源（从入门到高级）

## 1. Cranelift Official Documentation (Docs - Bytecode Alliance)

## 1. Cranelift 官方文档（文档 - Bytecode Alliance）

Start with the official docs to understand Cranelift's design and IR. The Bytecode Alliance provides thorough documentation covering Cranelift's intermediate representation (CLIF), type system, function signatures/ABI, and overall compiler pipeline [1]. These docs explain how Cranelift works as a library backend - translating a target-independent IR into machine code - and discuss concepts like SSA form, calling conventions, and supported architectures [2]. This is a definitive reference for all major components of Cranelift, suitable as you begin exploring or whenever you need in-depth details.

从官方文档开始，可以理解 Cranelift 的设计和中间表示（IR）。Bytecode Alliance 提供了详尽的文档，涵盖 Cranelift 的中间表示（CLIF）、类型系统、函数签名/ABI，以及整体编译器流水线 [1]。这些文档解释了 Cranelift 如何作为库形式的后端工作，也就是把与目标无关的 IR 转换为机器码，并讨论 SSA 形式、调用约定、受支持架构等概念 [2]。这是了解 Cranelift 各个主要组件的权威参考，既适合刚开始探索时阅读，也适合在需要深入细节时查阅。

## 2. Cranelift JIT Tutorial & Toy Language Demo (Code Example - GitHub repo)

## 2. Cranelift JIT 教程与玩具语言示例（代码示例 - GitHub 仓库）

Learn by example with an official JIT compiler demo. The Bytecode Alliance's `cranelift-jit-demo` repository contains a simple toy language implementation that uses Cranelift to JIT-compile code at runtime [3]. The well-documented README walks through constructing Cranelift IR with the `FunctionBuilder` API, handling variables and control flow (if/else, loops), and using the high-level `cranelift-jit` and `cranelift-module` APIs to manage memory and symbols [4] [5]. It even shows how to define function signatures, call external functions, and switch to producing native object files for AOT compilation [6]. This full-length example is great for beginners - it demonstrates JIT compilation step-by-step in real code, building your understanding of Cranelift's IR and runtime integration.

通过一个官方 JIT 编译器示例进行学习。Bytecode Alliance 的 `cranelift-jit-demo` 仓库包含一个简单的玩具语言实现，它使用 Cranelift 在运行时对代码进行 JIT 编译 [3]。文档完善的 README 会带你了解如何使用 `FunctionBuilder` API 构造 Cranelift IR，如何处理变量和控制流（if/else、循环），以及如何使用高级 `cranelift-jit` 和 `cranelift-module` API 管理内存和符号 [4] [5]。它甚至展示了如何定义函数签名、调用外部函数，以及如何切换到生成原生目标文件以进行 AOT 编译 [6]。这个完整示例非常适合初学者：它用真实代码一步一步演示 JIT 编译，帮助你建立对 Cranelift IR 和运行时集成方式的理解。

## 3. "Compilers in Rust: Cranelift" Video Series (Video - YouTube, 5 parts)

## 3. “Compilers in Rust: Cranelift” 视频系列（视频 - YouTube，共 5 部分）

Watch a progressive series of video tutorials covering Cranelift from fundamentals to advanced internals. Part 1 of this series introduces what Cranelift is, why one might choose it over LLVM, and how it serves as an all-Rust code generation backend [7] - perfect as a conceptual overview for newcomers. Subsequent episodes dive deeper: covering Cranelift's IR and type system basics, the ISLE DSL for instruction lowering (how high-level ops are lowered to machine instructions), adding a new backend (target integration), and finally instruction lowering & binary emission details in the codegen pipeline [8]. Across these videos, you'll see explanations of register allocation, calling conventions, and other engineering topics in a visual, approachable format. This series is ideal for learners who enjoy guided walkthroughs - start with the early parts for high-level context, and progress to later parts as you grow comfortable with Cranelift's concepts.

观看这一组循序渐进的视频教程，可以从基础到高级内部机制全面了解 Cranelift。该系列第 1 部分介绍 Cranelift 是什么、为什么有人会选择它而不是 LLVM，以及它如何作为一个全 Rust 的代码生成后端发挥作用 [7]，非常适合作为面向新手的概念总览。后续几集会进一步深入：讲解 Cranelift 的 IR 和类型系统基础、用于指令降低的 ISLE DSL（也就是如何把高级操作降低为机器指令）、如何添加新的后端（目标集成），最后介绍代码生成流水线中的指令降低和二进制发射细节 [8]。在这些视频中，你会以直观且易于理解的形式看到寄存器分配、调用约定以及其他工程主题的解释。这个系列很适合喜欢跟随式讲解的学习者：可以先从前几部分建立高层背景，再随着对 Cranelift 概念越来越熟悉，逐步进入后面的深入内容。

## 4. "Building a Brainfuck Compiler using Cranelift" by Clemens Tiedt (Blog Tutorial + Code)

## 4. Clemens Tiedt 的 “Building a Brainfuck Compiler using Cranelift”（博客教程 + 代码）

A beginner-friendly project walkthrough that covers the entire compilation process using Cranelift. This blog post details how to implement a simple Brainfuck language compiler in Rust with Cranelift [9] [10]. It guides you through all stages: parsing source code into an AST, translating the AST to Cranelift IR, and then using Cranelift to generate machine code and produce an executable (via an object file). Along the way, the article explains important concepts in context - for example, setting up the target ISA and default calling convention for the `Signature` (function ABI) [11] [12], and using `ObjectModule` to emit a native object file. This hands-on tutorial is great for those new to compiler development: you'll see how IR construction, function definitions, and code emission work in practice, with a real example that compiles and links a "Hello World" in Brainfuck. It's comprehensive but written for learners, so you'll gain practical experience with Cranelift's API and workflow.

这是一个适合初学者的项目 walkthrough，覆盖使用 Cranelift 的完整编译流程。这篇博客详细说明了如何用 Rust 和 Cranelift 实现一个简单的 Brainfuck 语言编译器 [9] [10]。它会引导你经历所有阶段：把源代码解析成 AST，将 AST 转换为 Cranelift IR，然后使用 Cranelift 生成机器码，并通过目标文件生成可执行文件。在这个过程中，文章会结合上下文解释重要概念，例如为 `Signature`（函数 ABI）设置目标 ISA 和默认调用约定 [11] [12]，以及使用 `ObjectModule` 发射原生目标文件。这个动手教程非常适合刚接触编译器开发的人：你会通过一个能编译并链接 Brainfuck 版 “Hello World” 的真实示例，看到 IR 构造、函数定义和代码发射在实践中如何工作。它内容全面，但面向学习者写作，因此能帮助你获得 Cranelift API 和工作流方面的实践经验。

## 5. "A Primer on Code Generation in Cranelift" by Benjamin Bouvier (Blog - deep dive)

## 5. Benjamin Bouvier 的 “A Primer on Code Generation in Cranelift”（博客 - 深入解析）

Deepen your understanding of Cranelift's internals and final machine-code generation stages. Written by a Cranelift engineer, this article follows a single instruction through the back-end pipeline - from its creation in CLIF IR down to the emitted machine code [13]. It breaks down key processes like IR lowering to a more machine-specific form (VCode), register allocation, and instruction scheduling/encoding into bytes. Each step comes with high-level explanations of the concept and how Cranelift implements it. While not a step-by-step tutorial, it's an excellent complementary read once you know the basics: for example, you'll learn how Cranelift's SSA-based IR is lowered and how the register allocator works behind the scenes, which demystifies how Cranelift achieves fast code generation without sacrificing too much performance. This resource is best for those who want to go from using Cranelift to truly understanding its engine under the hood, rounding out your knowledge of all major functional areas (IR, ABI, backend, regalloc, machine code emission) [13].

这篇文章可以加深你对 Cranelift 内部机制以及最终机器码生成阶段的理解。它由一位 Cranelift 工程师撰写，沿着后端流水线追踪一条指令，从它在 CLIF IR 中被创建，一直到最终发射出的机器码 [13]。文章拆解了多个关键过程，包括将 IR 降低到更贴近机器的形式（VCode）、寄存器分配，以及指令调度/编码为字节。每一步都配有对概念本身以及 Cranelift 实现方式的高层解释。虽然它不是一步一步的教程，但在你掌握基础之后，它是一篇非常好的补充读物：例如，你会了解 Cranelift 基于 SSA 的 IR 如何被降低，以及寄存器分配器在幕后如何工作，从而弄清 Cranelift 如何在不过度牺牲性能的前提下实现快速代码生成。这个资源最适合那些希望从“会使用 Cranelift”进一步走向“真正理解其底层引擎”的读者，可以补全你对主要功能领域（IR、ABI、后端、寄存器分配、机器码发射）的认识 [13]。

Each of these resources is well-maintained and beginner-appropriate, and together they form a progressive learning path. Start with the conceptual overviews (official docs and the Part 1 video) to grasp what Cranelift is. Then move on to the hands-on tutorials (the toy-language JIT demo and Brainfuck compiler blog) to learn how to construct IR and actually compile code using Cranelift's APIs. Finally, delve into the in-depth videos and Bouvier's engineering blog to explore Cranelift's deeper internals like backend integration, instruction lowering, and optimization infrastructure. This will give you a comprehensive understanding of Cranelift's functionality across IR, JIT/AOT, ABI, types, backends, and code generation, all tailored for newcomers to compiler development.

这些资源都维护良好，也适合初学者，并且合在一起构成了一条循序渐进的学习路径。可以先从概念总览（官方文档和第 1 部分视频）开始，理解 Cranelift 是什么。然后转向动手教程（玩具语言 JIT 示例和 Brainfuck 编译器博客），学习如何构造 IR，以及如何真正使用 Cranelift 的 API 编译代码。最后，再深入观看进阶视频并阅读 Bouvier 的工程博客，探索 Cranelift 更深层的内部机制，例如后端集成、指令降低和优化基础设施。这样你就能全面理解 Cranelift 在 IR、JIT/AOT、ABI、类型、后端和代码生成等方面的功能，而且这些内容都针对编译器开发新手进行了组织。

## References

## 参考资料

[1] [Cranelift](https://cranelift.dev/)

[2] [Cranelift](https://cranelift.dev/)

[3] [GitHub - bytecodealliance/cranelift-jit-demo: JIT compiler and runtime for a toy language, using Cranelift](https://github.com/bytecodealliance/cranelift-jit-demo)

[4] [GitHub - bytecodealliance/cranelift-jit-demo: JIT compiler and runtime for a toy language, using Cranelift](https://github.com/bytecodealliance/cranelift-jit-demo)

[5] [GitHub - bytecodealliance/cranelift-jit-demo: JIT compiler and runtime for a toy language, using Cranelift](https://github.com/bytecodealliance/cranelift-jit-demo)

[6] [GitHub - bytecodealliance/cranelift-jit-demo: JIT compiler and runtime for a toy language, using Cranelift](https://github.com/bytecodealliance/cranelift-jit-demo)

[7] [Cranelift, the All-Rust Codegen Alternative to LLVM (No C/C++, Part 1)](https://www.youtube.com/watch?v=ilhSdmv6bAY)

[8] [Instruction Lowering and Binary Emission in Cranelift (Part 5)](https://www.youtube.com/watch?v=zzeBpUXW4sM)

[9] [Building a Brainfuck Compiler using Cranelift | Clemens' Blog](https://blog.tiedt.dev/article/brainfuck_compiler)

[10] [Building a Brainfuck Compiler using Cranelift | Clemens' Blog](https://blog.tiedt.dev/article/brainfuck_compiler)

[11] [Building a Brainfuck Compiler using Cranelift | Clemens' Blog](https://blog.tiedt.dev/article/brainfuck_compiler)

[12] [Building a Brainfuck Compiler using Cranelift | Clemens' Blog](https://blog.tiedt.dev/article/brainfuck_compiler)

[13] [A primer on code generation in Cranelift by Benjamin Bouvier](https://bouvier.cc/cranelift-codegen-primer/)
