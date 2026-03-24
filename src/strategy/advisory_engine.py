from src.strategy.position_advisory_engine import PositionAdvisoryEngine

class AdvisoryEngine(PositionAdvisoryEngine):
    """
    Legacy wrapper for PositionAdvisoryEngine.
    """
    def __init__(self):
        super().__init__()
