# Diet Rust language design

## 1. Identity

- **Language name:** Diet Rust
- **Source extension:** `.dc`
- **Compiler command:** `dietc`
- **Tagline:** *All the ownership. None of the sugar.*
- **Compilation target:** stable Rust

Diet Rust is a surface dialect rather than a fork of the Rust type system. Its
purpose is to make data-processing and staged workflows read like a beverage
production line while retaining access to the Rust ecosystem.

## 2. Design principles

1. **Rust underneath.** Ownership, borrowing, lifetimes, generics, async, and
   unsafe code keep their Rust meanings.
2. **Manufacturing should be visible.** Multi-stage transformations get a terse,
   left-to-right notation.
3. **Quality control is typed.** Programs should model raw, filtered, blended,
   carbonated, filled, and sealed states as different types.
4. **Ingredients have units.** APIs should prefer `Mg`, `Ml`, `Ph`, and
   `CarbonationVolumes` newtypes to ambiguous floating-point parameters.
5. **The joke stops at the error message.** Diagnostics should be precise and
   searchable; themed terminology must never hide what failed.
6. **Documentation is compiler input.** Purpose, preconditions, guarantees, and
   examples are structured data that also render as normal rustdoc.
7. **AI work is explicit.** Generation intent, context, constraints, output,
   and acceptance criteria belong in reviewable source control.

## 3. Ingredients as a standard vocabulary

The language does not hard-code a proprietary formula. Instead, its proposed
`diet_std::ingredients` module models the categories printed on a typical Diet
Coke ingredient label:

| Ingredient category | Suggested program role |
| --- | --- |
| Carbonated water | Base input and carrier |
| Caramel color | Appearance transform |
| Aspartame | Measured high-intensity sweetener |
| Phosphoric acid | Acidity adjustment |
| Potassium benzoate | Preservation policy |
| Natural flavors | User-defined, opaque flavor profile |
| Citric acid | Secondary acidity adjustment |
| Caffeine | Measured stimulant component |

Ingredient amounts should be values supplied by the program, not compiler
defaults. That keeps the language theme separate from claims about a real-world
commercial formulation.

## 4. Lexical and semantic model

Diet Rust accepts Rust tokens, comments, strings, raw strings, attributes,
macros, and delimiters. Outside comments and literals, the translator maps the
reserved words listed in the README to their Rust equivalents. Identifiers are
case-sensitive.

The following Rust words are intentionally unchanged because renaming them
would make the language harder to learn or would obscure safety semantics:

- ownership and flow: `move`, `ref`, `return`, `break`, `continue`, `drop`
- borrowing and safety: `unsafe`, `dyn`, `where`, `as`
- control flow: `if`, `else`, `for`, `while`, `loop`, `async`, `await`
- module system: `mod`, `use`, `crate`, `super`, `self`

### Reserved-word grammar

```text
item_fn       := ["served"] "formula" IDENT rust_fn_tail
item_struct   := ["served"] "can" IDENT rust_struct_tail
item_enum     := ["served"] "flavor" IDENT rust_enum_tail
item_trait    := ["served"] "recipe" IDENT rust_trait_tail
item_impl     := "bottle" rust_impl_tail
let_stmt      := "ingredient" ["adjustable"] rust_pattern [":" rust_type]
                 ["=" rust_expr] ";"
match_expr    := "taste" rust_expr "{" rust_match_arms "}"
const_item    := "chilled" IDENT ":" rust_type "=" rust_expr ";"
```

The `rust_*` productions deliberately defer to Rust's grammar after the themed
leading word.

### Standard Rust compatibility

Diet Rust is additive. Except for the small themed reserved-word set, stable
Rust syntax passes through to `rustc`:

| Rust area | Diet Rust behavior |
| --- | --- |
| Ownership, borrowing, lifetimes | Unchanged |
| Generics, const generics, `where` clauses | Unchanged |
| Structs, enums, unions, type aliases | Themed aliases available; Rust forms otherwise pass through |
| Traits, associated types, implementations | Unchanged after keyword lowering |
| Modules, visibility, crates, Cargo dependencies | Unchanged |
| Attributes, derive, crate docs, `no_std` | Preserved before generated compiler items |
| Declarative and procedural macros | Passed through to Rust |
| Closures, iterators, pattern matching | Unchanged |
| Async/await, threads, atomics | Unchanged |
| `unsafe`, raw pointers, FFI | Available under normal Rust rules |

## 5. Production expressions

```text
production_expr := "production" "!" "(" rust_expr stage+ [","] ")"
stage           := "=>" IDENT ["(" [rust_expr ("," rust_expr)* [","]] ")"]
```

Evaluation is left-to-right. The prior stage's output is inserted as the first
argument of the next function. A stage is evaluated exactly once.

```dietrust
production!(raw => filter => blend(syrup, color) => carbonate(2.7))
```

lowers to the conceptual Rust expression:

```rust
carbonate(blend(filter(raw), syrup, color), 2.7)
```

The reference compiler implements the construct as a hygienic Rust macro, so
the Rust compiler still owns name resolution and type checking.

### Sorting contract

