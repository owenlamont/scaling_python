"""Run with: python -m unittest discover -s tests -v (requires aiohttp and pandas)."""

import asyncio
import io
import json
from pathlib import Path
import socket
import unittest

import aiohttp
from aiohttp import web
import pandas as pd


class AsyncDownloadTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        notebook = json.loads(
            (
                Path(__file__).resolve().parents[1] / "scaling_up_python.ipynb"
            ).read_text()
        )
        source = next(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
            and "async def download_file(" in "".join(cell["source"])
        )
        self.functions = {"pd": pd, "aiohttp": aiohttp, "io": io, "asyncio": asyncio}
        exec(
            compile(source, "scaling_up_python.ipynb:async-downloads", "exec"),
            self.functions,
        )

        async def respond(request):
            status = int(request.match_info["status"])
            value = request.match_info["value"]
            if value == "slow":
                await asyncio.sleep(0.02)
            # Even an error body can be valid CSV, so parsing alone is not validation.
            return web.Response(status=status, text=f"value\n{value}\n")

        app = web.Application()
        app.router.add_get("/{status}/{value}", respond)
        runner = web.AppRunner(app)
        await runner.setup()
        self.addAsyncCleanup(runner.cleanup)
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        self.base_url = f"http://127.0.0.1:{sock.getsockname()[1]}"
        await web.SockSite(runner, sock).start()

    async def test_successful_response_is_parsed(self):
        async with aiohttp.ClientSession() as session:
            frame = await self.functions["download_file"](
                session, f"{self.base_url}/200/data"
            )
        pd.testing.assert_frame_equal(frame, pd.DataFrame({"value": ["data"]}))

    async def test_http_errors_are_not_parsed_as_data(self):
        async with aiohttp.ClientSession() as session:
            for status in (404, 500):
                with self.subTest(status=status):
                    with self.assertRaises(aiohttp.ClientResponseError) as raised:
                        await self.functions["download_file"](
                            session, f"{self.base_url}/{status}/error"
                        )
                    self.assertEqual(raised.exception.status, status)

    async def test_batch_propagates_http_failure(self):
        with self.assertRaises(aiohttp.ClientResponseError):
            await self.functions["download_file_list"](
                [f"{self.base_url}/200/data", f"{self.base_url}/404/error"]
            )

    async def test_successful_batch_preserves_input_order(self):
        frames = await self.functions["download_file_list"](
            [f"{self.base_url}/200/slow", f"{self.base_url}/200/fast"]
        )
        self.assertEqual([frame.iloc[0, 0] for frame in frames], ["slow", "fast"])


if __name__ == "__main__":
    unittest.main()
