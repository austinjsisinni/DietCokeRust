# Diet Rust

Diet Rust is a Rust-compatible, AI-native language inspired by Diet Coke's
ingredient list and manufacturing line. Ownership, borrowing, generics,
pattern matching, async, macros, and zero-cost abstractions are unchanged. The
dialect adds manufacturing vocabulary, typed production pipelines, structured
self-documentation, and reviewable AI code-generation work orders.

```dietrust
served formula main() {
    ingredient finished = production!(
        source
        => filter
        => blend(ASPARTAME_MG, CAFFEINE_MG)
        => carbonate(2.7)
        => fill(355)
        => seal
    );

    taste inspect(finished) {
        Sealed(unit) => label!("released: {:?}", unit),
        Recalled(reason) => label!("recalled: {:?}", reason),
    }
}
```

The reference compiler, `dietc`, translates `.dc` files into ordinary `.rs`
files. It deliberately stays small: Rust remains the optimizer, type checker,
borrow checker, package manager, and final compiler.

## Self-documenting by construction

A `guide` block records intent and contracts in a form that both people and AI
tools can consume. During translation it becomes ordinary rustdoc; the same
data is also available in a versioned JSON manifest.

```dietrust
guide inspect {
    purpose: "Release only conforming sealed cans.";
    requires: "The value came from seal.";
    ensures: "Every rejection includes a QualityError.";
    example: "inspect(unit)?";
}
formula inspect(unit: SealedCan) -> Batch<ReleasedCan, QualityError> {
    // implementation
}
```

`purpose` is required. `requires`, `ensures`, `example`, and `note` may be
repeated. Because guides live next to code, changing the contract is a visible
source change rather than an update to an external prompt.

## AI-native code generation

`generate` blocks are explicit, version-controlled work orders. They never run
a model as a hidden compiler side effect; `dietc` turns them into deterministic
prompt packets containing constraints, acceptance criteria, relevant guides,
the current source, and its SHA-256 digest.

```dietrust
generate inspection_tests {
    mode: "tests";
    target: "inspect";
    goal: "Generate boundary and property-focused inspection tests.";
    context: "Use the QualityError variants in this module.";
    constraint: "Use only the Rust standard library.";
    acceptance: "Underfilled and low-carbonation units are rejected.";
    output: "tests/generated_inspection.dc";
}
```

Supported modes are `create`, `extend`, `replace`, `tests`, and `docs`. Context,
constraints, and acceptance criteria may be repeated.

## Vocabulary

| Diet Rust | Rust | Manufacturing idea |
| --- | --- | --- |
| `formula` | `fn` | A repeatable formulation |
| `ingredient` | `let` | A measured input |
| `adjustable` | `mut` | A quantity that may be changed |
| `served` | `pub` | Released for public consumption |
| `chilled` | `const` | Kept fixed |
| `can` | `struct` | A shaped container |
| `flavor` | `enum` | One of several variants |
| `recipe` | `trait` | A required formulation contract |
| `bottle` | `impl` | A concrete packaged implementation |
| `taste` | `match` | Inspect a value and choose a branch |
| `Batch<T, E>` | `Result<T, E>` | A batch that passes or fails QC |
| `Sealed(value)` | `Ok(value)` | A releasable batch |
| `Recalled(error)` | `Err(error)` | A rejected batch |
| `Supply<T>` | `Option<T>` | An ingredient that may be available |
| `Stocked(value)` | `Some(value)` | Ingredient is available |
| `Empty` | `None` | Ingredient is unavailable |
| `label!` | `println!` | Apply a human-readable label |

All other Rust syntax remains valid. In particular, Diet Rust passes through
lifetimes, generic and const-generic parameters, associated types, `where`
clauses, modules, attributes, declarative macros, closures, iterators, async and
await, unsafe blocks, FFI declarations, and crate-level documentation. The
themed words in the table are reserved.

## The production pipeline

`production!` passes the result of each stage as the first argument of the next
stage:

```dietrust
production!(water => filter => blend(sweetener) => carbonate(2.7))
```

is equivalent to:

```rust
carbonate(blend(filter(water), sweetener), 2.7)
```

Stages can have no extra arguments or a comma-separated argument list. Their
normal Rust function signatures do the safety work. A plant can model each
stage as a distinct type, making `seal(raw_water)` or `fill(unfiltered_batch)`
impossible to compile.

## Try it

Python 3.11+ is the only dependency needed for the reference translator.

```powershell
python -m dietc examples/atlanta_plant.dc -o build/atlanta_plant.rs
python -m dietc examples/ai_native.dc `
  -o build/ai_native.rs `
  --manifest build/ai_native.manifest.json `
  --prompt quality_rule_tests `
  --prompt-output build/quality_rule_tests.prompt.md
python -m unittest discover -s tests -v
```

On Windows, the repository includes an end-to-end runner that translates both
examples, executes the Python tests, compiles the generated Rust, and runs the
factory program:

```powershell
.\scripts\test_local.ps1
```

The runner locates the installed MSVC and Windows SDK libraries for its own
process and does not modify the user's global `LIB` setting.

If Rust is installed, compile the generated file normally:

```powershell
rustc build/atlanta_plant.rs -o build/atlanta_plant
```

See [AI_NATIVE.md](AI_NATIVE.md) for the AI development protocol and
[DESIGN.md](DESIGN.md) for the language rationale, grammar, ingredient model,
and roadmap. A complete mixed Rust/AI example lives in
[`examples/ai_native.dc`](examples/ai_native.dc).
