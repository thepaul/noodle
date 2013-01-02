# while

(= forwards [])
(= backwards (range 10 0 -1))
(while backwards
  (.forwards.append (.backwards.pop)))
(assert (== forwards (range 1 11)))
