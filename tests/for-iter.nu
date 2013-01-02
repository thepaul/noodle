# for-iter (generator expressions)

(= side-effect-list [])
(= the-generator
   (for-iter a in (range 5)
             (.side-effect-list.append a)
             (* a 100)))
(assert (not side-effect-list))
(assert (== (.the-generator.next) 0))
(assert (== side-effect-list \[0]))
(assert (== (.the-generator.next) 100))
(assert (== side-effect-list \[0 1]))

((define (check-for-iter)
   (define side-effect 'x')
   (for val in (for-iter a in 'myword' (= side-effect a) (ord a))
               (assert (== side-effect (chr val))))))

(for-iter (a (b c)) in `((0 (1 2)) (3 (4 5)) (6 (7 8)))
     (assert (== (+ a 1) b))
     (assert (== (+ b 1) c)))
