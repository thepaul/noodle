# printing

(= print-here (.(import cStringIO).StringIO))
(= .(import sys).stdout print-here)

(= foo "testing")
(assert (== (print foo "printing") "testing"))

# printing with no endline
(printnonl "everything is")

(print "ok.")

(assert (== (.print-here.getvalue) 'testing printing\neverything is ok.\n'))
