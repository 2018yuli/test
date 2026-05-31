<!-- Source: https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/cranelift/docs/testing.md -->
<!-- Title: Cranelift testing -->

# Testing Cranelift

# 测试 Cranelift

Cranelift is tested at multiple levels of abstraction and integration. When
possible, Rust unit tests are used to verify single functions and types. When
testing the interaction between compiler passes, file-level tests are
appropriate.

Cranelift 在多个抽象和集成层级上进行测试。在可能的情况下，会使用 Rust 单元测试来验证单个函数和类型。在测试编译器 pass 之间的交互时，文件级测试更为合适。

## Rust tests

## Rust 测试

Rust and Cargo have good support for testing. Cranelift uses unit tests, doc
tests, and integration tests where appropriate. The
[Rust By Example page on Testing] is a great illustration on how to write
each of these forms of test.

Rust 和 Cargo 对测试有良好的支持。Cranelift 会在适当的地方使用单元测试、文档测试和集成测试。[Rust By Example 的测试页面]很好地说明了如何编写这些形式的测试。

[Rust By Example page on Testing]: https://doc.rust-lang.org/rust-by-example/testing.html

## File tests

## 文件测试

Compilers work with large data structures representing programs, and it quickly
gets unwieldy to generate test data programmatically. File-level tests make it
easier to provide substantial input functions for the compiler tests.

编译器会处理表示程序的大型数据结构，而以编程方式生成测试数据很快会变得难以管理。文件级测试使得为编译器测试提供大量输入函数更加容易。

File tests are `*.clif` files in the `filetests/` directory
hierarchy. Each file has a header describing what to test followed by a number
of input functions in the :doc:`Cranelift textual intermediate representation
<ir>`:

文件测试是位于 `filetests/` 目录层级中的 `*.clif` 文件。每个文件都有一个头部，用于描述要测试的内容，后面跟着若干使用 :doc:`Cranelift 文本中间表示
<ir>` 编写的输入函数：

.. productionlist::
    test_file     : test_header `function_list`
    test_header   : test_commands (`isa_specs` | `settings`)
    test_commands : test_command { test_command }
    test_command  : "test" test_name { option } "\n"

.. productionlist::
    test_file     : test_header `function_list`
    test_header   : test_commands (`isa_specs` | `settings`)
    test_commands : test_command { test_command }
    test_command  : "test" test_name { option } "\n"

The available test commands are described below.

可用的测试命令如下所述。

Many test commands only make sense in the context of a target instruction set
architecture. These tests require one or more ISA specifications in the test
header:

许多测试命令只有在目标指令集架构的上下文中才有意义。这些测试要求在测试头部中包含一个或多个 ISA 规范：

.. productionlist::
    isa_specs     : { [`settings`] isa_spec }
    isa_spec      : "isa" isa_name { `option` } "\n"

.. productionlist::
    isa_specs     : { [`settings`] isa_spec }
    isa_spec      : "isa" isa_name { `option` } "\n"

The options given on the `isa` line modify the ISA-specific settings defined in
`cranelift-codegen/meta-python/isa/*/settings.py`.

`isa` 行上给出的选项会修改 `cranelift-codegen/meta-python/isa/*/settings.py` 中定义的 ISA 特定设置。

All types of tests allow shared Cranelift settings to be modified:

所有类型的测试都允许修改共享的 Cranelift 设置：

.. productionlist::
    settings      : { setting }
    setting       : "set" { option } "\n"
    option        : flag | setting "=" value

.. productionlist::
    settings      : { setting }
    setting       : "set" { option } "\n"
    option        : flag | setting "=" value

The shared settings available for all target ISAs are defined in
`cranelift-codegen/meta-python/base/settings.py`.

适用于所有目标 ISA 的共享设置定义在 `cranelift-codegen/meta-python/base/settings.py` 中。

The `set` lines apply settings cumulatively:

`set` 行会以累积方式应用设置：

```
    test legalizer
    set opt_level=best
    set is_pic=1
    target riscv64
    set is_pic=0
    target riscv32 supports_m=false

    function %foo() {}
```

