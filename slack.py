#!/usr/bin/python
from slacker import Slacker

import argparse
import datetime
import json
import os
import tempfile
import shutil
import sys
import zipfile


class SlackHistoryExporter:

    TEAM_NAME = None
    CURRENT_USER = None
    USER_ID = None

    def __init__(self, auth_token):
        self.slack = Slacker(auth_token)

        self._test_auth()

    def _test_auth(self):
        test_auth_body = self.slack.auth.test().body

        self.TEAM_NAME = test_auth_body['team']
        self.CURRENT_USER = test_auth_body['user']
        self.USER_ID = test_auth_body['user_id']

        print "Successfully authenticated for team {0} and user {1} ".format(self.TEAM_NAME, self.CURRENT_USER)

    def _get_channel_history(self, channel, page_size=100):
        _messages = []
        _last_timestamp = None

        while True:
            _response = self.slack.groups.history(
                channel, latest=_last_timestamp, oldest=0, count=page_size
            ).body

            _messages.extend(_response['messages'])

            if _response['has_more']:
                _last_timestamp = _messages[-1]['ts']
            else:
                break

        return _messages

    def _dump_channel_messages(self, target_dir, messages):
        _current_date = None
        _messages = []

        for _message in messages:
            _ts = self._parse_timestamp(_message['ts'])
            _date = '{:%Y-%m-%d}'.format(_ts)

            if not _current_date:
                _current_date = _date

            if _current_date != _date:
                with open(os.path.join(target_dir, '%s.json' % _current_date), 'w') as _file:
                    json.dump(_messages, _file, indent=4)

                _current_date = _date
                _messages = []

            _messages.append(_message)

        with open(os.path.join(target_dir, '%s.json' % _current_date), 'w') as _file:
            json.dump(_messages, _file, indent=4)

    def _dump_private_channels(self, target_dir, channels):
        _members = []
        _channels = []

        for _channel in self.slack.groups.list().body['groups']:
            if _channel['name'] in channels:
                _members += [x for x in _channel['members'] if x not in _members]
                _channels += [_channel['id']]

                _channel_dump_dir = os.path.join(target_dir, _channel['name'])
                if not os.path.exists(_channel_dump_dir):
                    os.mkdir(_channel_dump_dir)

                _messages = self._get_channel_history(_channel['id'])
                self._dump_channel_messages(_channel_dump_dir, _messages)

        return _channels, _members

    def _dump_channels_info(self, target_dir, channels):
        _channels = []

        for channel in self.slack.groups.list().body['groups']:
            if channel['id'] in channels:
                _channels.append({
                    'id': channel['id'],
                    'name': channel['name'],
                    'created': channel['created'],
                    'creator': channel['creator'],
                    'is_archived': channel['is_archived'],
                    'is_channel': True,
                    'is_general': False,
                    'is_member': True,
                    'members': channel['members'],
                    'num_members': len(channel['members']),
                    'purpose': channel['purpose'],
                    'topic': channel['topic']
                })

        with open(os.path.join(target_dir, 'channels.json'), 'w') as outFile:
            json.dump(_channels, outFile, indent=4)

    def _dump_members_info(self, target_dir, members):
        _members = []

        for member in self.slack.users.list().body['members']:
            if member['id'] in members:
                _members.append(member)

        with open(os.path.join(target_dir, 'users.json'), 'w') as _file:
            json.dump(_members, _file, indent=4)

    def _parse_timestamp(self, timestamp):
        if '.' in timestamp:
            t_parts = timestamp.split('.')
            if len(t_parts) != 2:
                raise ValueError('Invalid time stamp')
            else:
                return datetime.datetime.utcfromtimestamp(float(t_parts[0]))

    def _archive_directory(self, target_file, directory):
        _zip_file = zipfile.ZipFile(target_file, 'w', zipfile.ZIP_DEFLATED)
        _directory = directory if directory.endswith('/') else directory + '/'

        for _root, _, _files in os.walk(_directory):
            for _file in _files:
                _file_path = os.path.join(_root, _file)
                _zip_file.write(_file_path, _file_path.replace(_directory, ''))

        _zip_file.close()

    def export(self, target_file, channels):
        _tmp_dir = tempfile.mkdtemp()

        _channels, _members = self._dump_private_channels(_tmp_dir, channels)

        self._dump_channels_info(_tmp_dir, _channels)
        self._dump_members_info(_tmp_dir, _members)

        self._archive_directory(target_file, _tmp_dir)
        shutil.rmtree(_tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Slack history exporter')

    parser.add_argument('--token', '-t', type=str, required=True, help='Slack API access token')
    parser.add_argument('--output', '-o', type=str, help='export file path', default='export.zip')
    parser.add_argument('channels', metavar='channel', nargs='+', help='Slack private channels to export')

    args = parser.parse_args(sys.argv[1:])
    exporter = SlackHistoryExporter(args.token)

    exporter.export(args.output, args.channels)
