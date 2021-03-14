#!/usr/bin/env python
from rmtest import ModuleTestCase
from redis import ResponseError
import sys
import random
import math

if sys.version >= '3':
    xrange = range


def parse_tdigest_info(array_reply):
    reply_dict = {}
    for pos in range(0, len(array_reply), 2):
        property_name = array_reply[pos]
        property_value = array_reply[pos + 1]
        reply_dict[property_name] = property_value
    return reply_dict


class CMSTest(ModuleTestCase('../redisbloom.so')):
    # ensure all our random inputs are always the same
    random.seed(123)

    def test_tdigest_create(self):
        for compression in range(100, 1000, 100):
            self.assertOk(self.cmd('tdigest.create', 'tdigest', compression))
            self.assertEqual(compression,
                             parse_tdigest_info(self.cmd('tdigest.info', 'tdigest'))['Compression'])

    def test_negative_tdigest_create(self):
        self.cmd('SET', 'tdigest', 'B')
        # WRONGTYPE
        self.assertRaises(ResponseError, self.cmd, 'tdigest.create', 'tdigest', 100)
        self.cmd('DEL', 'tdigest')
        # arity lower
        self.assertRaises(ResponseError, self.cmd, 'tdigest.create', 'tdigest')
        # arity upper
        self.assertRaises(ResponseError, self.cmd, 'tdigest.create', 'tdigest', 100, 5)
        # parsing
        self.assertRaises(ResponseError, self.cmd, 'tdigest.create', 'tdigest', 'a')
        # compression negative/zero value
        self.assertRaises(ResponseError, self.cmd, 'tdigest.create', 'tdigest', 0)
        # compression negative/zero value
        self.assertRaises(ResponseError, self.cmd, 'tdigest.create', 'tdigest', -1)

    def test_tdigest_reset(self):
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 100))
        # reset on empty histogram
        self.assertOk(self.cmd('tdigest.reset', 'tdigest'))
        # insert datapoints into sketch
        for x in range(100):
            self.assertOk(self.cmd('tdigest.add', 'tdigest', random.random(), 1.0))

        # assert we have 100 unmerged nodes
        self.assertEqual(100,
                         parse_tdigest_info(self.cmd('tdigest.info', 'tdigest'))['Unmerged nodes'])

        self.assertOk(self.cmd('tdigest.reset', 'tdigest'))

        # assert we have 100 unmerged nodes
        self.assertEqual(0,
                         parse_tdigest_info(self.cmd('tdigest.info', 'tdigest'))['Unmerged nodes'])

    def test_negative_tdigest_reset(self):
        self.cmd('SET', 'tdigest', 'B')
        # WRONGTYPE
        self.assertRaises(ResponseError, self.cmd, 'tdigest.reset', 'tdigest')
        self.cmd('DEL', 'tdigest')
        # empty key
        self.assertRaises(ResponseError, self.cmd, 'tdigest.reset', 'tdigest')

        self.assertOk(self.cmd('tdigest.create', 'tdigest', 100))
        # arity lower
        self.assertRaises(ResponseError, self.cmd, 'tdigest.reset')
        # arity upper
        self.assertRaises(ResponseError, self.cmd, 'tdigest.reset', 'tdigest', 100)

    def test_tdigest_add(self):
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 100))
        # reset on empty histogram
        self.assertOk(self.cmd('tdigest.reset', 'tdigest'))
        # insert datapoints into sketch
        for x in range(10000):
            self.assertOk(self.cmd('tdigest.add', 'tdigest', random.random() * 10000, random.random() * 500 + 1.0))

    def test_negative_tdigest_add(self):
        self.cmd('SET', 'tdigest', 'B')
        # WRONGTYPE
        self.assertRaises(ResponseError, self.cmd, 'tdigest.add', 'tdigest', 100, 100)
        self.cmd('DEL', 'tdigest')
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 100))
        # arity lower
        self.assertRaises(ResponseError, self.cmd, 'tdigest.add', 'tdigest')
        # arity upper
        self.assertRaises(ResponseError, self.cmd, 'tdigest.add', 'tdigest', 100, 5, 100.0)
        # key does not exist
        self.assertRaises(ResponseError, self.cmd, 'tdigest.add', 'dont-exist', 100, 100)
        # parsing
        self.assertRaises(ResponseError, self.cmd, 'tdigest.add', 'tdigest', 'a', 5)
        self.assertRaises(ResponseError, self.cmd, 'tdigest.add', 'tdigest', 5.0, 'a')

    def test_tdigest_merge(self):
        self.assertOk(self.cmd('tdigest.create', 'to-tdigest', 100))
        self.assertOk(self.cmd('tdigest.create', 'from-tdigest', 100))
        # insert datapoints into sketch
        for x in range(100):
            self.assertOk(self.cmd('tdigest.add', 'from-tdigest', 1.0, 1.0))
        for x in range(100):
            self.assertOk(self.cmd('tdigest.add', 'to-tdigest', 1.0, 10.0))
        # merge from-tdigest into to-tdigest
        self.assertOk(self.cmd('tdigest.merge', 'to-tdigest', 'from-tdigest'))
        # we should now have 1100 weight on to-histogram
        to_info = parse_tdigest_info(self.cmd('tdigest.info', 'to-tdigest'))
        total_weight_to = float(to_info['Merged weight']) + float(to_info['Unmerged weight'])
        self.assertEqual(1100, total_weight_to)

    def test_tdigest_merge_to_empty(self):
        self.assertOk(self.cmd('tdigest.create', 'to-tdigest', 100))
        self.assertOk(self.cmd('tdigest.create', 'from-tdigest', 100))
        # insert datapoints into sketch
        for x in range(100):
            self.assertOk(self.cmd('tdigest.add', 'from-tdigest', 1.0, 1.0))
        # merge from-tdigest into to-tdigest
        self.assertOk(self.cmd('tdigest.merge', 'to-tdigest', 'from-tdigest'))
        # assert we have same merged weight on both histograms ( given the to-histogram was empty )
        from_info = parse_tdigest_info(self.cmd('tdigest.info', 'from-tdigest'))
        total_weight_from = float(from_info['Merged weight']) + float(from_info['Unmerged weight'])
        to_info = parse_tdigest_info(self.cmd('tdigest.info', 'to-tdigest'))
        total_weight_to = float(to_info['Merged weight']) + float(to_info['Unmerged weight'])
        self.assertEqual(total_weight_from, total_weight_to)

    def test_negative_tdigest_merge(self):
        self.cmd('SET', 'to-tdigest', 'B')
        self.cmd('SET', 'from-tdigest', 'B')

        # WRONGTYPE
        self.assertRaises(ResponseError, self.cmd, 'tdigest.merge', 'to-tdigest', 'from-tdigest')
        self.cmd('DEL', 'to-tdigest')
        self.assertOk(self.cmd('tdigest.create', 'to-tdigest', 100))
        self.assertRaises(ResponseError, self.cmd, 'tdigest.merge', 'to-tdigest', 'from-tdigest')
        self.cmd('DEL', 'from-tdigest')
        self.assertOk(self.cmd('tdigest.create', 'from-tdigest', 100))
        # arity lower
        self.assertRaises(ResponseError, self.cmd, 'tdigest.merge', 'to-tdigest')
        # arity upper
        self.assertRaises(ResponseError, self.cmd, 'tdigest.merge', 'to-tdigest', 'from-tdigest', 'from-tdigest')
        # key does not exist
        self.assertRaises(ResponseError, self.cmd, 'tdigest.merge', 'dont-exist', 'to-tdigest')
        self.assertRaises(ResponseError, self.cmd, 'tdigest.merge', 'to-tdigest', 'dont-exist')

    def test_tdigest_min_max(self):
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 100))
        # test for no datapoints first
        self.assertEqual(sys.float_info.max, float(self.cmd('tdigest.min', 'tdigest')))
        self.assertEqual(sys.float_info.min, float(self.cmd('tdigest.max', 'tdigest')))
        # insert datapoints into sketch
        for x in range(1, 101):
            self.assertOk(self.cmd('tdigest.add', 'tdigest', x, 1.0))
        # min/max
        self.assertEqual(100, float(self.cmd('tdigest.max', 'tdigest')))
        self.assertEqual(1, float(self.cmd('tdigest.min', 'tdigest')))

    def test_negative_tdigest_min_max(self):
        self.cmd('SET', 'tdigest', 'B')
        # WRONGTYPE
        self.assertRaises(ResponseError, self.cmd, 'tdigest.min', 'tdigest')
        self.assertRaises(ResponseError, self.cmd, 'tdigest.max', 'tdigest')
        # key does not exist
        self.assertRaises(ResponseError, self.cmd, 'tdigest.min', 'dont-exist')
        self.assertRaises(ResponseError, self.cmd, 'tdigest.max', 'dont-exist')

        self.cmd('DEL', 'tdigest', 'B')
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 100))
        # arity lower
        self.assertRaises(ResponseError, self.cmd, 'tdigest.min')
        self.assertRaises(ResponseError, self.cmd, 'tdigest.max')
        # arity upper
        self.assertRaises(ResponseError, self.cmd, 'tdigest.min', 'tdigest', 1)
        self.assertRaises(ResponseError, self.cmd, 'tdigest.max', 'tdigest', 1)

    def test_tdigest_quantile(self):
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 500))
        # insert datapoints into sketch
        for x in range(1, 10000):
            self.assertOk(self.cmd('tdigest.add', 'tdigest', x * 0.01, 1.0))
        # assert min min/max have same result as quantile 0 and 1
        self.assertEqual(float(self.cmd('tdigest.max', 'tdigest')), float(self.cmd('tdigest.quantile', 'tdigest', 1.0)))
        self.assertEqual(float(self.cmd('tdigest.min', 'tdigest')), float(self.cmd('tdigest.quantile', 'tdigest', 0.0)))
        self.assertAlmostEqual(1.0, float(self.cmd('tdigest.quantile', 'tdigest', 0.01)), places=2, msg=None,
                               delta=None)
        self.assertAlmostEqual(99.0, float(self.cmd('tdigest.quantile', 'tdigest', 0.99)), places=2, msg=None,
                               delta=None)

    def test_negative_tdigest_quantile(self):
        self.cmd('SET', 'tdigest', 'B')
        # WRONGTYPE
        self.assertRaises(ResponseError, self.cmd, 'tdigest.quantile', 'tdigest', 0.9)
        # key does not exist
        self.assertRaises(ResponseError, self.cmd, 'tdigest.quantile', 'dont-exist', 0.9)
        self.cmd('DEL', 'tdigest', 'B')
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 100))
        # arity lower
        self.assertRaises(ResponseError, self.cmd, 'tdigest.quantile')
        # arity upper
        self.assertRaises(ResponseError, self.cmd, 'tdigest.quantile', 'tdigest', 1, 1)
        # parsing
        self.assertRaises(ResponseError, self.cmd, 'tdigest.quantile', 'tdigest', 'a')

    def test_tdigest_cdf(self):
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 500))
        # insert datapoints into sketch
        for x in range(1, 100):
            self.assertOk(self.cmd('tdigest.add', 'tdigest', x, 1.0))

        self.assertAlmostEqual(0.01, float(self.cmd('tdigest.cdf', 'tdigest', 1.0)), places=2, msg=None, delta=None)
        self.assertAlmostEqual(0.99, float(self.cmd('tdigest.cdf', 'tdigest', 99.0)), places=2, msg=None, delta=None)

    def test_negative_tdigest_cdf(self):
        self.cmd('SET', 'tdigest', 'B')
        # WRONGTYPE
        self.assertRaises(ResponseError, self.cmd, 'tdigest.cdf', 'tdigest', 0.9)
        # key does not exist
        self.assertRaises(ResponseError, self.cmd, 'tdigest.cdf', 'dont-exist', 0.9)
        self.cmd('DEL', 'tdigest', 'B')
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 100))
        # arity lower
        self.assertRaises(ResponseError, self.cmd, 'tdigest.cdf')
        # arity upper
        self.assertRaises(ResponseError, self.cmd, 'tdigest.cdf', 'tdigest', 1, 1)
        # parsing
        self.assertRaises(ResponseError, self.cmd, 'tdigest.cdf', 'tdigest', 'a')

    def test_negative_tdigest_info(self):
        self.cmd('SET', 'tdigest', 'B')
        # WRONGTYPE
        self.assertRaises(ResponseError, self.cmd, 'tdigest.info', 'tdigest')
        # dont exist
        self.assertRaises(ResponseError, self.cmd, 'tdigest.info', 'dont-exist')
        self.cmd('DEL', 'tdigest', 'B')
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 100))
        # arity lower
        self.assertRaises(ResponseError, self.cmd, 'tdigest.info')
        # arity upper
        self.assertRaises(ResponseError, self.cmd, 'tdigest.info', 'tdigest', 1)

    def test_save_load(self):
        self.assertOk(self.cmd('tdigest.create', 'tdigest', 500))
        # insert datapoints into sketch
        for x in range(1, 101):
            self.assertOk(self.cmd('tdigest.add', 'tdigest', 1.0, 1.0))
        self.assertEqual(True, self.cmd('SAVE'))
        mem_usage_prior_restart = self.cmd('MEMORY', 'USAGE', 'tdigest')
        self.restart_and_reload()
        # assert we have 100 unmerged nodes
        self.assertEqual(1, self.cmd('EXISTS', 'tdigest'))
        self.assertEqual(100,
                         float(parse_tdigest_info(self.cmd('tdigest.info', 'tdigest'))['Merged weight']))
        mem_usage_after_restart = self.cmd('MEMORY', 'USAGE', 'tdigest')
        self.assertEqual(mem_usage_prior_restart, mem_usage_after_restart)


if __name__ == "__main__":
    import unittest

    unittest.main()
