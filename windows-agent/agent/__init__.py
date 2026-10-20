"""Employee Device Manager - Windows agent (prototype).

Collects device health and foreground application usage (application names and
durations only) and reports them to the management backend. It does NOT record
keystrokes, clipboard contents, window titles, URLs, or page contents.
"""

AGENT_VERSION = "0.6.0"
