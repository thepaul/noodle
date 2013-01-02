# for

(= zeros-and-ones [])
(for number in (xrange 10)
  (.zeros-and-ones.append (% number 2)))
(assert (== zeros-and-ones (* \[0 1] 5)))

(for (a b c) in (zip \[0 1 2] \[3 4 5] \[6 7 8])
  (assert (< a b c)))