Sorting is owned by the separate
[`diet-coke-sort`](https://github.com/austinjsisinni/diet-coke-sort) project.
Diet Rust's `sort!` macro is a thin language surface over that crate:

```text
sort!(values)                              -> diet_coke_sort::sort(values)
sort!(values, by comparator)               -> diet_coke_sort::sort_by(values, comparator)
sort!(values, flavor lime)                 -> DietCokeWithLime.sort(values)
sort!(values, flavor lime_caffeine_free)   -> DietCokeWithLimeCaffeineFree.sort(values)
```

This keeps algorithm ownership, stability guarantees, precision behavior, and
sorting assurance in one dedicated repository. The integration harness pins a
specific Git commit and its `Cargo.lock` records the resolved source. Standard
Rust APIs remain available for compatibility, but the official Diet Rust
sorting surface and examples use DietCokeSort.

## 6. Typestate manufacturing model

The recommended model uses a new type for each physical state:

```text
RawWater
   -> FilteredWater
   -> BlendedBatch
   -> CarbonatedBatch
   -> FilledCan
   -> SealedCan
   -> Batch<ReleasedCan, QualityError>
```

This is more than decoration. Given these signatures:

```dietrust
formula carbonate(batch: BlendedBatch, volumes: f32) -> CarbonatedBatch
formula fill(batch: CarbonatedBatch, size_ml: u16) -> FilledCan
formula seal(unit: FilledCan) -> SealedCan
```

the compiler rejects an attempt to seal a `BlendedBatch`, or to carbonate an
already filled can. Manufacturing order becomes a compile-time invariant.

## 7. Error and absence model

Diet Rust aliases Rust's established algebraic types rather than inventing new
semantics:

```dietrust
formula inspect(unit: SealedCan) -> Batch<ReleasedCan, QualityError> {
    if unit.fill_ml < 354 {
        return Recalled(QualityError::Underfilled);
    }
    Sealed(ReleasedCan { lot: unit.lot })
}

formula optional_caffeine() -> Supply<Mg> {
    Stocked(Mg(46.0))
}
```

The question-mark operator, iterator APIs, and the rest of Rust's `Result` and
`Option` ergonomics continue to work after translation.

## 8. Structured self-documentation

`guide` is an item-adjacent metadata block:

```text
guide_block := "guide" IDENT "{" guide_field+ "}"
guide_field := "purpose"  ":" STRING ";"
             | "requires" ":" STRING ";"
             | "ensures"  ":" STRING ";"
             | "example"  ":" STRING ";"
             | "note"     ":" STRING ";"
```

`purpose` occurs exactly once; all other fields may repeat. The block names the
symbol it describes and should immediately precede that item. Translation has
two outputs:

1. Markdown rustdoc attached to the following Rust item.
2. A JSON manifest entry retaining the fields, source line, file, and source
   digest for documentation generators and AI agents.

This dual representation keeps `cargo doc` useful while eliminating the need
for AI tooling to infer intent solely from implementation details.

## 9. AI generation declarations

`generate` declares desired work without making network access or nondeterminism
part of compilation:

```text
generate_block := "generate" IDENT "{" generate_field+ "}"
generate_field := "goal"       ":" STRING ";"
                | "target"     ":" STRING ";"
                | "context"    ":" STRING ";"
                | "constraint" ":" STRING ";"
                | "acceptance" ":" STRING ";"
                | "output"     ":" STRING ";"
                | "mode"       ":" STRING ";"
```

`goal` is required. `context`, `constraint`, and `acceptance` may repeat. A
prompt packet generated by `dietc --prompt NAME` includes the work order,
declared guides, complete source, safety protocol, and a SHA-256 digest. The
digest lets automation verify that a response was generated against the source
revision currently under review.

Generated code is never merged or executed automatically. The declared output
is a requested path, not write authority; an agent or developer must review,
write, translate, and test the result.

## 10. Compiler artifacts

One parse can produce three complementary artifacts:

| Artifact | Purpose |
| --- | --- |
| `.rs` | Deterministic code consumed by `rustc` |
| `.manifest.json` | Symbol intent and generation work orders for tools |
| `.prompt.md` | Reproducible, source-bound request for an AI coding agent |

The manifest is versioned independently through `schema_version`. Consumers
must ignore unknown fields so the protocol can grow without breaking older
tools.

## 11. Toolchain plan

The reference implementation is intentionally staged:

- **Stage 0 — included:** token-aware translator and `production!` lowering.
- **Stage 1 — included:** `guide` rustdoc, JSON manifests, `generate` work
  orders, deterministic prompt rendering, and source digests.
- **Stage 2:** source maps, `rustc` diagnostic remapping, and a `cargo-diet`
  subcommand.
- **Stage 3:** `rust-analyzer` bridge so `.dc` files get completion, guide
  previews, and inline diagnostics.
- **Stage 4:** optional `diet_std` crate containing unit newtypes and reusable
  typestate building blocks.

The dialect should not grow a separate borrow checker or package ecosystem.
Features that cannot lower clearly to Rust should face a high bar for inclusion.

## 12. Non-goals

- Reproducing or claiming knowledge of the commercial Diet Coke formula.
- Replacing Cargo, crates.io, rustfmt, Clippy, or rust-analyzer.
- Renaming every Rust keyword.
- Weakening Rust safety guarantees for the sake of themed syntax.
- Encoding a single factory's process as the only valid pipeline.
- Contacting an AI provider, accepting generated changes, or executing generated
  code as an implicit part of compilation.
- Reimplementing sorting algorithms already owned and tested by DietCokeSort.
