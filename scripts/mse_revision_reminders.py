#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json

from mse.reminders import send_revision_reminders


async def main() -> None:
    result = await send_revision_reminders()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