This example will run the legalizer test twice. Both runs will have
`opt_level=best`, but they will have different `is_pic` settings. The 32-bit
run will also have the RISC-V specific flag `supports_m` disabled.

此示例会运行 legalizer 测试两次。两次运行都将具有 `opt_level=best`，但它们的 `is_pic` 设置不同。32 位运行还会禁用 RISC-V 特定标志 `supports_m`。

The filetests are run automatically as part of `cargo test`, and they can
also be run manually with the `clif-util test` command.

filetests 会作为 `cargo test` 的一部分自动运行，也可以使用 `clif-util test` 命令手动运行。

By default, the test runner will spawn a thread pool with as many threads as
there are logical CPUs. You can explicitly control how many threads are spawned
via the `CRANELIFT_FILETESTS_THREADS` environment variable. For example, to
limit the test runner to a single thread, use:

默认情况下，测试运行器会生成一个线程池，其线程数与逻辑 CPU 数量相同。你可以通过 `CRANELIFT_FILETESTS_THREADS` 环境变量显式控制生成的线程数。例如，要将测试运行器限制为单个线程，请使用：

```
$ CRANELIFT_FILETESTS_THREADS=1 clif-util test path/to/file.clif
```

### Filecheck

### Filecheck

Many of the test commands described below use *filecheck* to verify their
output. Filecheck is a Rust implementation of the LLVM tool of the same name.
See the `documentation <https://docs.rs/filecheck/>`_ for details of its syntax.

下面描述的许多测试命令都使用 *filecheck* 来验证其输出。Filecheck 是同名 LLVM 工具的 Rust 实现。有关其语法的详细信息，请参阅 `文档 <https://docs.rs/filecheck/>`_。

Comments in `.clif` files are associated with the entity they follow.
This typically means an instruction or the whole function. Those tests that
use filecheck will extract comments associated with each function (or its
entities) and scan them for filecheck directives. The test output for each
function is then matched against the filecheck directives for that function.

`.clif` 文件中的注释会与其后面的实体相关联。
这通常意味着一条指令或整个函数。那些使用 filecheck 的测试会提取与每个函数（或其实体）相关联的注释，并扫描其中的 filecheck 指令。然后，将每个函数的测试输出与该函数的 filecheck 指令进行匹配。

Comments appearing before the first function in a file apply to every function.
This is useful for defining common regular expression variables with the
`regex:` directive, for example.

出现在文件中第一个函数之前的注释会应用于每个函数。
这对于使用 `regex:` 指令定义通用的正则表达式变量很有用，例如。

Note that LLVM's file tests don't separate filecheck directives by their
associated function. It verifies the concatenated output against all filecheck
directives in the test file. LLVM's :command:`FileCheck` command has a
`CHECK-LABEL:` directive to help separate the output from different functions.
Cranelift's tests don't need this.

请注意，LLVM 的文件测试不会按其关联的函数来分隔 filecheck 指令。它会将连接后的输出与测试文件中的所有 filecheck 指令进行验证。LLVM 的 :command:`FileCheck` 命令有一个 `CHECK-LABEL:` 指令，用于帮助分隔不同函数的输出。Cranelift 的测试不需要这样。

### `test cat`

### `test cat`

This is one of the simplest file tests, used for testing the conversion to and
from textual IR. The `test cat` command simply parses each function and
converts it back to text again. The text of each function is then matched
against the associated filecheck directives.

这是最简单的文件测试之一，用于测试与文本 IR 之间的转换。`test cat` 命令会简单地解析每个函数，然后再将其转换回文本。随后，每个函数的文本会与关联的 filecheck 指令进行匹配。

Example:

示例：

```
    function %r1() -> i32, f32 {
    block1:
        v10 = iconst.i32 3
        v20 = f32const 0.0
        return v10, v20
    }
    ; sameln: function %r1() -> i32, f32 {
    ; nextln: block0:
    ; nextln:     v10 = iconst.i32 3
    ; nextln:     v20 = f32const 0.0
    ; nextln:     return v10, v20
    ; nextln: }
```

### `test verifier`

### `test verifier`

