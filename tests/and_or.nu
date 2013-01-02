# and/or
(assert (not (and \[0 1 2] False \(3 4))))
(assert (== (and 'one' 'two' 'three') 'three'))
(assert (not (or False [] 0 0.0 ())))
(assert (== (or False [] 0 "notfalse" 0) 'notfalse'))
(assert (and))
(assert (not (or)))

# shortcutting
(= blah 'foo')
(assert (== (and 5 1 100 -4 [] (= blah 21)) []))
(assert (== blah 'foo'))
(assert (== (and 5 1 100 -4 15 (= blah 19)) 19))
(assert (== blah 19))
(assert (== (or 0 False 0.0 (= blah "forty-two") 0) "forty-two"))
(assert (== blah "forty-two"))
(assert (== (or 5 False 0.0 (= blah "not done") 0) 5))
(assert (== blah "forty-two"))
