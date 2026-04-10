from __future__ import annotations


class FormScorer:
    def __init__(self, spine_weight: float = 0.6, limb_weight: float = 0.4) -> None:
        self.spine_weight = spine_weight
        self.limb_weight = limb_weight

    def rep_score(self, angle: float, ideal_bottom: tuple[float, float], ideal_top: tuple[float, float]) -> float:
        low_ok = ideal_bottom[0] <= angle <= ideal_bottom[1]
        top_ok = ideal_top[0] <= angle <= ideal_top[1]
        if low_ok or top_ok:
            base = 95.0
        else:
            target = min(abs(angle - ideal_bottom[0]), abs(angle - ideal_bottom[1]), abs(angle - ideal_top[0]), abs(angle - ideal_top[1]))
            base = max(50.0, 100.0 - target)
        # Lightweight weighting proxy that emphasizes "critical" joints.
        return max(0.0, min(100.0, base * self.limb_weight + 100.0 * self.spine_weight))


class GamificationEngine:
    def __init__(self) -> None:
        self.session_scores: list[float] = []
        self.xp: int = 0
        self.high_form_streak: int = 0

    def register_rep(self, score: float) -> int:
        self.session_scores.append(score)
        if score >= 85.0:
            self.high_form_streak += 1
            bonus = 3 if self.high_form_streak >= 5 else 0
        else:
            self.high_form_streak = 0
            bonus = 0
        gained = int(score / 10) + 5 + bonus
        self.xp += gained
        return gained

    @property
    def session_score(self) -> float:
        if not self.session_scores:
            return 0.0
        return sum(self.session_scores) / len(self.session_scores)