Run each function through the IR verifier and check that it produces the
expected error messages.

将每个函数通过 IR 验证器，并检查它是否产生预期的错误消息。

Expected error messages are indicated with an `error:` directive *on the
instruction that produces the verifier error*. Both the error message and
reported location of the error is verified:

预期的错误消息通过位于*产生验证器错误的指令上*的 `error:` 指令来标示。错误消息和报告的错误位置都会被验证：

```
    test verifier

    function %test(i32) {
        block0(v0: i32):
            jump block1       ; error: terminator
            return
    }
```

This example test passes if the verifier fails with an error message containing
the sub-string `"terminator"` *and* the error is reported for the `jump`
instruction.

如果验证器失败，并返回的错误消息包含子串 `"terminator"`，*并且* 错误被报告在 `jump` 指令上，那么这个示例测试就会通过。

If a function contains no `error:` annotations, the test passes if the
function verifies correctly.

如果函数不包含任何 `error:` 注解，只要函数能够正确通过验证，测试就会通过。

### `test print-cfg`

### `test print-cfg`

Print the control flow graph of each function as a Graphviz graph, and run
filecheck over the result. See also the :command:`clif-util print-cfg`
command:

将每个函数的控制流图打印为 Graphviz 图，并对结果运行 filecheck。另请参见 :command:`clif-util print-cfg` 命令：

```
    ; For testing cfg generation. This code is nonsense.
    test print-cfg
    test verifier

    function %nonsense(i32, i32) -> f32 {
    ; check: digraph %nonsense {
    ; regex: I=\binst\d+\b
    ; check: label="{block0 | <$(BRIF=$I)>brif v1, block1(v2), block2 }"]

    block0(v0: i32, v1: i32):
        v2 = iconst.i32 0
        brif v1, block1(v2), block2  ; unordered: block0:$BRIF -> block1
                                     ; unordered: block0:$BRIF -> block2

    block1(v5: i32):
        return v0

    block2:
        v100 = f32const 0.0
        return v100
    }
```

### `test domtree`

### `test domtree`

Compute the dominator tree of each function and validate it against the
`dominates:` annotations::

计算每个函数的支配树，并根据 `dominates:` 注解对其进行验证::

```
    test domtree

    function %test(i32) {
        block0(v0: i32):
            jump block1              ; dominates: block1
        block1:
            brif v0, block2, block3  ; dominates: block2, block3
        block2:
            jump block3
        block3:
            return
    }
```

Every reachable basic block except for the entry block has an
*immediate dominator* which is a jump or branch instruction. This test passes
if the `dominates:` annotations on the immediate dominator instructions are
both correct and complete.

除了入口块之外，每个可达的基本块都有一个*直接支配者*，它是一条 jump 或 branch 指令。如果直接支配者指令上的 `dominates:` 注解既正确又完整，这个测试就会通过。

This test also sends the computed CFG post-order through filecheck.

此测试还会将计算得到的 CFG 后序遍历结果送入 filecheck。

### `test legalizer`

### `test legalizer`

Legalize each function for the specified target ISA and run the resulting
function through filecheck. This test command can be used to validate the
encodings selected for legal instructions as well as the instruction
transformations performed by the legalizer.

针对指定的目标 ISA 对每个函数进行合法化，并将生成的函数通过 filecheck 运行。此测试命令可用于验证为合法指令选择的编码，以及 legalizer 执行的指令转换。

### `test regalloc`

### `test regalloc`

Test the register allocator.

测试寄存器分配器。

First, each function is legalized for the specified target ISA. This is
required for register allocation since the instruction encodings provide
register class constraints to the register allocator.

首先，针对指定的目标 ISA 对每个函数进行合法化。这是寄存器分配所必需的，因为指令编码会向寄存器分配器提供寄存器类别约束。

Second, the register allocator is run on the function, inserting spill code and
assigning registers and stack slots to all values.

其次，在函数上运行寄存器分配器，插入溢出代码，并为所有值分配寄存器和栈槽。

The resulting function is then run through filecheck.

然后将得到的函数通过 filecheck 运行。

### `test simple-gvn`

