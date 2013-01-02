# global

(= bonk 554)
((lambda ()
  (= bonk 8)))  # (local, not global)
(assert (== bonk 554))

(= bonk 555)
((lambda ()
  (global bonk)
  (= bonk 8)))  # (this time, made global)
(assert (== bonk 8))
