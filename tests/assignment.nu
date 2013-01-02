# variable assignment/definition
(assert (== (= foo 'testing') foo))
(assert (== (= foo2 'testing2') foo2))
(assert (== (define foo3 'testing3') foo3))

# assignment with unpacking
# (= can take either an escaped tuple or a normal tuple as a list
#       of variable names to which to unpack the second argument.)
(assert (== (= (m1 m2 m3) \(9 99 999)) \(9 99 999)))
(assert (== \(m1 m2 m3) \(9 99 999)))
(assert (== (= \(m4 m5 m6) \(9 99 999)) \(9 99 999)))
(assert (== \(m4 m5 m6) \(9 99 999)))
(= somestuff \[19 20 21])
(assert (== (= (nineteen twenty twenty-one) somestuff) \[19 20 21]))
(assert (and (== nineteen 19)
             (== twenty 20)
             (== twenty-one 21)))
