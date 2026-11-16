"""Possession inference placeholder."""


def infer_possession(*, ball_position: tuple[float, float] | None, player_positions: dict[str, tuple[float, float]]) -> str | None:
    """Future logic will return a track ID; absence of data returns no claim."""
    if ball_position is None or not player_positions:
        return None
    # TODO: infer possession from calibrated positions and time.
    return None
