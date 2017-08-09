#!/usr/bin/python

import os
import sys
# traverse root directory, and list directories as dirs and files as files
for root, dirs, files in os.walk(sys.argv[1]):
    path = root.split(os.sep)
#    print((len(path) - 1) * '---', os.path.basename(root))
    for file in files:
        if file == "log.txt":
            #print(file)
            f = open(root +'/' + file,'r')
            #print(root +'/' + file)
            for line in f:
                if "eval" in line:
                    score1 = line.split()[-2][0:-1]
                    score2 = line.split()[-1][0:-1]
                    print "%s %s %s" % (os.path.basename(root), score1, score2)
                    break
            f.close()
      