### `test simple-gvn`

Test the simple GVN pass.

测试 simple GVN pass。

The simple GVN pass is run on each function, and then results are run
through filecheck.

simple GVN pass 会在每个函数上运行，然后结果会通过 filecheck 运行。

### `test licm`

### `test licm`

Test the LICM pass.

测试 LICM pass。

The LICM pass is run on each function, and then results are run
through filecheck.

LICM pass 会在每个函数上运行，然后结果会通过 filecheck 运行。

### `test dce`

### `test dce`

Test the DCE pass.

测试 DCE pass。

The DCE pass is run on each function, and then results are run
through filecheck.

DCE pass 会在每个函数上运行，然后结果会通过 filecheck 运行。

### `test shrink`

### `test shrink`

Test the instruction shrinking pass.

测试指令缩减 pass。

The shrink pass is run on each function, and then results are run
through filecheck.

shrink pass 会在每个函数上运行，然后结果会通过 filecheck 运行。

### `test simple_preopt`

### `test simple_preopt`

Test the preopt pass.

测试 preopt pass。

The preopt pass is run on each function, and then results are run
through filecheck.

preopt pass 会在每个函数上运行，然后结果会通过 filecheck 运行。

### `test compile`

### `test compile`

Test the whole code generation pipeline.

测试整个代码生成流水线。

Each function is passed through the full `Context::compile()` function
which is normally used to compile code. This type of test often depends
on assertions or verifier errors, but it is also possible to use
filecheck directives which will be matched against the final form of the
Cranelift IR right before binary machine code emission.

每个函数都会通过完整的 `Context::compile()` 函数处理，该函数通常用于编译代码。这类测试通常依赖断言或验证器错误，但也可以使用 filecheck 指令；这些指令会与二进制机器码发射之前 Cranelift IR 的最终形式进行匹配。

### `test run`

### `test run`

Compile and execute a function.

编译并执行一个函数。

This test command allows several directives:
 - to print the result of running a function to stdout, add a `print`
 directive and call the preceding function with arguments (see `%foo` in
 the example below); remember to enable `--nocapture` if running these
 tests through Cargo
 - to check the result of a function, add a `run` directive and call the
 preceding function with a comparison (`==` or `!=`) (see `%bar` below)
 - for backwards compatibility, to check the result of a function with a
 `() -> i*` signature, only the `run` directive is required, with no
 invocation or comparison (see `%baz` below);  a non zero value is
 interpreted as a successful test execution, whereas a zero value is
 interpreted as a failed test.

此测试命令允许使用若干指令：
 - 若要将运行函数的结果打印到 stdout，请添加一个 `print`
 指令，并使用参数调用前面的函数（参见下面示例中的 `%foo`）；如果通过 Cargo 运行这些
 测试，请记得启用 `--nocapture`
 - 若要检查函数的结果，请添加一个 `run` 指令，并使用比较（`==` 或 `!=`）调用
 前面的函数（参见下面的 `%bar`）
 - 为了向后兼容，若要检查具有 `() -> i*` 签名的函数结果，只需要 `run` 指令，
 无需调用或比较（参见下面的 `%baz`）；非零值会被解释为测试执行成功，
 而零值会被解释为测试失败。

Currently a `target` is required but is only used to indicate whether the host
platform can run the test and currently only the architecture is filtered. The
host platform's native target will be used to actually compile the test.

目前需要一个 `target`，但它仅用于指示宿主平台是否可以运行该测试，并且目前只过滤架构。实际编译该测试时将使用宿主平台的原生 target。

Example:

示例：

```
    test run
    target x86_64

    ; how to print the results of a function
    function %foo() -> i32 {
    block0:
        v0 = iconst.i32 42
        return v0
    }
    ; print: %foo()

    ; how to check the results of a function
    function %bar(i32) -> i32 {
    block0(v0:i32):
        v1 = iadd_imm v0, 1
        return v1
    }
    ; run: %bar(1) == 2

    ; legacy method of checking the results of a function
    function %baz() -> i8 {
    block0:
        v0 = iconst.i8 1
        return v0
    }
    ; run
```
