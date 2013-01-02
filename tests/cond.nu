# cond

(define (ctype c)
  (cond ((<= 'a' c 'z') "lowercase")
        ((<= 'A' c 'Z') "uppercase")
        ((in c "!@#$%^&*()-=_+[]{}\|;:'\"\\,./<>?`~") "punc")))

(assert (== (ctype 't') 'lowercase'))
(assert (== (ctype 'a') 'lowercase'))
(assert (== (ctype 'Z') 'uppercase'))
(assert (== (ctype 'R') 'uppercase'))
(assert (== (ctype '#') 'punc'))
(assert (is (ctype (chr 0)) None))

(assert (is (cond) None))
(assert (== (cond (False 14) (else 9)) 9))
