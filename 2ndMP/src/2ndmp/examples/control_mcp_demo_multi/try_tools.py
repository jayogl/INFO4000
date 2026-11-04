"""Call the three tools directly -- no AI, no MCP. Works the same on macOS and Windows.

    uv run python try_tools.py
"""
import tools

print("simulate_pid(2, 8, 2)      ->", tools.simulate_pid(2, 8, 2))
print("design_rc_lowpass(1000, 10) ->", tools.design_rc_lowpass(1000, 10))
print("read_log_stats('temp_c', 220) ->", tools.read_log_stats("temp_c", 220))
