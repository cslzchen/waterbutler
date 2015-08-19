import json

from tornado import testing

from waterbutler.core.path import WaterButlerPath

from tests import utils


class TestMoveHandler(utils.MultiProviderHandlerTestCase):
    HOOK_PATH = 'waterbutler.server.handlers.move.MoveHandler._send_hook'

    @testing.gen_test
    def test_calls_move(self):
        self.source_provider.move = utils.MockCoroutine(
            return_value=(utils.MockFileMetadata(), False)
        )

        yield self.http_client.fetch(
            self.get_url('/ops/move'),
            method='POST',
            body=json.dumps(self.payload())
        )

        assert self.source_provider.move.called
        self.source_provider.move.assert_called_once_with(
            self.destination_provider,
            WaterButlerPath(self.payload()['source']['path']),
            WaterButlerPath(self.payload()['destination']['path']),
            rename=None,
            conflict='replace'
        )

    @testing.gen_test
    def test_conflict(self):
        self.source_provider.move = utils.MockCoroutine(
            return_value=(utils.MockFileMetadata(), True)
        )

        payload = self.payload()
        payload['conflict'] = 'keep'

        resp = yield self.http_client.fetch(
            self.get_url('/ops/move'),
            method='POST',
            body=json.dumps(payload)
        )

        assert resp.code == 201
        assert self.source_provider.move.called
        self.source_provider.move.assert_called_once_with(
            self.destination_provider,
            WaterButlerPath(payload['source']['path']),
            WaterButlerPath(payload['destination']['path']),
            rename=None,
            conflict='keep'
        )

    @testing.gen_test
    def test_rename(self):
        metadata = utils.MockFileMetadata()
        self.source_provider.move = utils.MockCoroutine(
            return_value=(metadata, False)
        )

        payload = self.payload()
        payload['rename'] = 'MyCoolFileGuys'

        resp = yield self.http_client.fetch(
            self.get_url('/ops/move'),
            method='POST',
            body=json.dumps(payload)
        )

        assert resp.code == 200
        assert json.loads(resp.body.decode()) == metadata.serialized()
        assert self.source_provider.move.called
        self.source_provider.move.assert_called_once_with(
            self.destination_provider,
            WaterButlerPath(payload['source']['path']),
            WaterButlerPath(payload['destination']['path']),
            rename='MyCoolFileGuys',
            conflict='replace'
        )

    @testing.gen_test
    def test_intra_makes_callback(self):
        self.source_provider.move = utils.MockCoroutine(
            return_value=(utils.MockFileMetadata(), False)
        )

        yield self.http_client.fetch(
            self.get_url('/ops/move'),
            method='POST',
            body=json.dumps(self.payload())
        )

        self.mock_send_hook.assert_called_once_with(
            'move',
            utils.MockFileMetadata().serialized()
        )