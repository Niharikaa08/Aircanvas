"""
utils/gesture_state.py
Landmark-based state machine with debounce to prevent jitter.
"""

from collections import deque


# Minimum consecutive frames a gesture must be held before committing
DEBOUNCE_FRAMES = {
    "DRAW":   2,
    "SELECT": 3,
    "ERASE":  4,
    "CLEAR":  8,   # harder to trigger accidentally
    "IDLE":   2,
}


class GestureStateMachine:
    """
    Accepts raw per-frame gesture labels and emits stable states.

    States: DRAW | SELECT | ERASE | CLEAR | IDLE
    """

    def __init__(self):
        self.current: str = "IDLE"
        self._candidate: str = "IDLE"
        self._count: int = 0
        self._history: deque[str] = deque(maxlen=30)  # for debugging

    def update(self, raw_gesture: str) -> str:
        """
        Feed the raw gesture detected this frame.
        Returns the stable (debounced) current state.
        """
        if raw_gesture == self._candidate:
            self._count += 1
        else:
            self._candidate = raw_gesture
            self._count = 1

        threshold = DEBOUNCE_FRAMES.get(raw_gesture, 3)
        if self._count >= threshold and raw_gesture != self.current:
            self.current = raw_gesture

        self._history.append(self.current)
        return self.current

    def reset(self):
        self.current = "IDLE"
        self._candidate = "IDLE"
        self._count = 0
        self._history.clear()

    @property
    def history(self) -> list:
        return list(self._history)
