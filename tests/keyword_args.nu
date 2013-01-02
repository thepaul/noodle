# keyword arguments

(define (keyword-receiver a:9 b:2)
  (% a b))
(assert (== (keyword-receiver) 1))
(assert (== (keyword-receiver 10) 0))
(assert (== (keyword-receiver 10 6) 4))
(assert (== (keyword-receiver "mon%d") 'mon2'))
(assert (== (keyword-receiver a:"mon%d") 'mon2'))
(assert (== (keyword-receiver b:5) 4))
(assert (== (keyword-receiver a:19 b:3) 1))
(assert (== (keyword-receiver b:3 a:19) 1))
