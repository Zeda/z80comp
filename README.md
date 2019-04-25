# z80comp
(This is still a work-in-progress!)

This project is on [**GitHub**](https://github.com/Zeda/z80comp) if you want to contribute or report issues!

## Goal
The goal of this project is to compile higher-level code to decent Z80 assembly. At the time of this writing, it isn't producing decent assembly, but at least it is producing working assembly!

## Getting Started
First, download the files! An example input is in [`test.txt`](test.txt)
In order to compile that to assembly, first we pass it through [`sy.py`](sy.py) which basically converts each line to [Reverse Polish Notation](https://en.wikipedia.org/wiki/Reverse_Polish_notation)-like.
```
python sy.py test.txt test.rpn
```
Then we pass `test.rpn` through [`irToZ80.py`](irToZ80.py) to generate the assembly code. This goes through each line of RPN and generates an [Abstract Syntax Tree](https://en.m.wikipedia.org/wiki/Abstract_syntax_tree) and then performs optimizations on the input. Then it converts back to an RPN-like notation and compiles it bottom-up to generate assembly code. See [**below**](#algorithm-description) for a more in-depth explanation of how it works.
```
python compile.py -TI8X -MAX_PATHS=150 test.rpn
```
This generates code with headers for the TI-83+/84+ series of calculators, and limits the search depth to 150 paths. Setting `MAX_PATHS` to 0 will remove the limit, but you may get stuck for hours trying to compile a single line of code (paths grow exponentially, so even short expressions can have millions of paths to search)! Smaller numbers bigger than 0 will compile faster, but won't necessarily produce the best code that this program can create. 150 seems to be a good trade-off; the default is set to 100.

## Algorithm Description

In order to create an optimal code, it uses a modified version of [Dijkstra's Shortest Path Algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm). For every token, there are one or more potential assembly codes, with various sizes and speeds. We keep a list of paths, and find the current shortest path. We determine the shortest based on the total size and speed along with modifiers `SPEED_MOD` and `SIZE_MOD`:
```
SPEED_MOD=0.0 would mean that only size matters in optimization
SIZE_MOD =0.0 would mean that only speed matters in optimization
SPEED_MOD=1.0, SIZE_MOD=6.0 would mean we are willingly to gain 1 byte to save 6cc.
```
With our current shortest path, if it has reached the end of the source code, we have our best code! Otherwise, we need to advance to the next token and append our new set of paths to try.

Because this could easily explode into millions of potential paths, we do some pruning. If we reach our max number of paths (`MAX_PATHS`) and have a path that has parsed 2 tokens while all of the rest have already parsed 4 tokens, we should get rid of that one!

## Problems
* In the pruning described above, if all paths are at the same token, this might actually prune our best path!
* Ideally, instead of RPN->AST->RPN, we should parse directly into an AST. This will be necessary when we add functions that can have variable numbers of arguments.
