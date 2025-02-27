# calculator-geshko-av

## What has been done?
This repository hosts a command-line calculator that supports integer and floating-point operations. It parses expressions with operators `( ) + - * /`, handles nested parentheses, and validates input to block invalid symbols or problematic constructs. If any invalid patterns or operations occur (like division by zero), the app quits with an error code.  
Unit tests check both “positive” scenarios (valid expressions) and “negative” ones that should trigger errors. Integration tests confirm end-to-end behavior.

## How to run/use it?
### Building and Running
- Clone the repository and run `make all` to build everything (the `app.exe` and `unit-tests.exe`).  
- Use `make run-int` for integer mode:  
  ```bash
  make run-int
  ```
  The program reads an expression from stdin or by typing after launch.
- Use `make run-float` for float mode:  
  ```bash
  make run-float
  ```
  Same usage, but with floating-point math.

### Testing
- `make run-unit-test` launches the Google Test–based unit tests.  
- `make run-integration-tests` runs Python-based integration tests (requires `pytest` in a virtual environment).

## How it’s made?
The core parser is written in C, split into functions like `parseExpression` and `parseFactor`, compiled with `gcc`. A `--float` flag toggles integer vs. float mode. Google Test (C++) covers unit tests, while Python’s `pytest` verifies integration flows. The Makefile automates building, formatting via `clang-format`, test execution, and environment setup. The design emphasizes checking invalid expressions early, and uses `exit(1)` on errors, guaranteeing safety before computations proceed.
