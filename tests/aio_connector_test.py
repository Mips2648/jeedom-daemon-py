import re
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from aioresponses import aioresponses

from jeedomdaemon.aio_connector import Publisher


class TestPublisher():

    @pytest.mark.asyncio
    async def test_send_to_jeedom(self):
        received = []

        async def handler(request: web.Request):
            received.append((request.query.get('apikey'), await request.json()))
            return web.Response(text='test')

        app = web.Application()
        app.router.add_post('/', handler)
        async with TestServer(app) as server:
            async with Publisher(str(server.make_url('/')), 'cnysltyql') as pub:
                resp = await pub.send_to_jeedom({'val': 51})
                assert resp is True

        assert received == [('cnysltyql', {'val': 51})]

    @pytest.mark.asyncio
    async def test_send_to_jeedom_timeout(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            with aioresponses() as mocked:
                pattern = re.compile(r'^http://local/\?apikey=.*$')
                mocked.post(pattern, status=200, timeout=True)
                resp = await pub.send_to_jeedom({})
                assert resp is False

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

    @pytest.mark.asyncio
    async def test_add_change_deduplicates_keys(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('a::b', 1)
            await pub.add_change('c', 2)
            await pub.add_change('a::b', 3)

            # an updated key keeps its original position in the queue
            assert pub._build_batch() == {'a::b': 3, 'c': 2}

    @pytest.mark.asyncio
    async def test_nested_rebuild_mixed_keys(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('simple', 1)
            await pub.add_change('a::b::c', 2)
            await pub.add_change('a::b::d', 3)
            await pub.add_change('a::e', 4)

            assert pub.changes == {'simple': 1, 'a': {'b': {'c': 2, 'd': 3}, 'e': 4}}

    @pytest.mark.asyncio
    async def test_build_batch_limited_by_count(self):
        async with Publisher('http://local/', 'cnysltyql', max_changes_per_cycle=2) as pub:
            for i in range(5):
                await pub.add_change(f'root::key_{i}', i)

            assert pub._build_batch() == {'root::key_0': 0, 'root::key_1': 1}
            assert pub.changes == {'root': {'key_2': 2, 'key_3': 3, 'key_4': 4}}

    @pytest.mark.asyncio
    async def test_build_batch_limited_by_size(self):
        async with Publisher('http://local/', 'cnysltyql', max_payload_size=120) as pub:
            for i in range(5):
                await pub.add_change(f'key_{i}', 'x' * 40)

            first = pub._build_batch()
            assert 0 < len(first) < 5
            while pub._build_batch():
                pass
            assert pub.changes == {}

    @pytest.mark.asyncio
    async def test_build_batch_single_value_bigger_than_limit(self):
        async with Publisher('http://local/', 'cnysltyql', max_payload_size=50) as pub:
            await pub.add_change('huge', 'x' * 500)
            await pub.add_change('small', 1)

            assert pub._build_batch() == {'huge': 'x' * 500}
            assert pub._build_batch() == {'small': 1}

    @pytest.mark.asyncio
    async def test_requeue_keeps_newest_value(self):
        async with Publisher('http://local/', 'cnysltyql') as pub:
            await pub.add_change('a', 1)
            await pub.add_change('b', 2)

            batch = pub._build_batch()
            await pub.add_change('a', 99)  # change occurring while the batch was being sent

            pub._requeue(batch)
            assert pub.changes == {'a': 99, 'b': 2}

    @pytest.mark.asyncio
    async def test_queue_fully_drained_over_several_cycles(self):
        async with Publisher('http://local/', 'cnysltyql', max_changes_per_cycle=3) as pub:
            for i in range(7):
                await pub.add_change(f'key_{i}', i)

            sent = {}
            batches = 0
            while True:
                batch = pub._build_batch()
                if not batch:
                    break
                batches += 1
                sent.update(batch)

            assert batches == 3
            assert sent == {f'key_{i}': i for i in range(7)}
            assert pub.changes == {}
