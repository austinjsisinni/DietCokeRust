from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .compiler import (
    CompileError,
    analyze_source,
    compile_analysis,
    manifest_json,
    render_generation_prompt,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dietc",
        description="Translate Diet Rust (.dc) source into ordinary Rust.",
    )
    parser.add_argument("source", type=Path, help="Diet Rust source file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Rust output file (defaults to stdout)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="write the self-documentation and AI work-order manifest as JSON",
    )
    parser.add_argument(
        "--prompt",
        metavar="REQUEST",
        help="render one named generate block as an AI-ready prompt packet",
    )
    parser.add_argument(
        "--prompt-output",
        type=Path,
        help="write the rendered prompt to this path instead of stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.prompt_output is not None and args.prompt is None:
        print("dietc: --prompt-output requires --prompt", file=sys.stderr)
        return 2
    try:
        source = args.source.read_text(encoding="utf-8")
        analysis = analyze_source(source, source_name=str(args.source))
        generated = compile_analysis(analysis)
        prompt = (
            render_generation_prompt(analysis, source, args.prompt)
            if args.prompt
            else None
        )
    except OSError as error:
        print(f"dietc: {error}", file=sys.stderr)
        return 2
    except CompileError as error:
        print(f"dietc: {error}", file=sys.stderr)
        return 1

    if args.manifest is not None:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(manifest_json(analysis), encoding="utf-8")

    if args.output is None and prompt is None:
        sys.stdout.write(generated)
    elif args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(generated, encoding="utf-8")

    if prompt is not None:
        if args.prompt_output is None:
            sys.stdout.write(prompt)
        else:
            args.prompt_output.parent.mkdir(parents=True, exist_ok=True)
            args.prompt_output.write_text(prompt, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
