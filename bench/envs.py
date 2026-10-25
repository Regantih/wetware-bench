import numpy as np


class MiniPong:
    """Minimal 1-paddle Pong in a unit box.

    Paddle lives on the left wall (action 0 = up, 1 = down); top, bottom and
    right walls bounce. A left-wall return covered by the paddle is +1, a
    miss is -1 and respawns the ball. Deliberately tiny — the interesting
    part is the substrate, not the game.
    """

    def __init__(self, seed: int = 0, paddle_h: float = 0.2,
                 paddle_v: float = 0.07, ball_v: float = 0.035,
                 shape: float = 0.0):
        self.rng = np.random.default_rng(seed)
        self.paddle_h, self.paddle_v, self.ball_v = paddle_h, paddle_v, ball_v
        self.shape = shape  # dense shaping weight; 0 = sparse rewards only
        self.py = 0.5
        self.hits = 0
        self.arrivals = 0
        self._spawn()

    def _spawn(self) -> None:
        self.bx, self.by = 0.5, self.rng.uniform(0.3, 0.7)
        ang = self.rng.uniform(-0.35, 0.35) * np.pi
        self.vx = -self.ball_v * np.cos(ang)
        self.vy = self.ball_v * np.sin(ang)

    def obs(self) -> np.ndarray:
        return np.array([self.bx, self.by,
                         self.vx / self.ball_v, self.vy / self.ball_v, self.py])

    def step(self, action: int) -> float:
        self.py = float(np.clip(
            self.py + (-self.paddle_v if action == 0 else self.paddle_v),
            self.paddle_h / 2, 1 - self.paddle_h / 2))
        self.bx += self.vx
        self.by += self.vy
        if self.by <= 0 or self.by >= 1:
            self.vy *= -1
            self.by = float(np.clip(self.by, 0, 1))
        if self.bx >= 1:
            self.vx *= -1
            self.bx = 2 - self.bx
        if self.bx <= 0:
            self.arrivals += 1
            if abs(self.by - self.py) <= self.paddle_h / 2:
                self.vx *= -1
                self.bx = -self.bx
                self.hits += 1
                return 1.0
            self._spawn()
            return -1.0
        # dense shaping: small reward for keeping the paddle aligned with the
        # ball while it's inbound — gives learners signal between sparse hits
        if self.shape and self.vx < 0:
            return self.shape * (1.0 - min(1.0, abs(self.by - self.py)))
        return 0.0
