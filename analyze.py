import sys
import math

import ijson.backends.python as ijson
#import ijson.backends.yajl2 as ijson
#import ijson.backends.yajl as ijson


class Result:

   def __init__(self):
      self.success = 0
      self.fail = 0
      self.total = 0
      self.duration = 0

      ## Wallclock in us since epoch
      self.started = 0
      self.ended = 0

      ## Wallclock duration in us
      self.durationWallclock = 0

      self.openTimestamps = []
      self.closeTimestamps = []
      self.preInitMin = None
      self.preInitMax = None


def joinResults(results):
   res = Result()
   for r in results:
      res.success += r.success
      res.fail += r.fail
      res.total += r.total
      res.duration += r.duration
      res.openTimestamps.extend(r.openTimestamps)
      res.closeTimestamps.extend(r.closeTimestamps)

      if res.started == 0 or r.started < res.started:
         res.started = r.started
         
      if res.ended == 0 or r.ended > res.ended:
         res.ended = r.ended
   
   res.durationWallclock = res.ended - res.started

   return res


def printStats(timestamps):
   r = sorted(timestamps)
   r_cnt = len(timestamps)
   r_min = float(r[0])
   r_median = float(r[len(r)/2])
   r_avg = float(sum(timestamps)) / float(r_cnt)
   r_sd = math.sqrt(sum([((float(x) - r_avg)**2.) for x in timestamps]) / (float(r_cnt) - 1.))
   r_q90 = float(r[-len(r)/10])
   r_q95 = float(r[-len(r)/20])
   r_q99 = float(r[-len(r)/100])
   r_q999 = float(r[-len(r)/1000])
   r_q9999 = float(r[-len(r)/10000])
   r_max = float(r[-1])

   print ("     Min: %9.1f ms\n" + \
          "      SD: %9.1f ms\n" + \
          "     Avg: %9.1f ms\n" + \
          "  Median: %9.1f ms\n" + \
          "  q90   : %9.1f ms\n" + \
          "  q95   : %9.1f ms\n" + \
          "  q99   : %9.1f ms\n" + \
          "  q99.9 : %9.1f ms\n" + \
          "  q99.99: %9.1f ms\n" + \
          "     Max: %9.1f ms\n") % (r_min / 1000.,
                                     r_sd / 1000.,
                                     r_avg / 1000.,
                                     r_median / 1000.,
                                     r_q90 / 1000.,
                                     r_q95 / 1000.,
                                     r_q99 / 1000.,
                                     r_q999 / 1000.,
                                     r_q9999 / 1000.,
                                     r_max / 1000.)


def load(filename):

   res = Result()
   parser = ijson.parse(open(filename))

   for prefix, event, value in parser:

      if prefix == 'total_duration':
         res.duration = value

      if prefix == 'started':
         res.started = value

      if prefix == 'ended':
         res.ended = value

      if (prefix, event) == ('connection_stats.item', 'start_map'):
         # Start of a new connection.
         conn_failed = False
         conn_pre_init = None
         conn_open = None
         conn_close = None

      if prefix == 'connection_stats.item.tcp_pre_init':
         conn_pre_init = value

      if prefix == 'connection_stats.item.failed':
         if value:
            conn_failed = True
            res.fail += 1
         else:
            res.success += 1

      if prefix == 'connection_stats.item.open':
         conn_open = value

      if prefix == 'connection_stats.item.close':
         conn_close = value

      if (prefix, event) == ('connection_stats.item', 'end_map'):
         # End of a connection. Only save its statistics if it succeeded.
         # XXX This assumes that the open/close/tcp_pre_init values are always
         # defined by each connection object.
         if not conn_failed:
            if res.preInitMin is None or conn_pre_init < res.preInitMin:
               res.preInitMin = conn_pre_init
            if res.preInitMax is None or conn_pre_init > res.preInitMax:
               res.preInitMax = conn_pre_init

            res.openTimestamps.append(conn_open)
            res.closeTimestamps.append(conn_close)

   res.total = res.success + res.fail
   res.durationWallclock = res.ended - res.started
   return res


def analyze(res):
   duration_ms = float(res.durationWallclock) / 1000000.

   print
   print "Aggregate results (WebSocket Opening+Closing Handshake)"
   print
   #print "          Duration: %9d ms" % (float(res.duration) / 1000.)
   print "          Duration: %9.1f ms" % round(duration_ms, 1)
   print "             Total: %9d" % res.total
   print "           Success: %9d" % res.success
   print "              Fail: %9d" % res.fail
   print "            Fail %%: %9.2f" % (100. * float(res.fail) / float(res.total))
   print "    Handshakes/sec: %9d" % int(round((float(res.success) / (duration_ms / 1000.))))
   print
   printStats(res.openTimestamps)
   print


def printResults(files):
   results = []
   for fn in files:
      print "Loading wsperf result file %s .." % fn
      res = load(fn)
      results.append(res)

   res = joinResults(results)
   analyze(res)
   print "Analyze done."


if __name__ == '__main__':
   printResults(sys.argv[1:])


#pstat(res_close_timestamps)


#  start_array None
# item start_map None
# item map_key tcp_pre_init
# item.tcp_pre_init number 20594
# item map_key tcp_post_init
# item.tcp_post_init number 2
# item map_key open
# item.open number 15831
# item map_key close
# item.close number 38388
# item map_key failed
# item.failed boolean False
# item end_map None

# prefix, event, value
