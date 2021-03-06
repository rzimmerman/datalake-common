# Copyright 2015 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import pytest

from datalake_common import has_s3, DatalakeRecord
from datalake_common.errors import InsufficientConfiguration, \
    UnsupportedTimeRange, NoSuchDatalakeFile


@pytest.mark.skipif(not has_s3, reason='requires s3 features')
def test_list_from_s3_url(s3_file_from_metadata, random_metadata):
    url = 's3://foo/bar'
    s3_file_from_metadata(url, random_metadata)
    records = DatalakeRecord.list_from_url(url)
    assert len(records) >= 1
    for r in records:
        assert r['metadata'] == random_metadata


@pytest.mark.skipif(has_s3, reason='')
def test_from_url_fails_without_boto():
    with pytest.raises(InsufficientConfiguration):
        DatalakeRecord.list_from_url('s3://foo/bar')


def test_list_from_metadata(random_metadata):
    url = 's3://foo/baz'
    records = DatalakeRecord.list_from_metadata(url, random_metadata)
    assert len(records) >= 1
    for r in records:
        assert r['metadata'] == random_metadata


def test_timespan_too_big(random_metadata):
    url = 's3://foo/blapp'
    random_metadata['start'] = 0
    random_metadata['end'] = (DatalakeRecord.MAXIMUM_BUCKET_SPAN + 1) * \
        DatalakeRecord.TIME_BUCKET_SIZE_IN_MS
    with pytest.raises(UnsupportedTimeRange):
        DatalakeRecord.list_from_metadata(url, random_metadata)


@pytest.mark.skipif(not has_s3, reason='requires s3 features')
def test_no_such_datalake_file_in_bucket(s3_bucket_maker):
    s3_bucket_maker('test-bucket')
    url = 's3://test-bucket/such/file'
    with pytest.raises(NoSuchDatalakeFile):
        DatalakeRecord.list_from_url(url)


@pytest.mark.skipif(not has_s3, reason='requires s3 features')
def test_no_such_bucket(s3_connection):
    url = 's3://no/such/file'
    with pytest.raises(NoSuchDatalakeFile):
        DatalakeRecord.list_from_url(url)


def test_no_end(random_metadata):
    url = 's3://foo/baz'
    del(random_metadata['end'])
    records = DatalakeRecord.list_from_metadata(url, random_metadata)
    assert len(records) >= 1
    for r in records:
        assert r['metadata'] == random_metadata


def test_get_time_buckets_misaligned():
    # Test for regression on bug when querying over x buckets for a timeframe
    # (end - start) of < x buckets (i.e. end of B0 to start of B2)
    start = DatalakeRecord.TIME_BUCKET_SIZE_IN_MS * 4 / 5
    end = DatalakeRecord.TIME_BUCKET_SIZE_IN_MS * 11 / 5
    buckets = DatalakeRecord.get_time_buckets(start, end)
    assert buckets == [0, 1, 2]
