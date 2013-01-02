# let

(= some-var 'shadowed')
(let ((some-var 12))
     (assert (== some-var 12)))
(assert (== some-var 'shadowed'))

(define (test-let arg)
  (= share-me 42)
  (= the_divisor 2)
  (let ((the_answer share-me)
        (the_divisor (/ the_answer 3)))
    (assert (== share-me 42))
    (assert (== the_answer 42))
    (assert (== the_divisor 14.0)) 
    (= share-me arg))
  (assert (== the_divisor 2))
  (assert (== share-me arg)))
(test-let 1234)
