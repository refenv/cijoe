# Shell Modules

* Renamed `get_fib_range` to `cij::get_fib_range`
* `get_exp_2_range` to `cij::get_exp_2_range`
* vdbench: prefixed vars with `VDBENCH_`

# Tools

Changed `cij_reporter` it now takes the output path as positional argument
instead of optional named argument. E.g.:

```bash
# How it was
cij_reporter --output /path/to/output

# How it is now
cij_reporter /path/to/output
```
