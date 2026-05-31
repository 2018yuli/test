<!-- Source: https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/cranelift/isle/docs/language-reference.md -->
<!-- Title: ISLE language reference -->

# ISLE: Instruction Selection Lowering Expressions

# ISLE：指令选择降低表达式

This document will describe ISLE (Instruction Selection Lowering
Expressions), a DSL (domain-specific language) that we have developed
in order to help us express certain parts of the Cranelift compiler
backend more naturally. ISLE was first [described in RFC
#15](https://github.com/bytecodealliance/rfcs/pull/15) and now is used
by and lives in the Cranelift tree in
[cranelift/isle](https://github.com/bytecodealliance/wasmtime/tree/main/cranelift/isle).

本文档将介绍 ISLE（Instruction Selection Lowering
Expressions，指令选择降低表达式），这是一种 DSL（领域特定语言），我们开发它是为了帮助我们更自然地表达 Cranelift 编译器后端的某些部分。ISLE 最早在 [RFC
#15](https://github.com/bytecodealliance/rfcs/pull/15) 中被描述，现在由 Cranelift 使用，并位于 Cranelift 源码树的
[cranelift/isle](https://github.com/bytecodealliance/wasmtime/tree/main/cranelift/isle) 中。

Documentation on how ISLE is used in Cranelift can be found
[here](../../docs/isle-integration.md).

关于 ISLE 如何在 Cranelift 中使用的文档可在
[这里](../../docs/isle-integration.md) 找到。

## Intro and Whirlwind Tour: DSL for Instruction Lowering

## 简介与快速导览：用于指令降低的 DSL

The goal of ISLE is to represent *instruction lowering patterns*. An
instruction lowering pattern is a specification that a certain
combination of operators in the IR (CLIF), when combined under certain
conditions, can be compiled down into a certain sequence of machine
instructions. For example:

ISLE 的目标是表示*指令降低模式*。指令降低模式是一种规范，说明 IR（CLIF）中的某些运算符组合在满足特定条件时，可以被编译降低为某个机器指令序列。例如：

- An `iadd` (integer add) operator can always be lowered to an x86
  `ADD` instruction with two register sources.

- 一个 `iadd`（整数加法）运算符总是可以降低为带有两个寄存器源操作数的 x86
  `ADD` 指令。

- An `iadd` operator with one `iconst` (integer-constant) argument can
  be lowered to an x86 `ADD` instruction with a register and an
  immediate.

- 一个带有一个 `iconst`（整数常量）参数的 `iadd` 运算符可以降低为带有一个寄存器和一个立即数的 x86 `ADD` 指令。

One could write something like the following in ISLE (simplified from
the real code [here](https://github.com/bytecodealliance/wasmtime/blob/main/cranelift/codegen/src/isa/x64/lower.isle)):

可以在 ISLE 中写出类似下面的内容（从真实代码[这里](https://github.com/bytecodealliance/wasmtime/blob/main/cranelift/codegen/src/isa/x64/lower.isle)简化而来）：

```lisp
;; Add two registers.
(rule (lower (iadd x y))
      (value_reg (add
                   (put_in_reg x)
                   (RegMemImm.Reg (put_in_reg y)))))

;; Add a register and an immediate.
(rule (lower (iadd x (simm32_from_value y))
      (value_reg (add
                   (put_in_reg x)
                   ;; `y` is a `RegMemImm.Imm`.
                   y))))
```

ISLE lets the compiler backend developer express this information in a
declarative way -- i.e., just write down a list of patterns, without
worrying how the compilation process tries them out -- and the ISLE
DSL compiler will convert this list of patterns into efficient Rust
code that becomes part of Cranelift.

ISLE 让编译器后端开发者能够以声明式方式表达这些信息——也就是说，只需写下一组模式，而无需担心编译过程如何尝试它们——然后 ISLE
DSL 编译器会将这组模式转换为高效的 Rust 代码，并成为 Cranelift 的一部分。

The rest of this document will describe the semantics of the DSL
itself. ISLE has been designed to be a general-purpose DSL that can
apply to any sort of backtracking pattern-matching problem, and will
generate a decision tree in Rust that can call into arbitrary
interface code.

本文档的其余部分将描述该 DSL 本身的语义。ISLE 被设计为一种通用 DSL，可应用于任何形式的回溯模式匹配问题，并会在 Rust 中生成一棵决策树，该决策树可以调用任意接口代码。

Separate documentation will describe how we have written *bindings*
and *helpers* to allow ISLE to be specifically used to write Cranelift
lowering patterns like the above. (TODO: link this documentation)

单独的文档将描述我们如何编写*绑定*和*辅助函数*，以允许 ISLE 专门用于编写类似上述的 Cranelift 降低模式。（TODO：链接此文档）

## Outline of This Document

## 本文档大纲

This document is organized into the following sections:

本文档组织为以下几个部分：

* Term-Rewriting Systems: a general overview of how term-rewriting
  systems work, how to think about nested terms, patterns and rewrite
  rules, how they provide a general mechanism for computation, and how
  term-rewriting is often used in a compiler-implementation context.

* 项重写系统：对项重写系统如何工作的一般概述，包括如何理解嵌套项、模式和重写规则，它们如何提供一种通用的计算机制，以及项重写在编译器实现上下文中通常如何使用。

* Core ISLE: the foundational concepts of the ISLE DSL, building upon
  a general-purpose term-rewriting base. Covers the type system (typed
  terms) and how rules are written.

* 核心 ISLE：ISLE DSL 的基础概念，建立在通用项重写基础之上。涵盖类型系统（带类型的项）以及规则的编写方式。

* ISLE with Rust: covers how ISLE provides an "FFI" (foreign function
  interface) of sorts to allow interaction with Rust code, and
  describes the scheme by which ISLE execution is mapped onto Rust
  (data structures and control flow).[^1]

* 带 Rust 的 ISLE：介绍 ISLE 如何提供某种形式的 “FFI”（foreign function
  interface，外部函数接口）以允许与 Rust 代码交互，并描述 ISLE 执行映射到 Rust（数据结构和控制流）的方案。[^1]

* ISLE Internals: describes how the ISLE compiler works. Provides
  insight into how an unordered collection of rewrite rules are
  combined into executable Rust code that efficiently traverses the
  input and matches on it.

* ISLE 内部机制：描述 ISLE 编译器的工作方式。提供有关无序的重写规则集合如何被组合成可执行的 Rust 代码的洞见，这些代码能够高效地遍历输入并对其进行匹配。

[^1]: One might call this the BRIDGE (Basic Rust Interface Designed
    for Good Efficiency) to the ISLE, but unfortunately we missed the
    chance to introduce that backronym when we wrote the initial
    implementation.

[^1]: 有人可能会把这称为通往 ISLE 的 BRIDGE（Basic Rust Interface Designed
    for Good Efficiency），但遗憾的是，当我们编写最初实现时，错过了引入这个逆向首字母缩略词的机会。

## Background: Term-Rewriting Systems

## 背景：项重写系统

*Note: this section provides general background on term-rewriting
systems that is useful to better understand the context for ISLE and
how to develop systems using it. Readers already familiar with
term-rewriting systems, or wishing to skip to details on ISLE's
version of term rewriting, can skip to the [next
section](#core-isle-a-term-rewriting-system).*

*注意：本节提供关于项重写系统的一般背景知识，有助于更好地理解 ISLE 的上下文以及如何使用它开发系统。已经熟悉项重写系统的读者，或希望直接跳到 ISLE 版本项重写细节的读者，可以跳到[下一节](#core-isle-a-term-rewriting-system)。*

A [term-rewriting
system](https://en.wikipedia.org/wiki/Rewriting#Term_rewriting_systems),
or TRS, is a system that works by representing data as *terms* and
then applying *rules* to "rewrite" the terms. This rewrite process
continues until some application-specific end-condition is met, for
example until no more rules are applicable or until the term reaches a
"lowered" state by some definition, at which point the resulting term
is the system's output.

[项重写系统](https://en.wikipedia.org/wiki/Rewriting#Term_rewriting_systems)，或称 TRS，是一种通过将数据表示为*项*，然后应用*规则*来“重写”这些项的系统。这个重写过程会持续进行，直到满足某个特定于应用的结束条件，例如直到没有更多规则可适用，或直到该项按照某种定义达到“降低”状态，此时得到的项就是系统的输出。

Term-rewriting systems are a general kind of computing system, at the
same level as (e.g.) Turing machines or other abstract computing
machines. Term-rewriting is actually Turing-complete, or in other
words, can express any program, if no limits are placed on term length
or recursion.[^2]

项重写系统是一类通用的计算系统，与（例如）图灵机或其他抽象计算机器处于同一层次。项重写实际上是图灵完备的，换句话说，如果不对项长度或递归施加限制，它可以表达任何程序。[^2]

[^2]: In fact, the [lambda
      calculus](https://en.wikipedia.org/wiki/Lambda_calculus)
      introduced by Alonzo Church is actually a term-rewriting system
      and was developed at the same time as Turing's concepts of
      universal computation!

[^2]: 事实上，由 Alonzo Church 提出的 [lambda
      calculus](https://en.wikipedia.org/wiki/Lambda_calculus)
      实际上就是一种项重写系统，并且与 Turing 的通用计算概念是在同一时期发展起来的！

Why might one want to use a TRS rather than some other, more
conventional, way of computing an answer? One reason is that they are
highly applicable to *pattern-matching* problems: for example,
translating data in one domain to data in another domain, where the
translation consists of a bunch of specific equivalences. This is part
of why term-rewriting is so interesting in the compiler domain:
compiler backends work to lower certain patterns in the program (e.g.:
a multiply-add combination) into instructions that the target machine
provides (e.g.: a dedicated multiply-add instruction).

为什么人们可能想使用 TRS，而不是某种其他更传统的方式来计算答案？一个原因是它们非常适用于*模式匹配*问题：例如，将一个领域中的数据翻译为另一个领域中的数据，其中翻译由一组具体的等价关系组成。这也是项重写在编译器领域如此有趣的部分原因：编译器后端致力于将程序中的某些模式（例如：乘加组合）降低为目标机器提供的指令（例如：专用的乘加指令）。

Term rewriting as a process also naturally handles issues of
*priority*, i.e. applying a more specific rule before a less specific
one. This is because the abstraction allows for multiple rules to be
"applicable", and so there is a natural place to reason about priority
when we choose which rule to apply. This permits a nice separation of
concerns: we can specify which rewrites are *possible* to apply
separately from which are *desirable* to apply, and adjust or tune the
latter (the "strategy") at will without breaking the system's
correctness.

作为一个过程，项重写也自然地处理*优先级*问题，即在较不具体的规则之前应用更具体的规则。这是因为该抽象允许多个规则“适用”，因此当我们选择应用哪条规则时，就有了一个自然的位置来推理优先级。这允许一种很好的关注点分离：我们可以将哪些重写是*可能*应用的，与哪些重写是*值得*应用的分开指定，并且可以随意调整或调优后者（即“策略”），而不会破坏系统的正确性。

Additionally, term rewriting allows for a sort of *modularity* that is
not present in hand-written pattern-matching code: the specific rules
can be specified in any order, and the term-rewriting engine "weaves"
them together so that in any state, when we have partially matched the
input and are narrowing down which rule will apply, we consider all
the related rules at once. Said another way: hand-written code tends
to accumulate a lot of nested conditionals and switch/match
statements, i.e., resembles a very large decision tree, while
term-rewriting code tends to resemble a flat list of simple patterns
that, when composed and combined, become that more complex tree. This
allows the programmer to more easily maintain and update the set of
lowering rules, considering each in isolation.

此外，项重写允许某种手写模式匹配代码所不具备的*模块化*：具体规则可以按任意顺序指定，而项重写引擎会将它们“编织”在一起，使得在任何状态下，当我们已经部分匹配了输入并正在缩小将应用哪条规则的范围时，我们会同时考虑所有相关规则。换句话说：手写代码往往会积累大量嵌套条件和 switch/match 语句，也就是说，类似一棵非常大的决策树；而项重写代码往往类似一组扁平的简单模式列表，这些模式在组合与结合后会变成那棵更复杂的树。这使程序员能够更轻松地维护和更新 lowering 规则集，并能将每条规则单独考虑。

### Data: Nested Trees of Constructors

### 数据：构造子的嵌套树

A term-rewriting system typically operates on data that is in a *tree*
form, or at least can be interpreted that way.[^3]

项重写系统通常操作的是*树*形式的数据，或者至少是可以按这种方式解释的数据。[^3]

[^3]: In the most fundamental and mathematical sense, a TRS just
      operates on a sequence of symbols, but we can talk about
      structure that is present in those symbols in any well-formed
      sequence. For example, we can define a TRS that only operates on
      terms with balanced parentheses; then we have our tree.

[^3]: 从最基本和数学化的意义上说，TRS 只是操作一个符号序列，
      但我们可以讨论任何良构序列中这些符号所呈现的结构。
      例如，我们可以定义一个只操作括号平衡的项的 TRS；这样我们就有了树。

In ISLE and hence in this document, we operate on terms that are
written in an
[S-expression](https://en.wikipedia.org/wiki/S-expression) syntax,
borrowed from the Lisp world. So we might have a term:

在 ISLE 中，也因此在本文档中，我们操作的项使用
[S-expression](https://en.wikipedia.org/wiki/S-expression) 语法编写，
该语法借自 Lisp 世界。因此我们可能有一个项：

```lisp
    (a (b c 1 2) (d) (e 3 4))
```

which we can write more clearly as the tree:

我们可以将其更清晰地写成树：

```lisp
    (a
      (b
        c 1 2)
      (d)
      (e
        3 4))
```

Each term consists of either a *constructor* (which looks like a
function call to Lisp-trained eyes) or a *primitive*. In the above,
the `(a ...)`, `(b ...)`, `(d)`, and `(e ...)` terms/subterms are
constructor invocations. A constructor takes some number of arguments
(its *arity*), each of which is itself a term. Primitives can be
things like integer, string, or boolean constants, or variable names.

每个项要么由一个*构造子*组成（在熟悉 Lisp 的人看来像是函数调用），要么由一个*原语*组成。在上面的例子中，`(a ...)`、`(b ...)`、`(d)` 和 `(e ...)` 这些项/子项都是构造子调用。构造子接受若干个参数（其*元数*），每个参数本身也是一个项。原语可以是整数、字符串或布尔常量，或者变量名之类的东西。

Some term-rewriting systems have other syntax conventions: for
example, systems based on
[Prolog](https://en.wikipedia.org/wiki/Prolog) tend to write terms
like `a(b(c, 1, 2), d, e(3, 4))`, i.e., with the name of the term on
the outside of the parentheses. This is just a cosmetic difference to
the above, but we note it to make clear that the term structure is
important, not the syntax.

一些项重写系统有其他语法约定：例如，基于
[Prolog](https://en.wikipedia.org/wiki/Prolog) 的系统往往会把项写成
`a(b(c, 1, 2), d, e(3, 4))` 这样的形式，也就是说，把项的名称写在括号外面。这与上面的写法只是外观上的差异，但我们指出这一点，是为了明确重要的是项结构，而不是语法。

It may not be immediately clear how to use this data representation,
but we can give a small flavor here: if one defines *constructors* for
each instruction or operator in a compiler's intermediate
representation (IR), one can start to write expressions from that IR
as terms; for example:

可能不会立刻清楚如何使用这种数据表示，但我们可以在这里给出一个小例子：如果为编译器中间表示（IR）中的每条指令或每个运算符定义*构造子*，就可以开始把该 IR 中的表达式写成项；例如：

```lisp
    v1 = imul y, z
    v2 = iadd x, v1
```

could become:

可以变成：

```lisp
    (iadd x (imul y z))
```

This will become much more useful once we have rewrite rules to
perform transformations on the terms!

一旦我们有了用于对项执行转换的重写规则，这就会变得有用得多！

Representing an IR is, of course, just one possible use of term data
(albeit the original "MVP" that guided ISLE's design); there are many
others, too. Interested readers are encouraged to read more on, e.g.,
[Prolog](https://en.wikipedia.org/wiki/Prolog), which has been used to
represent logical predicates, "facts" in expert systems, symbolic
mathematical terms, and more.

表示一种 IR 当然只是项数据的一种可能用途
（尽管它是指导 ISLE 设计的最初 "MVP"）；此外还有许多
其他用途。鼓励感兴趣的读者进一步阅读，例如
[Prolog](https://en.wikipedia.org/wiki/Prolog)，它已被用于
表示逻辑谓词、专家系统中的“事实”、符号数学项等等。

### Rules: Left-hand-side Patterns, Right-hand-side Expressions

### 规则：左侧模式，右侧表达式

The heart of a term-rewriting system is in the set of *rules* that
actually perform the rewrites. The "program" itself, in a
term-rewriting DSL, consists simply of an unordered list of
rules. Each rule may or may not apply; if it applies, then it can be
used to edit the term. Execution consists of repeated application of
rules until some criteria are met.

项重写系统的核心在于实际执行重写的一组 *规则*。
在项重写 DSL 中，“程序”本身仅由一个无序的规则列表组成。
每条规则可能适用，也可能不适用；如果适用，那么它就可以
用来编辑该项。执行过程由反复应用规则组成，直到满足某些条件。

A rule consists of two parts: the left-hand side (LHS), or *pattern*,
and right-hand side (RHS), or *expression*. The left-hand and
right-hand nomenclature comes from a common way of writing rules as:

一条规则由两部分组成：左侧（LHS），即 *模式*，
以及右侧（RHS），即 *表达式*。左侧和右侧的命名来自一种
常见的规则写法：

```plain
    A -> B              ;; any term "A" is rewritten to "B"

    (A x) -> (B (C x))  ;; any term (A x), for some x, is rewritten to (B (C x)).

    (A _) -> (D)        ;; any term (A _), where `_` is a wildcard (any subterm),
                        ;; is rewritten to (D).
```

#### Left-hand Sides: Patterns

#### 左侧：模式

Each left-hand side is written in a pattern language that commonly has
a few different kinds of "matchers", or operators that can match
subterms:

每个左侧都用一种模式语言编写，这种语言通常有
几种不同的“匹配器”，即可以匹配子项的运算符：

* `(A pat1 pat2 ...)` matches a constructor `A` with patterms for each
  of its arguments.

* `(A pat1 pat2 ...)` 匹配一个构造器 `A`，并为其每个
  参数匹配相应的模式。

* `x` matches any subterm and captures its value in a variable
  binding, which can be used later when we specify the right-hand side
  (so that the rewrite contains parts of the original term).

* `x` 匹配任意子项，并将其值捕获到一个变量
  绑定中；当我们指定右侧时，可以稍后使用该绑定
  （这样重写结果就包含原始项的一部分）。

* `_` is a wildcard and matches anything, without capturing it.

* `_` 是通配符，可以匹配任何内容，但不捕获它。

* Primitive constant values, such as `42` or `$Symbol`, match only if
  the term is exactly equal to this constant.

* 原始常量值，例如 `42` 或 `$Symbol`，仅当
  该项与此常量完全相等时才匹配。

These pattern-matching operators can be combined, so we could write,
for example, `(A (B x _) z)`. This pattern would match the term `(A (B
1 2) 3)` but not `(A (C 4 5) 6)`.

这些模式匹配运算符可以组合使用，因此例如我们可以写
`(A (B x _) z)`。此模式会匹配项 `(A (B
1 2) 3)`，但不会匹配 `(A (C 4 5) 6)`。

A pattern can properly be seen as a partial function from input term
to captured (bound) variables: it either matches or it doesn't, and if
it does, it provides specific term values for each variable binding
that can be used by the right-hand side.

一个模式可以恰当地看作从输入项到已捕获（已绑定）变量的
偏函数：它要么匹配，要么不匹配；如果匹配，它会为每个变量绑定
提供具体的项值，供右侧使用。

A fully-featured term rewriting system usually has other operators as
well, for convenience: for example, "match already-captured value", or
"bind variable to subterm and also match it with subpattern", or
"match subterm with all of these subpatterns". But even the above is
powerful enough for Turing-complete term reduction, surprisingly; the
essence of term-rewriting's power is just its ability to trigger
different rules on different "shapes" of the tree of constructors in
the input, and on special cases for certain argument values.

一个功能完备的项重写系统通常还会有其他运算符以便使用：
例如，“匹配已经捕获的值”，或
“将变量绑定到子项，同时也用子模式匹配它”，或
“用所有这些子模式匹配子项”。但令人惊讶的是，即使只有上述功能，
也已经足以进行图灵完备的项归约；项重写能力的本质，
正是它能够根据输入中构造器树的不同“形状”，
以及某些参数值的特殊情况，触发不同的规则。

Pattern-based term rewriting has a notable and important feature: it
typically allows *overlapping* rules. This means that more than one
pattern might match on the input. For example, the two rules:

基于模式的项重写有一个显著且重要的特性：它
通常允许 *重叠* 规则。这意味着输入上可能有不止一个
模式能够匹配。例如，以下两条规则：

```plain
    (A (B x)) -> (C x)
    (A _) -> (D)
```

could *both* apply to an input term `(A (B 1))`. The first rule would
rewrite this input to `(C 1)`, and the second rule would rewrite it to
`(D)`. Either rewrite would be an acceptable execution step under the
base semantics of most term-rewriting systems; ordinarily, the
*correctness* of the rewrite should not depend on which rule is
chosen, only possibly the "optimality" of the output (whatever that
means for the application domain in question) or the number of rewrite
steps to get there.

可能*两者*都适用于输入项 `(A (B 1))`。第一条规则会将此输入重写为 `(C 1)`，第二条规则会将其重写为
`(D)`。在大多数项重写系统的
基础语义下，任一重写都可以是可接受的执行步骤；通常，重写的
*正确性*不应取决于选择了哪条规则，而只可能取决于输出的“最优性”（无论这对相关应用领域
意味着什么）或到达该输出所需的重写
步骤数。

However, in order to provide a deterministic answer, the system must
somehow specify which rule will be applied in such a situation based
on precedence, or specificity, or some other tie-breaker. A common
heuristic is "more specific rule wins". We will see how ISLE resolves
this question below by using both this heuristic and an explicit
priority mechanism.[^4]

然而，为了提供确定性的答案，系统必须
以某种方式基于优先级、特异性或某种其他决胜规则，指定在这种情况下
将应用哪条规则。一个常见的
启发式规则是“更具体的规则获胜”。下面我们将看到 ISLE 如何通过同时使用这一启发式规则和显式的
优先级机制来解决这个问题。[^4]

[^4]: Some term-rewriting systems actually elaborate the entire space
      of possibilities, following *all* possible rule application
      sequences / rewrite paths. For example, the *equality
      saturation* technique
      ([paper](https://cseweb.ucsd.edu/~lerner/papers/popl09.pdf),
      [example implementation
      Egg](https://blog.sigplan.org/2021/04/06/equality-saturation-with-egg/))
      builds a data structure that represents all equivalent terms
      under a set of rewrite rules, from which a heuristic
      (cost/goodness function) can be used to extract one answer when
      needed.

[^4]: 一些项重写系统实际上会展开整个可能性空间，遵循*所有*可能的规则应用
      序列 / 重写路径。例如，*等式
      饱和*技术
      ([paper](https://cseweb.ucsd.edu/~lerner/papers/popl09.pdf),
      [示例实现
      Egg](https://blog.sigplan.org/2021/04/06/equality-saturation-with-egg/))
      构建一种数据结构，用于表示在一组重写规则下所有等价的项，
      在需要时可以从中使用一种启发式
      （代价/优良度函数）来提取一个答案。

#### Right-hand Sides: Rewrite Expressions

#### 右侧：重写表达式

Given a rule whose pattern has matched, we now need to compute the
rewritten term that replaces the original input term. This rewrite is
specified by the right-hand side (RHS), which consists of an
*expression* that generates a new term. This expression can use parts
of the input term that have been captured by variables in the
pattern.

给定一条其模式已经匹配的规则，我们现在需要计算
用于替换原始输入项的重写后项。此重写由右侧（RHS）指定，右侧由一个
*表达式*组成，该表达式生成一个新项。该表达式可以使用输入项中
已被模式中的变量捕获的部分。

We have already seen a few examples of this above: simple term
expressions, with variables used in place of concrete subterms where
desired. A typical term-rewrite system allows just a few options in
the output expression:

我们在上面已经见过几个这样的例子：简单的项
表达式，在需要的位置使用变量来替代具体子项。
典型的项重写系统在输出表达式中只允许少数几种选项：

* Terms, with sub-expressions as arguments;
* Constant primitives (`42` or `$Symbol`); and
* Captured variable values (`x`).

* 项，以子表达式作为参数；
* 常量原语（`42` 或 `$Symbol`）；以及
* 捕获的变量值（`x`）。

The options are more limited in expressions than in patterns (e.g.,
there are no wildcards) because a pattern is matching on a range of
possible terms while an expression must specify a specific rewrite
result.

表达式中的选项比模式中的更受限制（例如，
没有通配符），因为模式是在匹配一系列
可能的项，而表达式必须指定一个具体的重写
结果。

### Rewrite Steps and Intermediate Terms

### 重写步骤和中间项

Now that we can specify rewrites via a list of rules, we can study how
the top-level execution of a term-rewriting system proceeds. Much of
the power of term-rewriting comes from the fact that rewrites can
*chain together* into a multi-step traversal through several
intermediate terms before the final answer is computed.

现在我们可以通过规则列表来指定重写，就可以研究
项重写系统的顶层执行如何进行。项重写的许多
威力来自这样一个事实：重写可以在计算出最终答案之前，
*串联起来*，形成经过若干
中间项的多步骤遍历。

For a simple example, consider the following rules:

举一个简单的例子，考虑以下规则：

```plain
    (A (B x)) -> (C x)
    (C (D x)) -> (E x)
    (C (F x)) -> (G x)
```

This set of rules will rewrite `(A (B (D 42)))` to `(C (D 42))`, then
to `(E 42)` (via the first and second rules respectively).

这组规则会将 `(A (B (D 42)))` 重写为 `(C (D 42))`，然后
重写为 `(E 42)`（分别通过第一条和第二条规则）。

How is this useful? First, rewriting one term to another (here, `C` at
the top level) that in turn appears in the left-hand side of other
rules allows us to *factor* a "program" of term-rewriting rules in the
same way that imperative programs are factored into separate
functions.[^5] The usual advantages of a well-factored program, where
each problem is solved with a small step that "reduces to a previously
solved problem", apply here.

这有什么用？首先，将一个项重写为另一个项（这里是顶层的 `C`），而 `C` 又出现在其他规则的左侧，这使我们能够以与命令式程序被分解为独立函数相同的方式，*分解* 一组项重写规则构成的“程序”。[^5] 良好分解的程序的通常优势在这里也同样适用：每个问题都通过一个小步骤来解决，而这个步骤“化简为先前已解决的问题”。

Second, repeating the rewrite step is actually what grants
term-rewriting its Turing-completeness: it allows for arbitrary
control flow.[^6] This might be useful in cases where, for example, a
term-rewriting program needs "loop" over a list of elements in the
input: it can recurse and use intermediate terms to store state.

其次，重复执行重写步骤实际上正是赋予项重写图灵完备性的原因：它允许任意控制流。[^6] 这在某些情况下可能很有用，例如，项重写程序需要对输入中的元素列表进行“循环”时：它可以递归，并使用中间项来存储状态。

While this full generality may not be used often in the
domain-specific applications of term-rewriting that emphasize its
pattern-matching (such as instruction selectors), the user should not
be afraid to define and use intermediate terms -- rewriting into them,
then defining additional rules to rewrite further -- when it helps to
factor common behavior out of multiple rules, or aids in conceptual
clarity.

虽然这种完整的通用性在强调模式匹配的项重写领域特定应用中（例如指令选择器）可能并不常用，但当这样做有助于从多条规则中分解出共同行为，或有助于概念上的清晰性时，用户不应害怕定义并使用中间项——先重写到这些中间项，再定义额外规则继续重写——。

[^5]: In fact, ISLE actually compiles rules for different top-level
      pattern terms (`(A ...)` and `(C ...)` in the example) into
      separate Rust functions, so factoring rules to use intermediate
      terms can provide code-size and compile-time benefits for the
      ISLE-generated Rust code as well.

[^5]: 事实上，ISLE 实际上会将针对不同顶层模式项（示例中的 `(A ...)` 和 `(C ...)`）的规则编译为独立的 Rust 函数，因此将规则分解为使用中间项也可以为 ISLE 生成的 Rust 代码带来代码大小和编译时间方面的收益。

[^6]: The [lambda calculus' reduction
      rules](https://en.wikipedia.org/wiki/Lambda_calculus#Reduction)
      are a good example of this.

[^6]: [lambda 演算的约简规则](https://en.wikipedia.org/wiki/Lambda_calculus#Reduction) 是一个很好的例子。

### Application to Compilers: A Term is a Value; Rewrites are Lowerings

### 在编译器中的应用：项是值；重写是降低

So far this has been a fairly abstract introduction to term-rewriting
systems as a general computing paradigm. How does this relate (or, how
is it commonly mapped) to the instruction-selection problem?

到目前为止，这只是对项重写系统作为一种通用计算范式的相当抽象的介绍。它与指令选择问题有什么关系（或者说，通常如何映射）？

In a domain such as instruction selection, we manipulate terms that
represent computations described by an IR, and the terms are
eventually rewritten into terms that name specific machine
instructions. We can think of each term as having a denotational value
that that *is* that program value. Then, any rewrite is correct if it
preserves the denotational value of the term.

在像指令选择这样的领域中，我们操作的是表示由 IR 描述的计算的项，而这些项最终会被重写为表示特定机器指令的项。我们可以把每个项看作具有一个指称值，而这个值就是该程序值。然后，只要某个重写保持了该项的指称值，它就是正确的。

In other words, terms are just values, and rules specify alternative
ways to compute the same values. We might have rewrite rules that
correspond to common algebraic identities (`a + b` == `b + a`, and
`a + 0` == `a`), for example. The main sort of rewrite rule, however,
will be one that takes a machine-*independent* operator term and
rewrites it into a machine-*dependent* instruction term. For example:

换句话说，项就是值，而规则指定了计算相同值的不同方式。例如，我们可能会有与常见代数恒等式对应的重写规则（`a + b` == `b + a`，以及 `a + 0` == `a`）。不过，主要的重写规则类型将是：把机器-*无关*的运算符项重写为机器-*相关*的指令项。例如：

```plain
    (iadd a b) -> (isa.add_reg_reg a b)

    (iadd a (iconst 0)) -> a

    (iadd a (iconst n)) (isa.add_reg_imm a n)
```

These rules specify three ways to convert an IR `iadd` operator into
an ISA-specific instruction. Recall from above that in general, an
application of a term-rewriting system should not depend for
correctness on the order or choice of rule application: when multiple
rules are applicable, then any sequence of rewrites that ends in a
terminating state (a state with no further-applicable rules) should be
considered a "correct" answer.[^7] Here, this is true: if, for
example, we choose the register-plus-register form (the first rule)
for an `iadd` operation, but the second argument is actually an
`iconst`, then that is still valid, and the `iconst` will separately
be rewritten by some other rule that generates a constant into a
register. It simply may not be as efficient as the more specific third
rule (or second rule, if the constant is zero). Hence, rule ordering
and prioritization is nevertheless important for the quality of the
instruction selector.

这些规则指定了将 IR `iadd` 运算符转换为
ISA 特定指令的三种方式。回想上文，一般来说，
项重写系统的一次应用，其正确性不应依赖于
规则应用的顺序或选择：当有多条规则适用时，任何以
终止状态（没有进一步适用规则的状态）结束的重写序列都应被
视为一个“正确”的答案。[^7] 在这里，确实如此：例如，如果我们为
某个 `iadd` 操作选择了寄存器加寄存器形式（第一条规则），
但第二个参数实际上是一个 `iconst`，那么这仍然是有效的，
并且该 `iconst` 会由生成常量到寄存器的其他规则单独重写。
它只是可能不如更具体的第三条规则（或者当常量为零时的第二条规则）
高效。因此，规则排序和优先级对于指令选择器的质量仍然很重要。

[^7]: Note that this suggests an interesting testing strategy: we
      could choose arbitrary (random) orders of lowering rules to
      apply, or even deliberately worst-case orders according to some
      heuristic. If we can differentially test programs compiled with
      such randomized lowerings against "normally" compiled programs
      and show that the results are always the same, then we have
      shown that are lowering rules are "internally consistent",
      without any other external oracle. This will have a similar
      effect to
      [wasm-mutate](https://github.com/bytecodealliance/wasm-tools/tree/main/crates/wasm-mutate),
      but takes mutations implicitly from the pool of rules rather
      than a separate externally-defined pool of mutations. This idea
      remains future work.

[^7]: 请注意，这暗示了一种有趣的测试策略：我们
      可以选择任意（随机）的降低规则应用顺序，
      甚至可以根据某种启发式方法故意选择最坏情况的顺序。
      如果我们能够对使用这种随机化降低编译的程序与“正常”编译的程序进行
      差分测试，并证明结果总是相同的，那么我们就证明了
      我们的降低规则是“内部一致的”，
      而无需任何其他外部预言机。这将产生类似于
      [wasm-mutate](https://github.com/bytecodealliance/wasm-tools/tree/main/crates/wasm-mutate)
      的效果，
      但其变异隐式来自规则池，
      而不是来自单独的外部定义的变异池。这个想法仍是未来工作。

## Core ISLE: a Term-Rewriting System

## Core ISLE：项重写系统

This section describes the core ISLE language. ISLE's core is a
term-rewriting system, with a design that very closely follows the
generic concepts that we have described above.

本节描述核心 ISLE 语言。ISLE 的核心是一个
项重写系统，其设计非常紧密地遵循了我们上文描述的
通用概念。

In the core language, ISLE's key departure from many other
term-rewriting systems is that it is *strongly typed*. A classical
term-rewriting system, especially one designed for instruction
rewriting, will typically have just one type of term, corresponding to
a "value" in the program. In contrast, ISLE is designed so that terms
can represent various concepts in a compiler backend: values, but also
machine instructions or parts of those instructions ("integer
immediate value encodable in machine's particular format"), or
abstract bundles of information with invariants or guarantees encoded
in the type system ("load that I can sink", "instruction that produces
flags").

在核心语言中，ISLE 相对于许多其他项重写系统的关键区别在于它是*强类型*的。经典的
项重写系统，尤其是为指令重写而设计的系统，通常只有一种项类型，
对应于程序中的一个“值”。相比之下，ISLE 的设计使得项
可以表示编译器后端中的各种概念：值，也可以是
机器指令或这些指令的组成部分（“可按机器特定格式编码的整数立即数值”），
或者是在类型系统中编码了不变量或保证的抽象信息包
（“我可以下沉的加载”，“产生标志的指令”）。

ISLE's other key departure from many other systems is its first-class
integration with Rust, including a well-defined "FFI" mapping that
allows ISLE rules to call into Rust in both their patterns and
expressions, and to operate directly on types that are defined in the
surrounding Rust code. This allows for easy and direct embedding into
an existing compiler backend. We will cover this aspect more in the
next section, [ISLE to Rust](#isle-to-rust).

ISLE 与许多其他系统的另一个关键区别是，它与 Rust 具有一等集成，包括一个定义良好的 "FFI" 映射，允许 ISLE 规则在其模式和表达式中调用 Rust，并直接操作在外围 Rust 代码中定义的类型。这使得它可以轻松而直接地嵌入到现有编译器后端中。我们将在下一节 [ISLE to Rust](#isle-to-rust) 中更详细地介绍这一方面。

### Rules

### 规则

ISLE allows the user to specify rewrite rules, with a syntax similar
in spirit to that shown above:

ISLE 允许用户指定重写规则，其语法在精神上类似于上面所示：

```lisp
    (rule
      ;; left-hand side (pattern): if the input matches this ...
      (A (B _ x) (C y))
      ;; ... then rewrite to this:
      (D x y))
```

The pattern (left-hand side) is made up of the following match
operators:

模式（左侧）由以下匹配操作符组成：

* Wildcards (`_`).
* Integer constants (decimal/hex/binary/octal, positive/negative: `1`, `-1`,
  `0x80`, `-0x80`). Hex constants can start with either `0x` or `0X`.
  Binary constants start with `0b`. Octal constants start with `0o`.
  Integers can also be interspersed with `_` as a separator, for example
  `1_000` or `0x1234_5678`, for readability.
* constants imported from the embedding, of arbitrary type
  (`$MyConst`).
* Variable captures and matches (bare identifiers like `x`; an
  identifier consists of alphanumeric characters and underscores, and
  does not start with a digit). The first occurrence of a variable `x`
  captures the value; each subsequent occurrence matches on the
  already-captured value, rejecting the match if not equal.
* Variable captures with sub-patterns: `x @ PAT`, which captures the
  subterm in `x` as above but also matches `PAT` against the
  subterm. For example, `x @ (A y z)` matches an `A` term and captures
  its arguments as `y` and `z`, but also captures the whole term as
  `x`.
* conjunctions of subpatterns: `(and PAT1 PAT2 ...)` matches all of
  the subpatterns against the term. If any subpattern does not match,
  then this matcher fails.
* Term deconstruction: `(term PAT1 PAT2 ...)`, where `term` is a
  defined term (type variant or constructor) and the subpatterns are
  applied to each argument value in turn. Note that `term` cannot be a
  wildcard; it must be a specific, concrete term.

* 通配符（`_`）。
* 整数常量（十进制/十六进制/二进制/八进制，正数/负数：`1`、`-1`、
  `0x80`、`-0x80`）。十六进制常量可以以 `0x` 或 `0X` 开头。
  二进制常量以 `0b` 开头。八进制常量以 `0o` 开头。
  整数中也可以穿插 `_` 作为分隔符，例如
  `1_000` 或 `0x1234_5678`，以提高可读性。
* 从嵌入环境导入的、任意类型的常量
  （`$MyConst`）。
* 变量捕获和匹配（裸标识符，如 `x`；标识符由字母数字字符和下划线组成，
  且不以数字开头）。变量 `x` 的第一次出现会捕获该值；
  每次后续出现都会与已捕获的值进行匹配，如果不相等则拒绝该匹配。
* 带子模式的变量捕获：`x @ PAT`，它如上所述将子项捕获到 `x` 中，
  同时还将 `PAT` 与该子项进行匹配。例如，`x @ (A y z)` 匹配一个 `A` 项并捕获
  其参数为 `y` 和 `z`，同时也将整个项捕获为
  `x`。
* 子模式的合取：`(and PAT1 PAT2 ...)` 将所有子模式与该项进行匹配。
  如果任何子模式不匹配，则此匹配器失败。
* 项解构：`(term PAT1 PAT2 ...)`，其中 `term` 是一个
  已定义的项（类型变体或构造器），子模式会依次应用于每个参数值。
  注意，`term` 不能是通配符；它必须是一个特定的、具体的项。

The expression (right-hand side) is made up of the following
expression operators:

表达式（右侧）由以下表达式操作符组成：

* Integer and symbolic constants, as above.
* Variable uses (bare `x` identifier).
* Term constructors (`(term EXPR1 EXPR2 ...)`, where each
  subexpression is evaluated first and then the term is constructed).
* `let`-expressions that bind new variables, possibly using the values
  multiple times within the body: `(let ((var1 type1 EXPR1) (var2 ...)
  ...) BODY ...)`. Each variable's initialization expression can refer
  to the immediately previous variable bindings (i.e., this is like a
  `let*` in Scheme). `let`s are lexically-scoped, meaning that bound
  variables are available only within the body of the `let`.

* 整数和符号常量，如上所述。
* 变量使用（裸 `x` 标识符）。
* 项构造器（`(term EXPR1 EXPR2 ...)`，其中每个
  子表达式先求值，然后构造该项）。
* `let` 表达式，用于绑定新变量，并且可以在主体中多次使用这些值：`(let ((var1 type1 EXPR1) (var2 ...)
  ...) BODY ...)`。每个变量的初始化表达式都可以引用紧邻其前面的变量绑定
  （也就是说，这类似于 Scheme 中的 `let*`）。`let` 具有词法作用域，意味着绑定的变量
  仅在该 `let` 的主体中可用。

When multiple rules are applicable to rewrite a particular term, ISLE
will choose the "more specific" rule according to a particular
heuristic: in the lowered sequence of matching steps, when one
left-hand side completes a match while another with the same prefix
continues with further steps, the latter (more specific) is chosen.

当有多条规则可用于重写某个特定项时，ISLE
会根据一种特定的启发式方法选择“更具体”的规则：在降低后的匹配步骤序列中，如果一个
左侧完成了匹配，而另一个具有相同前缀的左侧
继续执行更多步骤，则会选择后者（更具体的那个）。

The more-specific-first heuristic is usually good enough, but when an
undesirable choice occurs, explicit priorities can be specified.
Rules with explicit priorities are written as `(rule PRIO lhs rhs)`
where `PRIO` is a signed (positive or negative) integer. An applicable
rule with a higher priority will always match before a rule with a
lower priority. The default priority for all rules if not otherwise
specified is `0`.

“更具体者优先”的启发式方法通常已经足够好，但当出现
不理想的选择时，可以指定显式优先级。
带有显式优先级的规则写作 `(rule PRIO lhs rhs)`，
其中 `PRIO` 是一个有符号（正或负）整数。适用的
较高优先级规则总是会在较低优先级规则之前匹配。
如果未另行指定，所有规则的默认优先级都是 `0`。

Note that the system allows multiple applicable rules to exist with
the same priority: that is, while the priority system allows for
manual tie-breaking, this tie-breaking is not required.

请注意，系统允许存在多条具有
相同优先级的适用规则：也就是说，虽然优先级系统允许
手动打破平局，但并不要求必须打破这种平局。

Finally, one important note: the priority system is considered part of
the core language semantics and execution of rules with different
priorities is well-defined, so can be relied upon when specifying
correct rules. However, the tie-breaking heuristic is *not* part of
the specified language semantics, and so the user should never write
rules whose correctness depends on one rule overriding another
according to the heuristic.

最后，有一点重要说明：优先级系统被视为
核心语言语义的一部分，并且不同
优先级规则的执行是明确定义的，因此在指定
正确规则时可以依赖它。然而，打破平局的启发式方法*不是*
指定语言语义的一部分，因此用户绝不应编写
其正确性依赖于某条规则根据该启发式方法覆盖另一条规则的
规则。

### Typed Terms

### 带类型的项

ISLE allows the programmer to define types, and requires every term to
have *parameter types* and a *return type* (analogous to first-order
functions).

ISLE 允许程序员定义类型，并要求每个项都具有
*参数类型*和*返回类型*（类似于一阶
函数）。

The universe of types is very simple: there are *primitives*, which
can be integers or symbolic constants (imported from the Rust
embedding), and *enums*, which correspond directly to Rust enums with
variants that have named fields. There is no subtyping. Some examples
of type definitions are:

类型的宇宙非常简单：有*原语*，它们
可以是整数或符号常量（从 Rust
嵌入中导入），以及*枚举*，它们直接对应于带有
具有命名字段的变体的 Rust 枚举。不存在子类型。一些
类型定义示例如下：

```lisp

    (type u32 (primitive u32))  ;; u32 is a primitive, and is
                                ;; spelled `u32` in the generated Rust code.

    (type MyType (enum
                   (A (x u32) (y u32))
                   (B (z u32))
                   (C)))        ;; MyType is an enum, with variants
                                ;; `MyType::A { x, y }`, `MyType::B { z }`,
                                ;; and `MyType::C`.

    (type MyType2 extern (enum (A)))
                                ;; MyType2 is an enum with variant `MyType2::A`.
                                ;; Its type definition is not included in the
                                ;; generated Rust, but rather, assumed to exist
                                ;; in surrounding code. Useful for binding to
                                ;; existing definitions.
```

We then declare constructors with their parameter and return types as
follows:

然后，我们按如下方式声明构造器及其参数类型和返回类型：

```lisp

    (decl Term1 (u32 u32) MyType)  ;; Term1 has two `u32`-typed parameters,
                                   ;; and itself has type `MyType`.
    (decl Term2 () u32)            ;; Term2 has no parameters and type `u32`.
```

Note that when an enum type is defined, its variants are implicitly
defined as constructors as well. These constructors are namespaced
under the name of the type, to avoid ambiguity (or the need to do
type-dependent lookups in the compiler, which can complicate type
inference). For example, given the above `MyType` definitions, we
automatically have the following constructors:

请注意，当定义枚举类型时，其变体也会被隐式地
定义为构造器。这些构造器位于
该类型名称的命名空间下，以避免歧义（或避免编译器中需要进行
依赖类型的查找，因为这会使类型
推断复杂化）。例如，给定上面的 `MyType` 定义，我们
会自动拥有以下构造器：

```lisp

    ;; These definitions are implicit and do not need to be written (doing
    ;; so is a compile-time error, actually). We write them here just to
    ;; show what they would look like.

    (decl MyType.A (u32 u32) MyType)
    (decl MyType.B (u32) MyType)
    (decl MyType.C () MyType)

    (decl MyType2.A () MyType2)
```

### Why Types?

### 为什么需要类型？

For terms that are not enum variants, the notion that a term "has a
type" is somewhat foreign to a classical term-rewriting system. In
most formal symbolic systems, the terms are manipulated as opaque
sequences or trees of symbols; they have no inherent meaning other
than what the user implicitly defines with the given rules. What does
it mean for a term to "have a type" when it is just data? Or, said
another way: why isn't the type of `Term2` just `Term2`?

对于不是枚举变体的项而言，项“具有
类型”的概念对经典的项重写系统来说有些陌生。在
大多数形式化符号系统中，项被作为不透明的
符号序列或符号树来操作；除了用户通过给定规则隐式定义的含义之外，
它们没有固有含义。当一个项只是数据时，
说它“具有类型”是什么意思？或者换一种说法：
为什么 `Term2` 的类型不就是 `Term2`？

The types come into play when we define *rules*: one term of type `T`
can only be rewritten into another term of type `T`, and when a
parameter has a certain type, only subterms with that type can
appear. Without explicit types on terms and their parameters, any term
could be rewritten to any other, or substituted in as a parameter, and
there is thus a kind of dynamic typing about which the programmer must
have some caution. In most applications of a term-rewriting system,
there is already some de-facto "schema": some parameter of a term
representing a machine instruction can only take on one of a few
subterms (representing, say, different addressing modes). ISLE's types
just make this explicit.

当我们定义*规则*时，类型就会发挥作用：类型为 `T` 的一个项只能被重写为另一个类型为 `T` 的项；并且当某个参数具有特定类型时，只有具有该类型的子项才能出现。如果项及其参数没有显式类型，那么任何项都可能被重写为任何其他项，或作为参数被替换进去，因此就会存在一种动态类型机制，程序员必须对此保持一定谨慎。在项重写系统的大多数应用中，通常已经存在某种事实上的“模式”：例如，表示机器指令的项的某个参数只能取少数几种子项之一（比如表示不同寻址模式的子项）。ISLE 的类型只是将这一点显式化。

Thus, the first answer to "why types" is that they enforce a schema on
the terms, allowing the programmer to have stronger well-formed-data
invariants.

因此，对于“为什么需要类型”的第一个回答是：类型在项上强制执行一种模式，使程序员能够拥有更强的良构数据不变量。

The second reason is that the types are an integral part of the
compilation-to-Rust strategy: every constructor actually does evaluate
to a Rust value of the given "return value" type, given actual Rust
values for its parameters of the appropriate parameter types. We will
see more on this below.

第二个原因是，类型是编译到 Rust 策略的一个组成部分：给定相应参数类型的实际 Rust 值，每个构造器实际上都会求值为给定“返回值”类型的 Rust 值。我们将在下面看到更多相关内容。

### Well-Typed Rules and Type Inference

### 良好类型化的规则和类型推断

Now that we understand how to define types, let's examine in more
detail how they are used to verify that the pattern and rewrite
expression of a rule have the same type.

既然我们已经理解了如何定义类型，接下来让我们更详细地考察它们如何用于验证规则的模式和重写表达式具有相同的类型。

ISLE uses a simple unidirectional type-inference algorithm that
propagates type information through the pattern, resulting in a "type
environment" that specifies the type for each captured variable, and
then uses this to typecheck the rewrite expression. The result of this
is that types are almost completely inferred, and are only annotated
in a few places (`let` bindings specifically).

ISLE 使用一种简单的单向类型推断算法，该算法通过模式传播类型信息，生成一个“类型环境”，为每个捕获的变量指定类型，然后使用它来对重写表达式进行类型检查。其结果是，类型几乎完全是推断出来的，只需要在少数位置进行标注（具体来说是 `let` 绑定）。

The typing rules for patterns in ISLE are:

ISLE 中模式的类型规则如下：

* At the root of the pattern, we require that a *constructor* pattern
  is used, rather than some other match operation (a wildcard, integer
  constant, etc.). This is because compilation and dispatch into rules
  is organized by the top-level constructor of the term being
  rewritten.

* 在模式的根部，我们要求使用*构造器*模式，而不是其他匹配操作（通配符、整数常量等）。这是因为编译以及分派到规则的过程，是按被重写项的顶层构造器来组织的。

* At each part of the pattern except the root, there is an "expected
  type" that is inferred from the surrounding context. We check that
  this matches the actual type of the pattern.

* 在模式中除根部以外的每个部分，都有一个从周围上下文推断出的“期望类型”。我们会检查它是否与模式的实际类型匹配。

* A constructor pattern `(C x y z)`, given a constructor `(decl C (T1
  T2 T2) R)`, has type `R` and provides expected types `T1`, `T2`, and
  `T3` to its subpatterns.

* 给定构造器 `(decl C (T1
  T2 T2) R)`，构造器模式 `(C x y z)` 的类型为 `R`，并向其子模式提供期望类型 `T1`、`T2` 和 `T3`。

* A variable capture pattern `x` is compatible with any expected type
  the first time it appears, and captures this expected type under the
  variable identifier `x` in the type environment. Subsequent
  appearances of `x` check that the expected type matches the
  already-captured type.

* 变量捕获模式 `x` 第一次出现时与任何期望类型都兼容，并会在类型环境中以变量标识符 `x` 捕获此期望类型。`x` 随后的出现会检查期望类型是否与已捕获的类型匹配。

* A conjunction `(and PAT1 PAT2 ...)` checks that each subpattern is
  compatible with the expected type.

* 合取 `(and PAT1 PAT2 ...)` 会检查每个子模式是否与期望类型兼容。

* Integer constants are compatible with any primitive expected
  type. (This may change in the future if we add non-numeric
  primitives, such as strings.)

* 整数常量与任何原始期望类型兼容。（如果我们将来添加非数字原语，例如字符串，这一点可能会改变。）

If we are able to typecheck the pattern, we have a type environment
that is a map from variable bindings to types: e.g., `{ x: MyType, y:
MyType2, z: u32 }`. We then typecheck the rewrite expression.

如果我们能够对模式进行类型检查，就会得到一个类型环境，
它是从变量绑定到类型的映射：例如，`{ x: MyType, y:
MyType2, z: u32 }`。然后我们对 rewrite 表达式进行类型检查。

* Every expression also has an expected type, from the surrounding
  context. We check that the provided expression matches this type.

* 每个表达式也都有一个来自周围上下文的期望类型。
  我们检查所提供的表达式是否匹配此类型。

* The top-level rewrite expression must have the same type as the
  top-level constructor in the pattern. (In other words, a term can
  only be rewritten to another term of the same type.)

* 顶层 rewrite 表达式必须与模式中的顶层构造器具有相同类型。
  （换句话说，一个项只能被重写为另一个相同类型的项。）

* Constructors check their return values against the expected type,
  and typecheck their argument expressions against their parameter
  types.

* 构造器会根据期望类型检查其返回值，
  并根据其参数类型对其实参表达式进行类型检查。

* A `let` expression provides types for additional variable bindings;
  these are added to the type environment while typechecking the
  body. The expected type for the body is the same as the expected
  type for the `let` itself.

* `let` 表达式为额外的变量绑定提供类型；
  在对主体进行类型检查时，这些绑定会被添加到类型环境中。
  主体的期望类型与 `let` 本身的期望类型相同。

### A Note on Heterogeneous Types

### 关于异构类型的说明

We should illuminate one particular aspect of the ISLE type system
that we described above. We have said that a term must be rewritten to
another term of the same type. Note that this does *not* mean that,
for example, a set of ISLE rules cannot be used to translate a term of
type `T1` to a term of type `T2`. The trick is to define a top-level
"driver" that wraps the `T1`, such that reducing this term results in
a `T2`. Concretely:

我们应该阐明上面所描述的 ISLE 类型系统的一个特定方面。
我们曾说过，一个项必须被重写为另一个相同类型的项。请注意，这并*不*意味着，
例如，一组 ISLE 规则不能用于将类型为 `T1` 的项翻译为类型为 `T2` 的项。
技巧是定义一个顶层的“驱动器”，它包装 `T1`，使得规约此项会得到一个 `T2`。
具体来说：

```lisp
    (type T1 ...)
    (type T2 ...)

    (decl Translate (T1) T2)

    (rule (Translate (T1.A ...))
          (T2.X ...))
    (rule (Translate (T1.B ...))
          (T2.Y ...))
```

This gets to the heart of rewrite-system-based computation, and has
relevance for applications of ISLE to compiler backends. A common
technique in rewrite systems is to "kick off" a computation by
wrapping a term in some intermediate term that then drives a series of
reductions. Here we are using `Translate` as this top-level term. A
difference between ISLE and some other rewrite-based instruction
selectors is that rewrites are always driven by term reduction from
such a toplevel term, rather than a series of equivalences directly
from IR instruction to machine instruction forms.

这触及了基于重写系统的计算的核心，并且与 ISLE 在编译器后端中的应用相关。
重写系统中的一种常见技术是通过将某个项包装在某个中间项中来“启动”一次计算，
然后该中间项驱动一系列规约。这里我们使用 `Translate` 作为这个顶层项。
ISLE 与其他一些基于重写的指令选择器之间的一个区别是，重写总是由从这种顶层项开始的项规约来驱动，
而不是直接从 IR 指令形式到机器指令形式的一系列等价关系。

In other words, a conventional instruction selection pattern engine
might let one specify `(Inst.A ...) -> (Inst.X ...)`. In this
conventional design, the instruction/opcode type on the LHS and RHS
must be the same single instruction type (otherwise rewrites could not
be chained), and rewrite relation (which we wrote as `->`) is in
essence a single privileged relation. One can see ISLE as a
generalization: we can define many different types, and many different
toplevel terms from which we can start the reduction. In principle,
one could have:

换句话说，传统的指令选择模式引擎可能允许指定 `(Inst.A ...) -> (Inst.X ...)`。
在这种传统设计中，LHS 和 RHS 上的指令/opcode 类型必须是同一个单一的指令类型（否则重写无法串联），
而重写关系（我们写作 `->`）本质上是一个单一的特权关系。可以将 ISLE 视为一种泛化：
我们可以定义许多不同的类型，以及许多不同的顶层项，并从这些顶层项开始规约。原则上，
可以有：

```lisp

    (type IR ...)
    (type Machine1 ...)
    (type Machine2 ...)

    (decl TranslateToMachine1 (IR) Machine1)
    (decl TranslateToMachine2 (IR) Machine2)

    (rule (TranslateToMachine1 (IR.add a b)) (Machine1.add a b))
    (rule (TranslateToMachine2 (IR.add a b)) (Machine2.weird_inst a b))
```

and then both translations are available. We are "rewriting" from `IR`
to `Machine1` and from `IR` to `Machine2`, even if rewrites always
preserve the same type; we get around the rule by using a constructor.

然后两种翻译都可用。我们正在从 `IR` “重写”到 `Machine1`，并从 `IR` “重写”到 `Machine2`，
即使重写总是保持相同类型；我们通过使用构造器来绕过这条规则。

### Constructors and Extractors

### 构造器和提取器

So far, we have spoken of terms and constructors: a term is a schema
for data, like `(A arg1 arg2)`, while we have used the term
"constructor" to refer to the `A`, like a function. We now refine this
notion somewhat and define what it means for a term to appear in the
left-hand (pattern) or right-hand (expression) side of a rule.

到目前为止，我们讨论的是项和构造器：项是数据的模式，类似 `(A arg1 arg2)`，而我们一直使用“构造器”一词来指代其中的 `A`，类似一个函数。现在我们稍微细化这一概念，并定义一个项出现在规则左侧（模式）或右侧（表达式）时意味着什么。

More precisely, a term, like `A`, can have three kinds of behavior
associated with it: it can be an enum type variant, it can be a
constructor, or it can be an *extractor*, which we will define in a
moment. A term can be both an extractor and constructor
simultaneously, but the enum type variant case is mutually exclusive
with the others.

更准确地说，像 `A` 这样的项可以关联三种行为：它可以是一个枚举类型变体，可以是一个构造器，也可以是一个*提取器*，我们稍后会定义它。一个项可以同时既是提取器又是构造器，但枚举类型变体这种情况与其他两种情况是互斥的。

The distinction between a "constructor" and an "extractor" is whether
a term is being deconstructed (matched on) -- by an extractor -- or
constructed -- by a constructor.

“构造器”和“提取器”之间的区别在于，一个项是被解构（用于匹配）——通过提取器——还是被构造——通过构造器。

#### Constructors

#### 构造器

Constructor behavior on a term allows it to be invoked in the
right-hand side of a rule. A term can have either an "external
constructor" (see below) or an "internal constructor", defined in
ISLE. Any term `A` that has one or more `(rule (A ...) RHS)` rules in
the ISLE source implicitly has an internal constructor, and this
constructor can be invoked from the right-hand side of other rules.

项上的构造器行为允许它在规则的右侧被调用。一个项可以有一个“外部构造器”（见下文），也可以有一个在 ISLE 中定义的“内部构造器”。ISLE 源码中任何拥有一个或多个 `(rule (A ...) RHS)` 规则的项 `A` 都隐式拥有一个内部构造器，并且这个构造器可以从其他规则的右侧被调用。

#### Extractors

#### 提取器

Extractor behavior on a term allows it to be used in a pattern in the
left-hand side of a rule. If one considers a constructor to be a
function that goes from argument values to the complete term, then an
extractor is a function that takes a complete term and possibly
matches on it (it is fallible). If it does match, it provides the
arguments *as results*.

项上的提取器行为允许它在规则左侧的模式中使用。如果把构造器看作一个从参数值到完整项的函数，那么提取器就是一个接受完整项并可能对其进行匹配的函数（它是可失败的）。如果匹配成功，它会将参数*作为结果*提供出来。

One can see extractors as "programmable match operators". They are a
generalization of enum-variant deconstruction. Where a traditional
term-rewriting system operates on a term data-structure that exists in
memory, and can discover that a pattern `(A x y)` matches a term `A`
at a particular point in the input, an extractor-based system instead
sees `A` as an *arbitrary programmable operator* that is invoked
wherever a pattern-match is attempted, and can return "success" with
the resulting "fields" as if it were actually an enum variant. For
more on this topic, see the motivation and description in [RFC 15
under "programmable matching on virtual
nodes"](https://github.com/bytecodealliance/rfcs/blob/main/accepted/cranelift-isel-isle-peepmatic.md#extractors-programmable-matching-on-virtual-nodes).

可以将提取器看作“可编程的匹配操作符”。它们是枚举变体解构的一种泛化。传统的项重写系统在内存中存在的项数据结构上运行，并且可以发现模式 `(A x y)` 在输入中的某个特定位置匹配一个项 `A`；而基于提取器的系统则把 `A` 看作一个*任意可编程操作符*，在尝试模式匹配的任何地方都会调用它，并且可以返回“成功”以及由此得到的“字段”，就好像它实际上是一个枚举变体一样。关于此主题的更多内容，请参阅 [RFC 15 中 “programmable matching on virtual nodes” 下的动机和描述](https://github.com/bytecodealliance/rfcs/blob/main/accepted/cranelift-isel-isle-peepmatic.md#extractors-programmable-matching-on-virtual-nodes)。

To provide a concrete example, if we have the term declarations

举一个具体的例子，如果我们有如下项声明

```lisp
    (decl A (u32 u32) T)
    (decl B (T) U)
```

then if we write a rule like

那么如果我们写一个像这样的规则

```lisp
    (rule (B (A x y))
          (U.Variant1 x y))
```

then we have used `A` as an *extractor*. When `B` is invoked as a
constructor with some `T`, this rule uses `A` as an extractor and
attempts (via whatever programmable matching behavior) to use `A` to
turn the `T` into two `u32`s, binding `x` and `y`. `A` can succeed or
fail, just as any other part of a pattern-match can.

那么我们就将 `A` 用作了一个*提取器*。当 `B` 作为构造器并带有某个 `T` 被调用时，这条规则会将 `A` 用作提取器，并尝试（通过任何可编程匹配行为）使用 `A` 将该 `T` 转换为两个 `u32`，绑定 `x` 和 `y`。`A` 可以成功也可以失败，就像模式匹配中的任何其他部分一样。

Just as for constructors, there are *internal* and *external*
extractors. Most of the interesting programmable behavior occurs in
external extractors, which are defined in Rust; we will discuss this
further in a section below. Internal extractors, in contrast, behave
like macros, and can be defined for convenience: for example, we can
write

与构造器一样，提取器也分为*内部*和*外部*两种。大多数有趣的可编程行为都发生在外部提取器中，它们用 Rust 定义；我们将在下面的一个小节中进一步讨论这一点。相比之下，内部提取器的行为类似于宏，可以为了方便而定义：例如，我们可以编写

```lisp
    (decl A (u32 u32) T)
    (extractor (A pat1 pat2)
               (and
                 (extractArg1 pat1)
                 (extractArg2 pat2)))
```

which will, for example, expand a pattern `(A (subterm ...) _)` into
`(and (extractArg1 (subterm ...)) (extractArg2 _))`: in other words,
the arguments to `A` are substituted into the extractor body and then
this body is inlined.

例如，它会将模式 `(A (subterm ...) _)` 展开为
`(and (extractArg1 (subterm ...)) (extractArg2 _))`：换句话说，`A` 的参数会被替换到提取器主体中，然后该主体会被内联。

#### Implicit Type Conversions

#### 隐式类型转换

For convenience, ISLE allows the program to associate terms with pairs
of types, so that type mismatches are *automatically resolved* by
inserting that term.

为方便起见，ISLE 允许程序将项与类型对相关联，从而通过插入该项来*自动解决*类型不匹配。

For example, if one is writing a rule such as

例如，如果正在编写如下规则

```lisp
    (decl u_to_v (U) V)
    (rule ...)

    (decl MyTerm (T) V)
    (rule (MyTerm t)
          (u_to_v t))
```

the `(u_to_v t)` term would not typecheck given the ISLE language
functionality that we have seen so far, because it expects a `U` for
its argument but `t` has type `T`. However, if we define

根据我们目前所见的 ISLE 语言功能，`(u_to_v t)` 项将无法通过类型检查，因为它期望其参数为 `U`，但 `t` 的类型是 `T`。不过，如果我们定义

```lisp
    (convert T U t_to_u)

    ;; For the above to be valid, `t_to_u` should be declared with the
    ;; signature:
    (decl t_to_u (T) U)
    (rule ...)
```

then the DSL compiler will implicitly understand the above `MyTerm` rule as:

那么 DSL 编译器会隐式地将上面的 `MyTerm` 规则理解为：

```lisp
    (rule (MyTerm t)
          (u_to_v (t_to_u t)))
```

This also works in the extractor position: for example, if one writes

这在提取器位置也同样适用：例如，如果有人编写

```lisp
    (decl defining_instruction (Inst) Value)
    (extern extractor defining_instruction ...)

    (decl iadd (Value Value) Inst)

    (rule (lower (iadd (iadd a b) c))
          ...)

    (convert Inst Value defining_instruction)
```

then the `(iadd (iadd a b) c)` form will be implicitly handled like
`(iadd (defining_instruction (iadd a b)) c)`. Note that the conversion
insertion needs to have local type context in order to find the right
converter: so, for example, it cannot infer a target type from a
pattern where just a variable binding occurs, even if the variable is
used in some typed context on the right-hand side. Instead, the
"inner" and "outer" types have to come from explicitly typed terms.

那么 `(iadd (iadd a b) c)` 形式会被隐式地处理为
`(iadd (defining_instruction (iadd a b)) c)`。请注意，转换插入需要具有局部类型上下文，才能找到正确的转换器：因此，例如，它无法从一个仅发生变量绑定的模式中推断目标类型，即使该变量在右侧的某个有类型上下文中使用也是如此。相反，“内部”和“外部”类型必须来自显式带类型的项。

#### Summary: Terms, Constructors, and Extractors

#### 总结：项、构造器和提取器

We start with a `term`, which is just a schema for data:

我们从一个 `term` 开始，它只是数据的一个模式：

```lisp
    (decl Term (A B C u32 u32) T)
```

A term can have:

一个项可以具有：

1. A single internal extractor body, via a toplevel `(extractor ...)`
   form, OR

1. 通过顶层 `(extractor ...)`
   形式提供的单个内部提取器主体，或者

2. A single external extractor binding (see next section); AND

2. 单个外部提取器绑定（见下一节）；并且

3. One or more `(rule (Term ...) ...)` toplevel forms, which together
   make up an internal constructor definition, OR

3. 一个或多个 `(rule (Term ...) ...)` 顶层形式，它们共同构成一个内部构造器定义，或者

4. A single external constructor binding (see next section).

4. 单个外部构造器绑定（见下一节）。

### If-Let Clauses

### If-Let 子句

As an extension to the basic left-hand-side / right-hand-side rule
idiom, ISLE allows *if-let clauses* to be used. These add additional
pattern-matching steps, and can be used to perform additional tests
and also to use constructors in place of extractors during the match
phase when this is more convenient.

作为对基本左侧 / 右侧规则惯用法的扩展，ISLE 允许使用 *if-let 子句*。这些子句会添加额外的模式匹配步骤，并且可用于执行额外测试；在匹配阶段，当这样更方便时，也可用构造器代替提取器。

To introduce the concept, an example follows (this is taken from the
[RFC](https://github.com/bytecodealliance/rfcs/tree/main/accepted/isle-extended-patterns.md)
that proposed if-lets):

为引入这一概念，下面给出一个示例（取自提出 if-let 的 [RFC](https://github.com/bytecodealliance/rfcs/tree/main/accepted/isle-extended-patterns.md)）：

```lisp
;; `u32_fallible_add` can now be used in patterns in `if-let` clauses
(decl pure u32_fallible_add (u32 u32) u32)
(extern constructor u32_fallible_add u32_fallible_add)

(rule (lower (load (iadd addr
                         (iadd (uextend (iconst k1))
                               (uextend (iconst k2))))))
      (if-let k (u32_fallible_add k1 k2))
      (isa_load (amode_reg_offset addr k)))
```

The key idea is that we allow a `rule` form to contain the following
sub-forms:

核心思想是，我们允许 `rule` 形式包含以下子形式：

```lisp
(rule LHS_PATTERN
  (if-let PAT2 EXPR2)
  (if-let PAT3 EXPR3)
  ...
  RHS)
```

The matching proceeds as follows: the main pattern (`LHS_PATTERN`)
matches against the input value (the term to be rewritten), as
described in detail above. Then, if this matches, execution proceeds
to the if-let clauses in the order they are specified. For each, we
evaluate the expression (`EXPR2` or `EXPR3` above) first. An
expression in an if-let context is allowed to be "fallible": the
constructors return `Option<T>` at the Rust level and can return
`None`, in which case the whole rule application fails and we move on
to the next rule as if the main pattern had failed to match. (More on
the fallible constructors below.) If the expression evaluation
succeeds, we match the associated pattern (`PAT2` or `PAT3` above)
against the resulting value. This too can fail, causing the whole rule
to fail. If it succeeds, any resulting variable bindings are
available. Variables bound in the main pattern are available for all
if-let expressions and patterns, and variables bound by a given if-let
clause are available for all subsequent clauses. All bound variables
(from the main pattern and if-let clauses) are available in the
right-hand side expression.

匹配过程如下：主模式（`LHS_PATTERN`）
会与输入值（要被重写的项）进行匹配，如上文详细所述。然后，如果该匹配成功，执行会按指定顺序继续处理 if-let 子句。对于每个子句，我们首先求值表达式（上面的 `EXPR2` 或 `EXPR3`）。if-let 上下文中的表达式允许是“可失败的”：构造器在 Rust 层面返回 `Option<T>`，并且可以返回 `None`；在这种情况下，整个规则应用失败，我们会继续尝试下一条规则，就好像主模式未能匹配一样。（关于可失败构造器，下文会有更多说明。）如果表达式求值成功，我们就将关联的模式（上面的 `PAT2` 或 `PAT3`）与得到的值进行匹配。这同样可能失败，从而导致整条规则失败。如果成功，则任何产生的变量绑定都会可用。主模式中绑定的变量可用于所有 if-let 表达式和模式，而由某个 if-let 子句绑定的变量可用于所有后续子句。所有已绑定的变量（来自主模式和 if-let 子句）都可用于右侧表达式。

#### Pure Expressions and Constructors

#### 纯表达式和构造器

In order for an expression to be used in an if-let clause, it has to
be *pure*: it cannot have side-effects. A pure expression is one that
uses constants and pure constructors only. Enum variant constructors
are always pure. In general constructors that invoke function calls,
however (either as internal or external constructor calls), can lead
to arbitrary Rust code and have side-effects. So, we add a new
annotation to declarations as follows:

为了让表达式能够在 if-let 子句中使用，它必须是*纯*的：它不能有副作用。纯表达式是指只使用常量和纯构造器的表达式。枚举变体构造器始终是纯的。然而，一般来说，调用函数的构造器（无论是作为内部还是外部构造器调用）可能会执行任意 Rust 代码并产生副作用。因此，我们向声明添加一个新的注解，如下所示：

```lisp
;; `u32_fallible_add` can now be used in patterns in `if-let` clauses
(decl pure u32_fallible_add (u32 u32) u32)

;; This adds a method
;; `fn u32_fallible_add(&mut self, _: u32, _: u32) -> Option<u32>`
;; to the `Context` trait.
(extern constructor u32_fallible_add u32_fallible_add)
```

The `pure` keyword here is a declaration that the term, when used as a
constructor, has no side-effects. Declaring an external constructor on
a pure term is a promise by the ISLE programmer that the external Rust
function we are naming (here `u32_fallible_add`) has no side-effects
and is thus safe to invoke during the match phase of a rule, when we
have not committed to a given rule yet.

这里的 `pure` 关键字是一项声明，表示该项在作为构造器使用时没有副作用。将一个外部构造器声明在纯项上，是 ISLE 程序员作出的承诺：我们所命名的外部 Rust 函数（这里是 `u32_fallible_add`）没有副作用，因此可以在规则的匹配阶段安全调用，此时我们尚未确定要采用某条规则。

When an internal constructor body is generated for a term that is pure
(i.e., if we had `(rule (u32_fallible_add x y) ...)` in our program
after the above declaration instead of the `extern`), the right-hand
side expression of each rule that rewrites the term is also checked
for purity.

当为一个纯项生成内部构造器体时（也就是说，如果在上述声明之后，我们的程序中有 `(rule (u32_fallible_add x y) ...)`，而不是 `extern`），每条重写该项的规则的右侧表达式也会被检查是否为纯。

#### `partial` Expressions

#### `partial` 表达式

ISLE's `partial` keyword on a term indicates that the term's
constructors may fail to match, otherwise, the ISLE compiler assumes
the term's constructors are infallible.

ISLE 中项上的 `partial` 关键字表示该项的构造器可能匹配失败；否则，ISLE 编译器会假定该项的构造器是不可失败的。

For example, the following term's constructor only matches if the value
is zero:

例如，以下项的构造器只有在值为零时才会匹配：

```
;; Match any zero value.
(decl pure partial is_zero_value (Value) Value)
(extern constructor is_zero_value is_zero_value)
```

Internal constructors without the `partial` keyword can
only use other constructors that also do not have the `partial` keyword.

没有 `partial` 关键字的内部构造器只能使用同样没有 `partial` 关键字的其他构造器。

#### `if` Shorthand

#### `if` 简写

It is a fairly common idiom that if-let clauses are used as predicates
on rules, such that their only purpose is to allow a rule to match,
and not to perform any destructuring with a sub-pattern. For example,
one might want to write:

一种相当常见的用法是将 if-let 子句用作规则上的谓词，使其唯一目的只是允许规则匹配，而不是使用子模式执行任何解构。例如，可能会想写：

```lisp
(rule (lower (special_inst ...))
      (if-let _ (isa_extension_enabled))
      (isa_special_inst ...))
```

where `isa_extension_enabled` is a pure constructor that is fallible,
and succeeds only when a condition is true.

其中 `isa_extension_enabled` 是一个可能失败的纯构造器，
并且只有在条件为真时才会成功。

To enable more succinct expression of this idiom, we allow the
following shorthand notation using `if` instead:

为了能够更简洁地表达这种惯用法，我们允许使用
如下基于 `if` 的简写表示法：

```lisp
(rule (lower (special_inst ...))
      (if (isa_extension_enabled))
      (isa_special_inst ...))
```

#### Recursion

#### 递归

ISLE terms may be recursive: a rewrite rule's RHS can reference the term it
matches on, either directly or via a reference cycle.  However, recursive terms
present a risk of potentially unbounded term rewriting. In the compilation
context, it is possible that certain recursive rules could be exploited to
induce a stack overflow with a malicious input program.  Therefore, ISLE
disallows recursion by default.

ISLE 项可以是递归的：重写规则的 RHS 可以直接或通过引用环来引用它所匹配的项。  然而，递归项
存在导致潜在无界项重写的风险。在编译上下文中，某些递归规则可能会被恶意输入程序利用，
从而诱发栈溢出。因此，ISLE
默认禁止递归。

Recursion can still be justified when it can be shown to be bounded, therefore
ISLE allows certain terms to opt-in to recursive definitions.  To permit
recursive references in a term's rules, declare the term with the `rec`
attribute: `(decl rec A ...)`. In the case of a reference cycle, all terms in
the cycle must have the `rec` attribute. When using the `rec` attribute,
developers should provide a `; Recursion: ...` comment explaining why this use
is bounded.

当可以证明递归是有界的时，递归仍然可以是合理的；因此
ISLE 允许某些项选择加入递归定义。要允许
某个项的规则中出现递归引用，请使用 `rec`
属性声明该项：`(decl rec A ...)`。在存在引用环的情况下，环中的所有项
都必须具有 `rec` 属性。使用 `rec` 属性时，
开发者应提供一条 `; Recursion: ...` 注释，说明为什么这种用法
是有界的。

## ISLE to Rust

## ISLE 到 Rust

Now that we have described the core ISLE language, we will document
how it interacts with Rust code. We consider these interactions to be
semantically as important as the core language: they are not
implementation details, but rather, a well-defined interface by which
ISLE can interface with the outside world (an "FFI" of sorts).

既然我们已经描述了核心 ISLE 语言，接下来将记录
它如何与 Rust 代码交互。我们认为这些交互在语义上
与核心语言同等重要：它们不是
实现细节，而是一个定义良好的接口，ISLE 可通过该接口与外部世界交互
（某种意义上的 "FFI"）。

### Mapping to Rust: Constructors, Functions, and Control Flow

### 映射到 Rust：构造器、函数和控制流

ISLE was designed to have a simple, easy-to-understand mapping from
its language semantics to Rust semantics. This means that the
execution of ISLE rewriting has a well-defined implementation in
Rust. The basic principles are:

ISLE 被设计为从
其语言语义到 Rust 语义具有简单且易于理解的映射。这意味着
ISLE 重写的执行在
Rust 中具有定义良好的实现。基本原则是：

1. Every term with rules in ISLE becomes a single Rust function. The
   arguments are the Rust function arguments. The term's "return
   value" is the Rust function's return value (wrapped in an `Option`
   because pattern coverage can be incomplete).

1. ISLE 中每个带有规则的项都会成为一个 Rust 函数。
   参数就是 Rust 函数参数。该项的“返回
   值”就是 Rust 函数的返回值（包装在 `Option` 中，
   因为模式覆盖可能是不完整的）。

2. One rewrite step is one Rust function call.

2. 一个重写步骤就是一次 Rust 函数调用。

3. Rewriting is thus eager, and reified through ordinary Rust control
   flow. When we construct a term that appears on the left-hand side
   of rules, we do so by calling a function (the "constructor body");
   and this function *is* the rewrite logic, so the term is rewritten
   as soon as it exists. The code that embeds the ISLE generated code
   will kick off execution by calling a top-level "driver"
   constructor. The body of the constructor will eventually choose one
   of several rules to apply, and execute code to build the right-hand
   side expression; this can invoke further constructors for its
   subparts, kicking off more rewrites, until eventually a value is
   returned.

3. 因此，重写是急切的，并通过普通的 Rust 控制流
   具现化。当我们构造一个出现在规则左侧的项时，
   是通过调用一个函数（“构造器主体”）来完成的；
   而这个函数*就是*重写逻辑，因此该项一经存在
   就会被重写。嵌入 ISLE 生成代码的代码
   将通过调用一个顶层“驱动”
   构造器来启动执行。该构造器的主体最终会选择
   若干规则之一来应用，并执行代码以构建右侧
   表达式；这可以为其子部分调用更多构造器，
   从而触发更多重写，直到最终返回一个值。

4. This design means that "intermediate terms" -- constructed terms
   that are then further rewritten -- are never actually built as
   in-memory data-structures. Rather, they exist only as ephemeral
   stack-frames while the corresponding Rust function executes. This
   means that there is very little or no performance penalty to
   factoring code into many sub-rules (subject only to function-call
   overhead and/or the effectiveness of the Rust inliner).

4. 这种设计意味着，“中间项”——先构造出来然后再被进一步重写的项——实际上从不会作为内存中的数据结构被构建出来。相反，它们只是在相应的 Rust 函数执行期间作为短暂存在的栈帧而存在。这意味着，将代码分解为许多子规则几乎没有或完全没有性能代价（只受函数调用开销和/或 Rust 内联器有效性的影响）。

5. Backtracking -- attempting to match rules, and backing up to follow
   a different path when a match fails -- exists, but is entirely
   internal to the generated Rust function for rewriting one
   term. Once we are rewriting a term, we have committed to that term
   existing as a rewrite step; we cannot backtrack further. However,
   backtracking can occur within the delimited scope of this one
   term's rewrite; we have a phase during which we evaluate left-hand
   sides, trying to find a matching rule, and once we find one, we
   commit and start to invoke constructors to build the right-hand
   side.

5. 回溯——尝试匹配规则，并在匹配失败时回退以沿另一条路径继续——是存在的，但完全局限于为重写一个项而生成的 Rust 函数内部。一旦我们开始重写某个项，就已经承诺该项作为一个重写步骤存在；我们不能再进一步回溯。不过，回溯可以发生在这个单个项的重写所限定的范围内；我们会有一个阶段来求值左侧，尝试找到匹配的规则，而一旦找到，就会提交并开始调用构造器来构建右侧。

   Said another way, the principle is that left-hand sides can be
   fallible, and have no side-effects as they execute; right-hand
   sides, in contrast, are infallible. This simplifies the control
   flow and makes reasoning about side-effects (especially with
   respect to external Rust actions) easier.

换句话说，其原则是：左侧可以失败，并且在执行时没有副作用；相反，右侧不会失败。这简化了控制流，并使得对副作用的推理（尤其是关于外部 Rust 动作的副作用）更加容易。

This will become more clear as we look at how Rust interfaces are
defined, and how the generated code appears, below.

随着我们在下文查看 Rust 接口如何定义以及生成的代码是什么样子，这一点会变得更加清楚。

### Extern Constructors and Extractors

### 外部构造器和提取器

ISLE programs interact with the surrounding Rust code in which they
are embedded by allowing the programmer to define a term to have
*external constructors* and an *external extractor*.

ISLE 程序通过允许程序员为一个项定义*外部构造器*和*外部提取器*，来与其嵌入其中的周围 Rust 代码交互。

The design philosophy of ISLE is that while internally it operates as
a fairly standard term-rewriting system, on the boundaries the "terms"
should be virtual, and defined procedurally rather than reified into
data structures, in order to allow for very flexible binding to the
embedding application. Thus, when term-rewriting bottoms out on the
input side, it just calls "extractors" to match on whatever ultimate
input the user provides, and these are fully programmable; and when it
bottoms out on the output side, the "term tree" is reified as a tree
of Rust function calls rather than plain data.

ISLE 的设计理念是：虽然在内部它作为一个相当标准的项重写系统运行，但在边界处，“项”应当是虚拟的，并且以过程化方式定义，而不是具体化为数据结构，以便能够非常灵活地绑定到嵌入它的应用。因此，当项重写在输入侧触底时，它只是调用“提取器”来匹配用户提供的任何最终输入，而这些提取器是完全可编程的；当它在输出侧触底时，“项树”会被具体化为一棵 Rust 函数调用树，而不是普通数据。

#### Constructors

#### 构造器

As we defined above, a "constructor" is a term form that appears in an
expression and builds its return value from its argument
values. During the rewriting process, a constructor that can trigger
further rewriting rules results in a Rust function call to the body of
the "internal constructor" built from these rules; the term thus never
exists except as argument values on the stack. However, ultimately the
ISLE code needs to return some result to the outside world, and this
result may be built up of many parts; this is where *external
constructors* come into play.

如上所定义，“构造器”是一种出现在表达式中的项形式，它从其参数值构建返回值。在重写过程中，能够触发进一步重写规则的构造器会导致对由这些规则构建的“内部构造器”主体进行 Rust 函数调用；因此，该项除了作为栈上的参数值之外从不存在。然而，最终 ISLE 代码需要向外部世界返回某个结果，而该结果可能由许多部分构建而成；这就是*外部构造器*发挥作用的地方。

For any term declared like

对于任何像下面这样声明的项

```lisp
    (decl T (A B C) U)
```

the programmer can declare

程序员可以声明

```lisp
    (extern constructor T ctor_func)
```

which means that there is a Rust function `ctor_func` on the context
trait (see below) that can be *invoked* with arguments of type `A`,
`B`, `C` (actually borrows `&A`, `&B`, `&C`, for non-primitive types)
and returns a `U`.

这意味着在上下文 trait（见下文）上存在一个 Rust 函数 `ctor_func`，它可以接受类型为 `A`、`B`、`C` 的参数（实际上对于非原始类型，传入的是 `&A`、`&B`、`&C` 的借用），并返回一个 `U`。

External constructors are infallible: that is, they must succeed, and
always return their return type. In contrast, internal constructors
can be fallible because they are implemented by a list of rules whose
patterns may not cover the entire domain (in which case, the term
should be marked `partial`). If fallible behavior is needed when
invoking external Rust code, that behavior should occur in an extractor
(see below) instead: only pattern left-hand sides are meant to be
fallible.

外部构造器是不会失败的：也就是说，它们必须成功，并且总是返回其返回类型。相比之下，内部构造器可能会失败，因为它们是通过一组规则实现的，而这些规则的模式可能无法覆盖整个定义域（在这种情况下，该项应标记为 `partial`）。如果在调用外部 Rust 代码时需要可失败的行为，那么这种行为应该发生在一个提取器（见下文）中：只有模式的左侧才应该是可失败的。

#### Extractors

#### 提取器

An *external extractor* is an implementation of matching behavior in
left-hand sides (patterns) that is fully programmable to interface
with the embedding application. When the generated pattern-matching
code is attempting to match a rule, and has a value to match against
an extractor pattern defined as an external extractor, it simply calls
a Rust function with the value of the term to be deconstructed, and
receives an `Option<(arg1, arg2, ...)>` in return. In other words, the
external extractor can choose to match or not, and if it does, it
provides the values that are in turn matched by sub-patterns.

外部提取器是在左侧（模式）中实现匹配行为的一种方式，它可以完全由程序控制，以便与嵌入的应用程序交互。当生成的模式匹配代码试图匹配某条规则，并且有一个值要与一个被定义为外部提取器的提取器模式匹配时，它会简单地调用一个 Rust 函数，传入要解构的项的值，并返回一个 `Option<(arg1, arg2, ...)>`。换句话说，外部提取器可以选择匹配或不匹配；如果它匹配，它就提供那些随后会被子模式匹配的值。

For any term declared like

对于任何像下面这样声明的项

```lisp
    (decl T (A B C) U)`
```

the programmer can declare

程序员可以声明

```lisp
    (extern extractor T etor_func)
```

which means that there is a Rust function `etor_func` on the context
trait (see below) that can be *invoked* with an argument of type `&U`,
and returns an `Option<(A, B, C)>`.

这意味着在上下文 trait（见下文）上存在一个 Rust 函数 `etor_func`，它可以接受一个类型为 `&U` 的参数，并返回一个 `Option<(A, B, C)>`。

If an extractor returns `None`, then the generated matching code
proceeds just as if an enum variant match had failed: it moves on to
try the next rule in turn.

如果提取器返回 `None`，那么生成的匹配代码的行为就与枚举变体匹配失败时完全一样：它会继续依次尝试下一个规则。

### Mapping Type Declarations to Rust

### 将类型声明映射到 Rust

When we declare a type like

当我们声明如下类型时

```lisp
    (decl MyEnum (enum
                   (A (x u32) (y u32))
                   (B)))
```

ISLE will generate the Rust type definition

ISLE 将生成 Rust 类型定义

```rust
#[derive(Clone, Debug)]
pub enum MyEnum {
    A { x: u32, y: u32, },
    B,
}
```

Note that enum variants with no fields take on the brace-less form,
while those with fields use the named-struct-field `A { x: ... }`
form. If all variants are field-less, then the type will additionally
derive `Copy`, `PartialEq`, and `Eq`.

请注意，没有字段的枚举变体采用不带花括号的形式，而带字段的变体则使用命名结构体字段形式 `A { x: ... }`。如果所有变体都没有字段，那么该类型还会派生 `Copy`、`PartialEq` 和 `Eq`。

If the type is declared as extern (`(decl MyEnum extern (enum ...))`)
then the same definition is assumed to exist. Primitives (`(decl u32
(primitive u32))`) are assumed to be defined already, and are required
to be `Copy`.

如果该类型被声明为 extern（`(decl MyEnum extern (enum ...))`），那么就假定存在同样的定义。原始类型（`(decl u32 (primitive u32))`）则假定已经定义，并且要求它们是 `Copy`。

All imported/extern types are pulled in via `use super::*` at the top
of the generated code; thus, these types should exist in (or be
re-exported from) the parent module.

所有导入的/外部的类型都会通过生成代码顶部的 `use super::*` 引入；因此，这些类型应当存在于父模块中（或从父模块重新导出）。

### Symbolic Constants

### 符号常量

ISLE allows the user to refer to external constants as follows:

ISLE 允许用户按如下方式引用外部常量：

```lisp
    (extern const $I32 Type)
```

This allows code to refer to `$I32` whenever a value of type `Type` is
needed, in either a pattern (LHS) or an expression (RHS). These
constants are pulled in via the same `use super::*` that imports all
external types.

这使得代码在需要某个 `Type` 类型的值时，可以在模式（LHS）或表达式（RHS）中使用 `$I32`。这些常量会通过同一个 `use super::*` 引入，它也会导入所有外部类型。

### Exported Interface: Functions and Context Trait

### 导出的接口：函数和上下文 trait

The generated ISLE code provides an interface that is designed to be
agnostic to the embedding application. This means that ISLE knows
nothing about, e.g., Cranelift or compiler concepts in
general. Rather, the generated code provides function entry points
with well-defined signatures based on the terms, and imports the
extern constructors and extractors via a context trait that the
embedder must implement.

生成的 ISLE 代码提供了一个接口，其设计与嵌入应用无关。这意味着 ISLE 对诸如 Cranelift 或一般编译器概念等内容一无所知。相反，生成的代码会基于这些 term 提供具有明确定义签名的函数入口点，并通过嵌入者必须实现的上下文 trait 导入外部构造器和提取器。

When a term `T` is defined like

当一个 term `T` 被定义为

```lisp
    (decl T (A B C) U)
```

and has an internal constructor (provided by `rule` bodies), then a
function with the following signature will be exported from the
generated code:

并且具有一个内部构造器（由 `rule` 主体提供）时，则会从生成的代码中导出一个具有以下签名的函数：

```rust
    pub fn constructor_T<C: Context>(ctx: &mut C, arg0: &A, arg1: &B, arg2: &C) -> Option<U>;
```

In other words, `constructor_` is prepended, and the function takes
the expected arguments, along with a "context" (more on this
below). It returns an `Option<U>` because internal constructors can be
partial: if no rule's pattern matches, then the constructor
fails. Note that if a sub-constructor fails, no backtracking occurs;
rather, the failure propagates all the way up to the entry point.

换句话说，前面会加上 `constructor_` 前缀，并且该函数会接收预期的参数，以及一个“上下文”（下面会进一步说明）。它返回一个 `Option<U>`，因为内部构造器可能是部分的：如果没有任何规则的模式匹配，则构造器失败。请注意，如果某个子构造器失败，不会发生回溯；相反，失败会一直向上传播，直到入口点。

What is this "context" for? The context argument is used to allow
external extractors and constructors to access the necessary state of
the embedding application. (For example, in Cranelift, it might be the
`LowerCtx` that controls the code-lowering process.)

这个“上下文”是用来做什么的？上下文参数用于让外部提取器和构造器访问嵌入应用所需的状态。（例如，在 Cranelift 中，它可能是控制代码下沉过程的 `LowerCtx`。）

The context is a trait because we want to decouple the generated code
from the application as much as possible. The trait will have a method
for each defined external extractor and constructor. For example, if
we have the following terms and declarations:

上下文之所以是 trait，是因为我们希望尽可能将生成的代码与应用解耦。该 trait 会为每个已定义的外部提取器和构造器提供一个方法。例如，如果我们有以下 term 和声明：

```lisp
    (decl A (u32 u32) T)
    (extern constructor A build_a)

    (decl B (T) U)
    (external extractor B disassemble_b)
```

then the `Context` trait will include these methods:

那么 `Context` trait 将包含这些方法：

```rust
    trait Context {
        fn build_a(&mut self, arg0: u32, arg1: u32) -> T;
        fn disassemble_b(&mut self, arg0: &U) -> Option<T>;
    }
```

These functions should be implemented as described above for external
constructors and extractors.

这些函数应按上文针对外部构造器和提取器所描述的方式实现。

Note that some external extractors are known to always succeed, for
example if they are just fetching some information that is always
present; in this case, the generated code can be made slightly more
efficient if we tell the ISLE compiler that this is so. By declaring

请注意，某些外部提取器已知总是成功的，例如它们只是获取一些始终存在的信息；在这种情况下，如果我们告知 ISLE 编译器这一点，生成的代码可以稍微更高效一些。通过声明

```lisp
    (external extractor infallible B disassemble_b)
```

we eliminate the `Option` on the return type, so the method is instead

我们就去掉了返回类型上的 `Option`，因此该方法改为

```rust
    trait Context {
        // ...
        fn disassemble_b(&mut self, arg0: &U) -> T;
    }
```

## ISLE Internals

## ISLE 内部实现

### Compiler Stages

### 编译阶段

Some detail and pointers to the compilation stages can be found in the
[README](../isle/README.md). The sequence starts as any ordinary
compiler: lexing, parsing, semantic analysis, and generation of an
IR. The most unique part is the "decision trie generation", which is
what converts the unordered-list-of-rule representation into something
that corresponds to the final Rust code's control flow and order of
matching operations.

关于编译阶段的一些细节和指引可以在 [README](../isle/README.md) 中找到。整个序列和普通编译器一样开始：词法分析、解析、语义分析，以及生成 IR。最独特的部分是“决策 trie 生成”，它将无序的规则列表表示转换为对应最终 Rust 代码中的控制流和匹配操作顺序的形式。

We describe this data structure below with the intent to provide an
understanding of how the DSL compiler weaves rules together into Rust
control flow. While this understanding shouldn't be strictly necessary
to use the DSL, it may be helpful. (The ultimate answer to "how does
the generated code work" is, of course, found by reading the generated
code; some care has been taken to ensure it is reasonably legible for
human consumption!)

下面我们描述这种数据结构，目的在于帮助理解 DSL 编译器如何将规则编织成 Rust 控制流。虽然使用该 DSL 并不严格需要理解这些内容，但这可能会有帮助。（关于“生成的代码如何工作”的最终答案，当然是阅读生成的代码；我们已经尽量让它对人类来说足够易读！）

### Decision Trie

### 决策 trie

The heart of the ISLE transformation lies in how the compiler converts
a list of rules into a scheme to attempt to match rules in some order,
possibly sharing match operations between similar rules to reduce
work.

ISLE 转换的核心在于编译器如何将
一组规则转换为一种按某种顺序尝试匹配规则的方案，
并可能在相似规则之间共享匹配操作以减少
工作量。

The core data structure we produce is a "decision trie" per internal
constructor body. This is an intermediate representation of sorts that
is built from individual-rule IR (LHS + RHS) sequences, and is then
used to generate Rust source.

我们生成的核心数据结构是每个内部
构造器主体对应的一个“决策 trie”。这可以算作一种中间表示，
它由单条规则的 IR（LHS + RHS）序列构建而成，随后
用于生成 Rust 源码。

The decision trie is, as the name implies, a kind of decision tree, in
the sense that we start at the root and move down the tree based on
the result of match operations (each feeding one "decision").

decision trie 顾名思义是一种决策树，也就是说，我们从根节点开始，
根据匹配操作的结果沿树向下移动（每个操作提供一个“决策”）。

It is a "trie" (which is a kind of tree) because at each level, its
edges are labeled with match operations; a trie is a tree where one
input character from an alphabet is used to index children at each
level.

之所以称它为“trie”（一种树），是因为在每一层，其
边都带有匹配操作的标签；trie 是一种树，其中字母表中的一个
输入字符用于在每一层索引子节点。

Each node in the tree is either an internal decision node, or a leaf
"expression" node (which we reach once we have a successful rule
match). The "execution semantics" of the trie are
backtracking-based. We attempt to find some path down the tree through
edges whose match ops run successfully; when we do this to reach a
leaf, we have the values generated by all of the match ops, and we can
execute the sequence of "expression instructions" in the leaf. Each
rule's left-hand side becomes a series of edges (merged into the
existing tree as we process rules) and each rule's right-hand side
becomes one leaf node with expression instructions.

树中的每个节点要么是内部决策节点，要么是叶子
“表达式”节点（当我们成功匹配到某条规则时就会到达这里）。trie 的“执行语义”是
基于回溯的。我们尝试沿着树向下寻找一条由
匹配操作成功运行的边组成的路径；当我们到达
叶子时，就已经获得了所有匹配操作生成的值，并且可以
执行叶子中的“表达式指令”序列。每条
规则的左侧会变成一系列边（在处理规则时并入现有树中），而每条规则的右侧
会变成一个带有表达式指令的叶节点。

At any point, if a match op does not succeed, we try the next out-edge
in sequence. If we have tried all out-edges from a decision node and
none were successful, then we backtrack one level further. Thus, we
simply perform an in-order tree traversal and find the first
successful match.

在任何时候，如果某个匹配操作没有成功，我们就按顺序尝试下一个出边。
如果我们已经尝试了某个决策节点的所有出边，
且都不成功，那么就再回溯一层。因此，我们
只需执行一次中序树遍历，并找到第一个
成功的匹配。

Though this sounds possibly very inefficient if some decision node has
a high fan-out, in practice it is not because the edges are often
known to be *mutually exclusive*. The canonical example of this is
when an enum-typed value is destructured into different variants by
various edges; we can use a Rust `match` statement in the generated
source and have `O(1)` (or close to it) cost for the dispatch at this
level.[^8]

虽然如果某个决策节点具有很高的分叉数，这听起来可能会非常低效，但实际上并不会，因为这些边通常被认为是 *互斥的*。一个典型的例子是，当一个枚举类型的值被不同的边解构为不同的变体时；我们可以在生成的源码中使用 Rust `match` 语句，并使这一层的分发开销达到 `O(1)`（或接近 `O(1)`）的成本。[^8]

[^8]: The worst-case complexity for a single term rewriting operation
      is still the cost of evaluating each rule's left-hand side
      sequentially, because in general there is no guarantee of
      overlap between the patterns. Ordering of the edges out of a
      decision node also affects complexity: if mutually-exclusive
      match operations are not adjacent, then they cannot be merged
      into a single `match` with `O(1)` dispatch. In general this
      ordering problem is quite difficult. We could do better with
      stronger heuristics; this is an open area for improvement in the
      DSL compiler!

[^8]: 单次项重写操作的最坏情况复杂度
      仍然是按顺序评估每条规则左侧的成本，
      因为一般无法保证模式之间存在
      重叠。决策节点的出边排序也会影响复杂度：如果互斥的
      匹配操作不相邻，那么它们就无法合并
      为一个带有 `O(1)` 分发的单个 `match`。总体而言，这个
      排序问题相当困难。我们可以通过更强的启发式方法做得更好；这在
      DSL 编译器中仍是一个有待改进的开放领域！

## Reference: ISLE Language Grammar

## 参考：ISLE 语言语法

Baseline: allow arbitrary whitespace, and wasm-style comments (`;` to
newline, or nested block-comments with `(;` and `;)`).

基线：允许任意空白，以及 wasm 风格注释（从 `;` 到
换行，或使用 `(;` 和 `;)` 的嵌套块注释）。

The grammar accepted by the parser is as follows:

解析器接受的语法如下：

```bnf
<skip> ::= <whitespace> | <comment>

<whitespace> ::= " "
               | "\t"
               | "\n"
               | "\r"

<comment> ::= <line-comment> | <block-comment>

<line-comment> ::= ";" <line-char>* (<newline> | eof)
<line-char> ::= <any character other than "\n" or "\r">
<newline> ::= "\n" | "\r"

<block-comment> ::= "(;" <block-char>* ";)"
<block-char> ::= <any character other than ";" or "(">
               | ";" if the next character is not ")"
               | "(" if the next character is not ";"
               | <block-comment>

<ISLE> ::= <def>*

<def> ::= "(" "pragma" <pragma> ")"
        | "(" "type" <typedecl> ")"
        | "(" "decl" <decl> ")"
        | "(" "rule" <rule> ")"
        | "(" "extractor" <extractor> ")"
        | "(" "extern" <extern> ")"
        | "(" "convert" <converter> ")"

;; No pragmas are defined yet
<pragma> ::= <ident>

<typedecl> ::= <ident> [ "extern" | "nodebug" ] <type-body>

<ident> ::= <ident-start> <ident-cont>*
<const-ident> ::= "$" <ident-cont>*
<ident-start> ::= <any non-whitespace character other than "-", "0".."9", "(", ")", ";", "#" or "$">
<ident-cont>  ::= <any non-whitespace character other than "(", ")", ";" or "@">

<type-body> ::= "(" "primitive" <ident> ")"
              | "(" "enum" <enum-variant>* ")"
              | "(" "struct" <fields> ")"

<enum-variant> ::= <ident>
                 | "(" <ident> <fields> ")"

<fields> ::= <struct-fields> | <tuple-fields>

<struct-fields> ::= <struct-field>*
<struct-field> ::= "(" <ident> <ty> ")"

<tuple-fields> ::= <tuple-field>*
<tuple-field> ::= <ty>

<ty> ::= <ident>

<decl> ::= [ "pure" ] [ "multi" ] [ "partial" ] [ "rec" ] <ident> "(" <ty>* ")" <ty>

<rule> ::= [ <ident> ] [ <prio> ] <pattern> <stmt>* <expr>

<prio> ::= <int>

<int> ::= [ "-" ] ( "0".."9" ) ( "0".."9" | "_" )*
        | [ "-" ] "0" ("x" | "X") ( "0".."9" | "A".."F" | "a".."f" | "_" )+
        | [ "-" ] "0" ("o" | "O") ( "0".."7" | "_" )+
        | [ "-" ] "0" ("b" | "B") ( "0".."1" | "_" )+

<pattern> ::= <int>
            | "true" | "false"
            | <const-ident>
            | "_"
            | <ident>
            | <ident> "@" <pattern>
            | "(" "and" <pattern>* ")"
            | "(" <ident> <pattern>* ")"

<stmt> ::= "(" "if-let" <pattern> <expr> ")"
         | "(" "if" <expr> ")"

<expr> ::= <int>
         | "true" | "false"
         | <const-ident>
         | <ident>
         | "(" "let" "(" <let-binding>* ")" <expr> ")"
         | "(" <ident> <expr>* ")"

<let-binding> ::= "(" <ident> <ty> <expr> ")"

<extractor> ::= "(" <ident> <ident>* ")" <pattern>

<extern> ::= "constructor" <ident> <ident>
           | "extractor" [ "infallible" ] <ident> <ident>
           | "const" <const-ident> <ty>

<converter> ::= <ty> <ty> <ident>
```

## Reference: ISLE Language Grammar verification extensions

## 参考：ISLE 语言语法验证扩展

```bnf
<def> += "(" "spec" <spec> ")"
       | "(" "model" <model> ")"
       | "(" "form" <form> ")"
       | "(" "instantiate" <instantiation> ")"

<spec> ::= "(" <ident> <ident>* ")" <provide> [ <require> ]
<provide> ::= "(" "provide" <spec-expr>* ")"
<require> ::= "(" "require" <spec-expr>* ")"

<model> ::= <ty> "(" "type" <model-ty> ")"
          | <ty> "(" "enum" <model-variant>* ")"

<model-ty> ::= "Bool"
             | "Int"
             | "Unit"
             | "(" "bv" [ <int> ] ")"

<model-variant> ::= "(" <ident> [ <spec-expr> ] ")"

<form> ::= <ident> <signature>*

<instantiation> ::= <ident> <signature>*
                  | <ident> <ident>

<spec-expr> ::= <int>
              | <spec-bv>
              | "true" | "false"
              | <ident>
              | "(" "switch" <spec-expr> <spec-pair>* ")"
              | "(" <spec-op> <spec-expr>* ")"
              | "(" <ident> ")"
              | "(" ")"

<spec-bv> ::= "#b" [ "+" | "-" ] ("0".."1")+
            | "#x" [ "+" | "-" ] ("0".."9" | "A".."F" | "a".."f")+

<spec-pair> ::= "(" <spec-expr> <spec-expr> ")"

<spec-op> ::= "and" | "not" | "or" | "=>"
            | "=" | "<=" | "<" | ">=" | ">"
            | "bvnot" | "bvand" | "bvor" | "bvxor"
            | "bvneg" | "bvadd" | "bvsub" | "bvmul"
            | "bvudiv" | "bvurem" | "bvsdiv" | "bvsrem"
            | "bvshl" | "bvlshr" | "bvashr"
            | "bvsaddo" | "subs"
            | "bvule" | "bvult" | "bvugt" | "bvuge"
            | "bvsle" | "bvslt" | "bvsgt" | "bvsge"
            | "rotr" | "rotl"
            | "extract" | "concat" | "conv_to"
            | "zero_ext" | "sign_ext"
            | "int2bv" | "bv2int"
            | "widthof"
            | "if" | "switch"
            | "popcnt" | "rev" | "cls" | "clz"
            | "load_effect" | "store_effect"

<signature>  ::= "(" <sig-args> <sig-ret> <sig-canon> ")"
<sig-args>   ::= "(" "args" <model-ty>* ")"
<sig-ret>    ::= "(" "ret" <model-ty>* ")"
<sig-canon>  ::= "(" "canon" <model-ty>* ")"
```
