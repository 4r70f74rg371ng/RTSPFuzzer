from time import gmtime, strftime
import socket
import sys
import traceback
import random
import threading

def connect_server(host, port, packet):
   data = ""
   try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.settimeout(0.2)
      s.connect((host, port))
      s.send(packet)
      data = s.recv(10240)
      s.close()
      #print "====> "+ repr(data)
   except Exception, e:
      """
      exc_type, exc_value, exc_traceback = sys.exc_info()
      explines_raw = traceback.format_exception(exc_type, exc_value,exc_traceback)
      explines = []
      for lines_raw in explines_raw:
         for line in lines_raw.strip().split("\n"):
            explines.append(line)
      for line in explines:
         print line
      """
      pass
   return data

def test_server_up(host, port):
   packet = "OPTIONS rtsp://192.168.43.161:8554/test.mpg RTSP/1.0\r\nCSeq: 1\r\nUser-Agent: LibVLC/3.0.0-git (LIVE555 Streaming Media v2016.02.22)\r\n\r\n"
   data = connect_server(host, port, packet)
   if data != '':
      return True
   return False

def test_send_packet(host, port, packet):
   while test_server_up(host, port) == False:
      pass
   data = connect_server(host, port, packet)
   if data != '':
      return True
   return False
   
patterns = [" ","}","]",")","'","\"",";",":",">","\\","--","#","`","&","?",",","a"*1024,"1"*1024,"../"*1024]
patterns_flag = ["\" \"","\"}\"","\"]\"","\")\"","\"'\"","\"\\\"\"","\";\"","\":\"","\">\"","\"\\\\\"","\"--\"","\"#\"","\"`\"","\"&\"","\"?\"","\",\"","\"a\"*1024","\"1\"*1024","\"../\"*1024"]
assert len(patterns) == len(patterns_flag)
for i in range(0, len(patterns)-1):
   assert(patterns[i] == eval(patterns_flag[i]))

def fuzz_string(packet):
   global patterns, patterns_flag
   new_packet = ""
   mode = random.randint(1, 4)
   ret_datas = None
   if mode == 1:
      # injection based
      index_injection = random.randint(0, len(packet)-1)
      pattern_index_injection = random.randint(0, len(patterns)-1)
      pattern_injection = patterns[pattern_index_injection]
      new_packet = packet[:index_injection] + pattern_injection + packet[index_injection:]
      ret_datas = [ "[%s]" % strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    "injection based           ",
                    "(" + ("%4d" % index_injection) + "," + ("%15s" % patterns_flag[pattern_index_injection]) + ")",
                    repr(new_packet),
                    new_packet]
   elif mode == 2:
      # mutation based
      index_injection = random.randint(0, len(packet)-1)
      char_injection = chr(random.randint(0, 255))
      new_packet = packet[:index_injection] + char_injection + packet[index_injection+1:]
      ret_datas = [ "[%s]" % strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    "mutation based            ",
                    "(" + ("%4d" % index_injection) + "," + ("%15s" % repr(char_injection)) + ")",
                    repr(new_packet),
                    new_packet]
   elif mode == 3:
      # injection + mutation based
      index_injection = random.randint(0, len(packet)-1)
      pattern_index_injection = random.randint(0, len(patterns)-1)
      pattern_injection = patterns[pattern_index_injection]
      new_packet = packet[:index_injection] + pattern_injection + packet[index_injection+1:]
      ret_datas = [ "[%s]" % strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    "injection + mutation based",
                    "(" + ("%4d" % index_injection) + "," + ("%15s" % patterns_flag[pattern_index_injection]) + ")",
                    repr(new_packet),
                    new_packet]
   else: # 4
      # generation based
      index_injection = random.randint(0, len(packet)-1)
      pattern_index_injection = random.randint(0, len(patterns)-1)
      pattern_injection = patterns[pattern_index_injection]
      new_packet = packet[:index_injection] + pattern_injection
      ret_datas = [ "[%s]" % strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                    "generation based          ",
                    "(" + ("%4d" % index_injection) + "," + ("%15s" % patterns_flag[pattern_index_injection]) + ")",
                    repr(new_packet),
                    new_packet]
   return ret_datas
   


"""
test_packet="abcd"
for i in range(0,100):
   fuzzer = fuzz_string(test_packet)
   if fuzzer != None:
      print " ".join(fuzzer[0:4])
      print "fuzzing: " + repr(fuzzer[4])
"""

class MyFuzzer(threading.Thread):
   def __init__(self, host, port, packet):
      threading.Thread.__init__(self)
      self.host = host
      self.port = port
      self.packet = packet
   
   def run(self): 
      while True:
         fuzzer = fuzz_string(self.packet)
         ret = test_send_packet(self.host, self.port, fuzzer[4])
         if ret == False:
            if test_server_up(self.host, self.port) == False:
               print "[+]"+" ".join(fuzzer[0:4])
            else:
               #print "[o]"+" ".join(fuzzer[0:4])
               pass

HOST = '169.254.252.116'
PORT =  8554
PACKET = "GET_PARAMETER rtsp://192.168.43.161:8554/test.mpg/ RTSP/1.0\r\nCSeq: 1\r\nUser-Agent: LibVLC/3.0.0-git (LIVE555 Streaming Media v2016.02.22)\r\nSession: 176B5092\r\n\r\n"
threads = []
for i in range(0,100):
   thread = MyFuzzer(HOST, PORT, PACKET)
   threads.append(thread)
   thread.start()

for thread in threads:
   thread.join()

   

