from __future__ import annotations

import unittest

from dietc import (
    CompileError,
    analyze_source,
    compile_source,
    manifest_json,
    render_generation_prompt,
)


class CompilerTests(unittest.TestCase):
    def body(self, source: str) -> str:
        return compile_source(source).split("\n\n", 2)[-1]

    def test_translates_dialect_vocabulary(self) -> None:
        generated = compile_source(
            "served formula main() { ingredient adjustable cans = 1; "
            "taste Stocked(cans) { Stocked(n) => label!(\"{}\", n), "
            "Empty => label!(\"none\") } }"
        )
        self.assertIn("pub fn main()", generated)
        self.assertIn("let mut cans = 1", generated)
        self.assertIn("match Some(cans)", generated)
        self.assertIn('Some(n) => println!("{}", n)', generated)
        self.assertIn('None => println!("none")', generated)

    def test_label_is_only_special_as_a_macro(self) -> None:
        generated = compile_source(
            'can Package { label: &\'static str } '
            'formula show(x: Package) { label ! ("{}", x.label); }'
        )
        self.assertIn("struct Package { label: &'static str }", generated)
        self.assertIn('println ! ("{}", x.label)', generated)

    def test_does_not_translate_comments_or_literals(self) -> None:
        source = '''// formula ingredient label
formula words() {
    label!("formula ingredient label");
    ingredient raw = r#"taste Sealed can"#;
    /* nested /* formula */ ingredient */
}
'''
        generated = compile_source(source)
        self.assertIn("// formula ingredient label", generated)
        self.assertIn('"formula ingredient label"', generated)
        self.assertIn('r#"taste Sealed can"#', generated)
        self.assertIn("/* nested /* formula */ ingredient */", generated)
        self.assertIn("fn words()", generated)

    def test_preserves_lifetimes_and_character_literals(self) -> None:
        source = "formula first<'a>(x: &'a str) -> char { ingredient c = 'x'; c }"
        generated = compile_source(source)
        self.assertIn("fn first<'a>(x: &'a str)", generated)
        self.assertIn("let c = 'x'", generated)

    def test_includes_production_macro(self) -> None:
        generated = compile_source(
            "formula main() { ingredient x = "
            "production!(raw => filter => blend(1, 2) => seal); }"
        )
        self.assertIn("macro_rules! production", generated)
        self.assertIn(
            "production!(raw => filter => blend(1, 2) => seal)", generated
        )

    def test_reports_mismatched_delimiter_with_location(self) -> None:
        with self.assertRaisesRegex(
            CompileError, r"plant\.dc:2:5: expected '\}'"
        ):
            compile_source("formula main() {\n    ]\n}", "plant.dc")

    def test_reports_unterminated_raw_string(self) -> None:
        with self.assertRaisesRegex(CompileError, "unterminated raw string"):
            compile_source('formula main() { r#"not done; }')

    def test_guide_becomes_rustdoc_and_manifest_data(self) -> None:
        source = '''guide inspect {
    purpose: "Release conforming units.";
    requires: "The unit is sealed.";
    ensures: "Rejected units return a reason.";
    example: r#"inspect(unit)"#;
}
served formula inspect() {}
'''
        analysis = analyze_source(source, "line.dc")
        generated = compile_source(source, "line.dc")

        self.assertIn("/// # Diet Rust guide: `inspect`", generated)
        self.assertIn("/// ## Guarantees", generated)
        self.assertIn("pub fn inspect()", generated)
        self.assertEqual(analysis.guides[0].purpose, "Release conforming units.")
        self.assertEqual(analysis.guides[0].requires, ("The unit is sealed.",))
        self.assertIn('"schema_version": 1', manifest_json(analysis))
        self.assertIn('"source": "line.dc"', manifest_json(analysis))

    def test_generate_block_becomes_prompt_not_rust(self) -> None:
        source = '''generate boundary_tests {
    mode: "tests";
    goal: "Generate boundary tests.";
    target: "inspect";
    context: "Use QualityError.";
    constraint: "No external crates.";
    acceptance: "The underfilled case is rejected.";
    output: "tests/generated.dc";
}
formula inspect() {}
'''
        analysis = analyze_source(source, "plant.dc")
        generated = compile_source(source, "plant.dc")
        prompt = render_generation_prompt(analysis, source, "boundary_tests")

        self.assertNotIn("generate boundary_tests", generated)
        self.assertIn("AI generation request `boundary_tests`", generated)
        self.assertEqual(analysis.generation_requests[0].mode, "tests")
        self.assertIn("Goal: Generate boundary tests.", prompt)
        self.assertIn("- No external crates.", prompt)
        self.assertIn("Source SHA-256:", prompt)
        self.assertIn("```dietrust", prompt)

    def test_metadata_words_inside_comments_and_strings_are_untouched(self) -> None:
        source = '''// generate fake { goal: "no"; }
formula words() {
    ingredient text = "guide fake { purpose: no; }";
}
'''
        analysis = analyze_source(source)
        self.assertEqual(analysis.guides, ())
        self.assertEqual(analysis.generation_requests, ())
        self.assertIn('"guide fake { purpose: no; }"', analysis.rust_body)

    def test_standard_rust_features_pass_through(self) -> None:
        source = '''//! Crate documentation stays at the crate root.
#![allow(dead_code)]
use std::future::Future;
served async formula collect<const N: usize, F, Fut>(adjustable f: F) -> [u8; N]
where F: FnMut() -> Fut, Fut: Future<Output = u8> {
    ingredient adjustable out = [0; N];
    ingredient closure = |x: u8| x + 1;
    out[0] = closure(f().await);
    out
}
unsafe formula raw(pointer: *const u8) -> u8 { unsafe { *pointer } }
'''
        generated = compile_source(source)
        self.assertLess(generated.index("//! Crate documentation"), generated.index("macro_rules!"))
        self.assertLess(generated.index("#![allow(dead_code)]"), generated.index("macro_rules!"))
        self.assertIn("pub async fn collect<const N: usize, F, Fut>", generated)
        self.assertIn("where F: FnMut() -> Fut", generated)
        self.assertIn("let closure = |x: u8| x + 1", generated)
        self.assertIn("unsafe fn raw(pointer: *const u8)", generated)

    def test_metadata_validation_is_actionable(self) -> None:
        with self.assertRaisesRegex(CompileError, "requires field 'purpose'"):
            analyze_source('guide inspect { ensures: "safe"; }', "bad.dc")
        with self.assertRaisesRegex(CompileError, "unknown generation request"):
            render_generation_prompt(analyze_source("formula main() {}"), "", "missing")


if __name__ == "__main__":
    unittest.main()
