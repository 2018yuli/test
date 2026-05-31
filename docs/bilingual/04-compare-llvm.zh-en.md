<!-- Source: https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/cranelift/docs/compare-llvm.md -->
<!-- Title: Comparison with LLVM -->

# Cranelift compared to LLVM

# Cranelift 与 LLVM 的比较

[LLVM](https://llvm.org) is a collection of compiler components implemented as
a set of C++ libraries. It can be used to build both JIT compilers and static
compilers like [Clang](https://clang.llvm.org), and it is deservedly very
popular.
[Chris Lattner's chapter about LLVM](https://www.aosabook.org/en/llvm.html)
in the 
[Architecture of Open Source Applications](https://aosabook.org/en/index.html)
book gives an excellent overview of the architecture and design of LLVM.

[LLVM](https://llvm.org) 是一组以一系列 C++ 库实现的编译器组件。它既可用于构建 JIT 编译器，也可用于构建像 [Clang](https://clang.llvm.org) 这样的静态编译器，而且它理所当然地非常受欢迎。[Chris Lattner 关于 LLVM 的章节](https://www.aosabook.org/en/llvm.html) 在 [开源应用架构](https://aosabook.org/en/index.html) 一书中对 LLVM 的架构和设计做了极好的概述。

Cranelift and LLVM are superficially similar projects, so it is worth
highlighting some of the differences and similarities. Both projects:

Cranelift 和 LLVM 在表面上看起来很相似，因此值得强调一些差异和相似之处。两个项目都：

- Use a mostly-ISA-agnostic input language in order to mostly abstract away the
  differences between target instruction set architectures.
- Depend extensively on SSA form.
- Have both textual and in-memory forms of their primary intermediate
  representation. (LLVM also has a binary bitcode format; Cranelift doesn't.)
- Can target multiple ISAs.
- Can cross-compile by default without rebuilding the code generator.

- 使用一种大体上与 ISA 无关的输入语言，以尽量抽象掉不同目标指令集架构之间的差异。
- 大量依赖 SSA 形式。
- 其主要中间表示既有文本形式，也有内存形式。（LLVM 还有一种二进制 bitcode 格式；Cranelift 没有。）
- 可以面向多个 ISA。
- 默认支持交叉编译，无需重新构建代码生成器。

However, there are also some major differences, described in the following sections.

不过，它们也存在一些重大差异，下面各节将加以说明。

## Intermediate representations

## 中间表示

LLVM uses multiple intermediate representations as it translates a program to
binary machine code:

LLVM 在将程序翻译为二进制机器码时使用多个中间表示：

[LLVM IR](https://llvm.org/docs/LangRef.html):
    This is the primary intermediate representation which has textual, binary, and
    in-memory forms. It serves two main purposes:

[LLVM IR](https://llvm.org/docs/LangRef.html):
    这是主要的中间表示，具有文本、二进制和内存三种形式。它有两个主要用途：

    - An ISA-agnostic, stable(ish) input language that front ends can generate
      easily.
    - Intermediate representation for common mid-level optimizations. A large
      library of code analysis and transformation passes operate on LLVM IR.

- 一种与 ISA 无关、相对稳定的输入语言，前端可以很容易地生成它。
    - 用于通用中层优化的中间表示。大量代码分析和转换 pass 在 LLVM IR 上运行。

[SelectionDAG](https://llvm.org/docs/CodeGenerator.html#instruction-selection-section):
    A graph-based representation of the code in a single basic block is used by
    the instruction selector. It has both ISA-agnostic and ISA-specific
    opcodes. These main passes are run on the SelectionDAG representation:

[SelectionDAG](https://llvm.org/docs/CodeGenerator.html#instruction-selection-section):
    指令选择器使用一种基于图的表示来表示单个基本块中的代码。它既有与 ISA 无关的操作码，也有 ISA 特定的操作码。以下主要 pass 在 SelectionDAG 表示上运行：

    - Type legalization eliminates all value types that don't have a
      representation in the target ISA registers.
    - Operation legalization eliminates all opcodes that can't be mapped to
      target ISA instructions.
    - DAG-combine cleans up redundant code after the legalization passes.
    - Instruction selection translates ISA-agnostic expressions to ISA-specific
      instructions.

- 类型合法化会消除所有在目标 ISA 寄存器中没有表示形式的值类型。
    - 操作合法化会消除所有无法映射到目标 ISA 指令的操作码。
    - DAG-combine 会在合法化 pass 之后清理冗余代码。
    - 指令选择将与 ISA 无关的表达式转换为与 ISA 相关的指令。

    The SelectionDAG representation automatically eliminates common
    subexpressions and dead code.

SelectionDAG 表示会自动消除公共子表达式和死代码。

[MachineInstr](https://llvm.org/docs/CodeGenerator.html#machine-code-representation):
    A linear representation of ISA-specific instructions that initially is in
    SSA form, but it can also represent non-SSA form during and after register
    allocation. Many low-level optimizations run on MI code. The most important
    passes are:

[MachineInstr](https://llvm.org/docs/CodeGenerator.html#machine-code-representation):
    一种 ISA 特定指令的线性表示，最初处于 SSA 形式，但在寄存器分配期间和之后也可以表示非 SSA 形式。许多底层优化在 MI 代码上运行。最重要的 pass 有：

    - Scheduling.
    - Register allocation.

- 调度。
    - 寄存器分配。

[MC](https://llvm.org/docs/CodeGenerator.html#the-mc-layer)
    MC serves as the output abstraction layer and is the basis for LLVM's
    integrated assembler. It is used for:

[MC](https://llvm.org/docs/CodeGenerator.html#the-mc-layer)
    MC 充当输出抽象层，并且是 LLVM 集成汇编器的基础。它用于：

    - Branch relaxation.
    - Emitting assembly or binary object code.
    - Assemblers.
    - Disassemblers.

- 分支松弛。
    - 发出汇编或二进制目标代码。
    - 汇编器。
    - 反汇编器。

There is an ongoing "global instruction selection" project to replace the
SelectionDAG representation with ISA-agnostic opcodes on the MachineInstr
representation. Some target ISAs have a fast instruction selector that can
translate simple code directly to MachineInstrs, bypassing SelectionDAG when
possible.

目前有一个正在进行的“全局指令选择”项目，旨在用 MachineInstr 表示中的 ISA 无关操作码来取代 SelectionDAG 表示。一些目标 ISA 拥有快速指令选择器，可以在可能时绕过 SelectionDAG，将简单代码直接转换为 MachineInstr。

[Cranelift IR](ir.md) uses a single intermediate representation to cover
these levels of abstraction. This is possible in part because of Cranelift's
smaller scope.

[Cranelift IR](ir.md) 使用单一中间表示来覆盖这些抽象层级。这在一定程度上是因为 Cranelift 的范围较小。

- Cranelift does not provide assemblers and disassemblers, so it is not
  necessary to be able to represent every weird instruction in an ISA. Only
  those instructions that the code generator emits have a representation.
- Cranelift's opcodes are ISA-agnostic, but after legalization / instruction
  selection, each instruction is annotated with an ISA-specific encoding which
  represents a native instruction.
- SSA form is preserved throughout. After register allocation, each SSA value
  is annotated with an assigned ISA register or stack slot.

- Cranelift 不提供汇编器和反汇编器，因此无需能够表示 ISA 中的每一条奇怪指令。只有代码生成器会发出的那些指令才有表示。
- Cranelift 的操作码是 ISA 无关的，但在合法化 / 指令选择之后，每条指令都会带有一个 ISA 特定编码的注解，该编码表示一条原生指令。
- SSA 形式会全程保留。寄存器分配之后，每个 SSA 值都会带有一个已分配的 ISA 寄存器或栈槽的注解。

The Cranelift intermediate representation is similar to LLVM IR, but at a slightly
lower level of abstraction, to allow it to be used all the way through the
codegen process.

Cranelift 中间表示类似于 LLVM IR，但抽象层级略低，以便它能够贯穿整个代码生成过程使用。

This design tradeoff does mean that Cranelift IR is less friendly for mid-level
optimizations. Cranelift doesn't currently perform mid-level optimizations,
however if it should grow to where this becomes important, the vision is that
Cranelift would add a separate IR layer, or possibly an separate IR, to support
this. Instead of frontends producing optimizer IR which is then translated to
codegen IR, Cranelift would have frontends producing codegen IR, which can be
translated to optimizer IR and back.

这种设计取舍确实意味着 Cranelift IR 对中层优化不太友好。Cranelift 目前不执行中层优化；不过，如果它发展到这一点变得重要的程度，设想是 Cranelift 会添加一个单独的 IR 层，或者可能是一个单独的 IR，来支持它。Cranelift 不会让前端生成优化器 IR，然后再将其转换为代码生成 IR；而是让前端生成代码生成 IR，该 IR 可以转换为优化器 IR，然后再转换回来。

This biases the overall system towards fast compilation when mid-level
optimization is not needed, such as when emitting unoptimized code for or when
low-level optimizations are sufficient.

这使整个系统在不需要中层优化时偏向快速编译，例如在发出未优化代码时，或者在低层优化已经足够时。

And, it removes some constraints in the mid-level optimize IR design space,
making it more feasible to consider ideas such as using a
[VSDG-based IR](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-705.pdf).

并且，它移除了中层优化 IR 设计空间中的一些约束，使得考虑诸如使用基于 [VSDG 的 IR](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-705.pdf) 之类的想法更加可行。

### Program structure

### 程序结构

In LLVM IR, the largest representable unit is the *module* which corresponds
more or less to a C translation unit. It is a collection of functions and
global variables that may contain references to external symbols too.

在 LLVM IR 中，最大的可表示单元是 *module*，它大致对应于一个 C 翻译单元。它是函数和全局变量的集合，也可能包含对外部符号的引用。

In [Cranelift's IR](ir.md)
used by the [cranelift-codegen](https://docs.rs/cranelift-codegen/) crate,
functions are self-contained, allowing them to be compiled independently. At
this level, there is no explicit module that contains the functions.

在 [cranelift-codegen](https://docs.rs/cranelift-codegen/) crate 使用的 [Cranelift 的 IR](ir.md) 中，函数是自包含的，因此可以独立编译。在这个层级上，不存在包含这些函数的显式模块。

Module functionality in Cranelift is provided as an optional library layer, in
the [cranelift-module](https://docs.rs/cranelift-module/) crate. It provides
facilities for working with modules, which can contain multiple functions as
well as data objects, and it links them together.

Cranelift 中的模块功能作为可选的库层提供，位于
[cranelift-module](https://docs.rs/cranelift-module/) crate 中。它提供了用于处理模块的设施；模块可以包含多个函数以及数据对象，并将它们链接在一起。

Both LLVM and Cranelift use a graph of *basic blocks* as their IR for functions.
However, LLVM uses
[phi instructions](https://llvm.org/docs/LangRef.html#phi-instruction) in its
SSA representation while Cranelift passes arguments to BBs instead. The two
representations are equivalent, but the BB arguments are better suited to handle
BBs that may contain multiple branches to the same destination block with
different arguments. Passing arguments to a BB looks a lot like passing
arguments to a function call, and the register allocator treats them very
similarly. Arguments are assigned to registers or stack locations.

LLVM 和 Cranelift 都使用*基本块*图作为函数的 IR。
不过，LLVM 在其 SSA 表示中使用
[phi 指令](https://llvm.org/docs/LangRef.html#phi-instruction)，而 Cranelift 则改为向基本块传递参数。这两种表示是等价的，但基本块参数更适合处理可能包含多个分支到同一目标块且参数不同的基本块。向基本块传递参数看起来很像向函数调用传递参数，寄存器分配器也以非常相似的方式处理它们。参数会被分配到寄存器或栈位置。

### Value types

### 值类型

[Cranelift's type system](ir.md#value-types) is mostly a subset of LLVM's type
system. It is less abstract and closer to the types that common ISA registers
can hold.

[Cranelift 的类型系统](ir.md#value-types)大体上是 LLVM 类型系统的一个子集。它抽象程度较低，更接近常见 ISA 寄存器能够保存的类型。

- Integer types are limited to powers of two from `i8` to
  `i64`. LLVM can represent integer types of arbitrary bit width.
- Floating point types are limited to `f32` and `f64`
  which is what WebAssembly provides. It is possible that 16-bit and 128-bit
  types will be added in the future.
- Addresses are represented as integers---There are no Cranelift pointer types.
  LLVM currently has rich pointer types that include the pointee type. It may
  move to a simpler 'address' type in the future. Cranelift may add a single
  address type too.
- SIMD vector types are limited to a power-of-two number of vector lanes up to
  256. LLVM allows an arbitrary number of SIMD lanes.
- Cranelift has no aggregate types. LLVM has named and anonymous struct types as
  well as array types.

- 整数类型限制为从 `i8` 到
  `i64` 的 2 的幂。LLVM 可以表示任意位宽的整数类型。
- 浮点类型限制为 `f32` 和 `f64`，
  这也是 WebAssembly 提供的类型。未来可能会添加 16 位和 128 位
  类型。
- 地址表示为整数——Cranelift 中没有指针类型。
  LLVM 目前具有丰富的指针类型，其中包含被指向对象的类型。它未来可能会
  转向更简单的“地址”类型。Cranelift 也可能添加单一的
  地址类型。
- SIMD 向量类型限制为向量 lane 数量为 2 的幂，最多
  256 个。LLVM 允许任意数量的 SIMD lane。
- Cranelift 没有聚合类型。LLVM 有具名和匿名结构体类型，
  以及数组类型。

Cranelift uses integer-typed values of `0` or `1` for booleans, whereas LLVM
simply uses `i1`. The sized Cranelift integer types are used to represent SIMD
vector masks like `i32x4` where each lane is either all 0 or all 1 bits.

Cranelift 使用类型为整数的 `0` 或 `1` 值来表示布尔值，而 LLVM
则直接使用 `i1`。定宽的 Cranelift 整数类型用于表示 SIMD
向量掩码，例如 `i32x4`，其中每个 lane 要么全为 0 位，要么全为 1 位。

Cranelift instructions and function calls can return multiple result values. LLVM
instead models this by returning a single value of an aggregate type.

Cranelift 指令和函数调用可以返回多个结果值。LLVM
则通过返回聚合类型的单个值来建模这一点。

### Instruction set

### 指令集

LLVM has a small well-defined basic instruction set and a large number of
intrinsics, some of which are ISA-specific. Cranelift has a larger instruction
set and no intrinsics. Some Cranelift instructions are ISA-specific.

LLVM 有一个小型且定义明确的基本指令集，以及大量
intrinsics，其中一些是 ISA 特定的。Cranelift 有更大的指令
集，并且没有 intrinsics。一些 Cranelift 指令是 ISA 特定的。

Since Cranelift instructions are used all the way until the binary machine code
is emitted, there are opcodes for every native instruction that can be
generated. There is a lot of overlap between different ISAs, so for example the
`iadd_imm` instruction is used by every ISA that can add an
immediate integer to a register. A simple RISC ISA like RISC-V can be defined
with only shared instructions, while x86 needs a number of specific
instructions to model addressing modes.

由于 Cranelift 指令会一直使用到二进制机器码被发出，因此对于每一条可能生成的原生指令都有对应的 opcode。不同 ISA 之间有很多重叠，因此例如
`iadd_imm` 指令会被每个能够将立即数整数加到寄存器上的 ISA 使用。像 RISC-V 这样的简单 RISC ISA 可以只用共享指令来定义，而 x86 则需要一些特定
指令来建模寻址模式。
