from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .ai_generation import GenerationError
from .daily_website_ready import (
    DAILYProductionError if False else DailyProductionError,
)
