# closure

(define (dictadd a b)
  (.(= d (.a.copy)).update b)
  d)

(define (partial func @fa @@fk)
  (lambda (@a @@k) (func @(+ fa a) @@(dictadd fk k))))

(assert (is .partial.__doc__ None))

(define (add a b) (+ a b))
(define p (partial add 2))
(assert (== (p 9) 11))

(define (keywords foo:1 bar:2) \(foo bar))

(= tuple-ending-in-10 (partial keywords bar:10))
(assert (== (tuple-ending-in-10 12) \(12 10)))
(assert (== (tuple-ending-in-10 foo:11) \(11 10)))
(assert (== (tuple-ending-in-10 bar:3) \(1 3)))
