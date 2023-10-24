from _typeshed import Incomplete

class LinuxCNC_Exception(Exception): ...

class LinuxCNC:
    command: Incomplete
    status: Incomplete
    error: Incomplete
    def __init__(self, command: Incomplete | None = ..., status: Incomplete | None = ..., error: Incomplete | None = ...) -> None: ...
    def wait_for_linuxcnc_startup(self, timeout: float = ...) -> None: ...
    def all_joints_homed(self, joints): ...
    def wait_for_home(self, joints, timeout: float = ...) -> None: ...
    def wait_for_axis_to_stop(self, axis_letter, timeout: float = ...) -> None: ...
    def jog_axis(self, axis_letter, target, vel: float = ..., timeout: float = ...): ...
    def wait_for_axis_to_stop_at(self, axis_letter, target, timeout: float = ..., tolerance: float = ...) -> None: ...
    def wait_for_interp_state(self, target_state, timeout: float = ...) -> None: ...
    def wait_for_tool_in_spindle(self, expected_tool, timeout: float = ...) -> None: ...
