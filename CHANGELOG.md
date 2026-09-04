# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-11

### Added
- Initial release of **crest**: a generative terminal-art CLI
- **5 parametric patterns**: wave, plasma, gradient, mandala, ripple
- **8 colour maps**: mono, ember, fire, ocean, viridis, rainbow, ice, matrix
- **2 glyph styles**: Unicode blocks (shaded) and ASCII ramp
- **Live animation** with `animate` command
- **PNG export** via `export` command (optional Pillow dependency)
- **Interactive wizard** for guided setup and discovery
- **Zero core dependencies** — runs on any Python 3.8+ install
- Comprehensive test suite (30 tests)
- Shell integration helpers (fish and sh launchers)
- Full CLI documentation and usage examples

### Features
- Pure parametric generators (deterministic, no side effects)
- Modular architecture: patterns, colours, renderers, CLI
- ANSI truecolour terminal rendering
- Lazy-loaded optional dependencies (Pillow for PNG)
- Cross-platform support
- Terminal auto-detection for dimensions
