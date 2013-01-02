# generators

(define (pairs seq)
  (= i (iter seq))
  (while 1 (yield \((.i.next) (.i.next)))))

(assert (==
          (for-list val in (pairs (range 9)) val)
          \[\(0 1) \(2 3) \(4 5) \(6 7)]))

(define (generate-count)
  (yield 17)
  (yield 18)
  (yield 29))

(= gen (generate-count))
(assert (== (.gen.next) 17))
(assert (== (.gen.next) 18))
(assert (== (.gen.next) 29))
