import re
import pytest
from aioresponses import aioresponses

from jeedomdaemon.aio_connector import Publisher

class TestPublisher():

    @pytest.mark.asyncio
    async def test_send_to_jeedom(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            with aioresponses() as mocked:
                pattern = re.compile(r'^http://local/\?apikey=.*$')
                mocked.get(pattern, status=200, body='test')
                mocked.post(pattern, status=200, body='test')
                resp = await pub.send_to_jeedom({})
                assert resp == True

    @pytest.mark.asyncio
    async def test_send_to_jeedom_timeout(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            with aioresponses() as mocked:
                pattern = re.compile(r'^http://local/\?apikey=.*$')
                mocked.post(pattern, status=200, timeout=True)
                resp = await pub.send_to_jeedom({})
                assert resp == False

    @pytest.mark.asyncio
    async def test_add_change_basic(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('val', 51)
            assert pub.changes == {'val': 51}

    @pytest.mark.asyncio
    async def test_add_change_None(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('val', None)
            assert pub.changes == {}

    @pytest.mark.asyncio
    async def test_add_change_compose(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('val::51', 51)
            await pub.add_change('val::5', 5)
            assert pub.changes == {'val': {'5': 5, '51': 51}}

    @pytest.mark.asyncio
    async def test_merge_changes(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('val::51', 51)
            await pub.add_change('val::5', 5)
            assert pub.changes == {'val': {'5': 5, '51': 51}}

            await pub.add_change('val::5', 7)
            assert pub.changes == {'val': {'5': 7, '51': 51}}

    @pytest.mark.asyncio
    async def test_merge_changes_None(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('value_5', 5)
            await pub.add_change('value_10', 10)
            assert pub.changes == {'value_5': 5, 'value_10': 10}
            await pub.add_change('value_10', None)
            assert pub.changes == {'value_5': 5, 'value_10': 10}

    @pytest.mark.asyncio
    async def test_merge_changes_None_level(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('val::value_5', 5)
            await pub.add_change('val::value_10', 10)
            assert pub.changes == {'val': {'value_5': 5, 'value_10': 10}}
            await pub.add_change('val::value_10', None)
            assert pub.changes == {'val': {'value_5': 5, 'value_10': 10}}

    @pytest.mark.asyncio
    async def test_merge_changes_empty_string(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('value_int', 5)
            await pub.add_change('value_string', "test")
            assert pub.changes == {'value_int': 5, 'value_string': 'test'}
            await pub.add_change('value_string', '')
            assert pub.changes == {'value_int': 5, 'value_string': ''}

    @pytest.mark.asyncio
    async def test_merge_changes_with_0(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('val::51', 51)
            await pub.add_change('val::5_or_0', 5)
            assert pub.changes == {'val': {'5_or_0': 5, '51': 51}}

            await pub.add_change('val::5_or_0', 0)
            assert pub.changes == {'val': {'5_or_0': 0, '51': 51}}