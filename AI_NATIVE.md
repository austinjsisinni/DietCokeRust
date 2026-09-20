# AI-native development protocol

Diet Rust treats intent as source data and AI generation as an explicit build
artifact. The objective is not to let a probabilistic model sit inside the
compiler. It is to give developers and coding agents the same contracts,
context, constraints, and definition of done.

## `guide`: documentation with structure

Place a guide directly before the item it documents:

```dietrust
guide carbonate {
    purpose: "Add a measured volume of dissolved carbon dioxide.";
    requires: "The input is a BlendedBatch.";
    requires: "volumes is finite and positive.";
    ensures: "The result is typed as CarbonatedBatch.";
    example: "carbonate(batch, 2.7)";
    note: "Pressure control belongs to the hardware adapter.";
}
formula carbonate(batch: BlendedBatch, volumes: f32) -> CarbonatedBatch {
    // ...
}
```

The compiler emits Markdown rustdoc in the `.rs` output and preserves the
original structure in the JSON manifest. Repeated fields retain source order.
Raw Rust strings are accepted when examples contain many quotes.

Recommended guide coverage:

- Public types: purpose, invariants, and one construction example.
- Public functions: purpose, preconditions, guarantees, and error behavior.
- Unsafe functions: safety requirements as `requires` entries.
- Traits: behavioral guarantees expected from implementations.

## `generate`: a bounded AI work order

```dietrust
generate carbonation_properties {
    mode: "tests";
    target: "carbonate";
    goal: "Generate tests for valid and invalid carbonation measurements.";
    context: "Use the carbonate guide and existing batch typestates.";
    constraint: "Do not change production function signatures.";
    constraint: "Do not add dependencies.";
    acceptance: "Covers zero, negative, nominal, and non-finite values.";
    acceptance: "All tests compile as standard Rust after translation.";
    output: "tests/generated_carbonation.dc";
}
```

Field meanings:

| Field | Cardinality | Meaning |
| --- | --- | --- |
| `goal` | exactly one | Desired outcome, not implementation instructions |
| `target` | zero or one | Symbol or subsystem to modify |
| `context` | repeatable | Relevant types, guides, modules, or decisions |
| `constraint` | repeatable | Boundaries the generated change must preserve |
| `acceptance` | repeatable | Verifiable completion conditions |
| `output` | zero or one | Requested destination; never implicit write authority |
| `mode` | zero or one | `create`, `extend`, `replace`, `tests`, or `docs` |

## Artifact workflow

```powershell
python -m dietc examples/ai_native.dc `
  -o build/ai_native.rs `
  --manifest build/ai_native.manifest.json

python -m dietc examples/ai_native.dc `
  --prompt quality_rule_tests `
  --prompt-output build/quality_rule_tests.prompt.md
```

The manifest is suitable for documentation indexes, retrieval, task discovery,
and policy checks. The prompt packet is suitable for a developer-selected AI
agent. It contains the full current source and its digest, making stale prompts
detectable during review.

## Trust boundary

The translator is deterministic and does not use the network. It does not call
a model, write a request's declared output, run generated code, or approve a
change. Those remain deliberate actions in the surrounding development
workflow. This boundary preserves reproducible builds and makes AI involvement
auditable in version control.

## Standard Rust remains available

AI-oriented metadata does not define a second execution model. After guides and
generation declarations are extracted, the remaining program is regular Rust.
That includes lifetimes, generics, const generics, trait bounds, associated
types, macros, async/await, attributes, modules, Cargo dependencies, `no_std`,
unsafe code, raw pointers, and FFI.
