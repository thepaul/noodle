# function definition

(define (same-number one two)
  (== one two))

(assert (same-number 1 1.0))
(assert (not (same-number 2 -2)))

(define (func-with-specials foo bar:'bar' @varargs @@kwargs)
  \(foo bar varargs kwargs))

(assert (== (func-with-specials 2)
            \(2 'bar' () {})))
(assert (== (func-with-specials 2 boo:'froo')
            \(2 'bar' () {'boo': 'froo'})))
(assert (== (func-with-specials 3 'bonk' 'broom')
            \(3 'bonk' \('broom') {})))
(assert (==
  (try (func-with-specials)
    (except (TypeError) 15)
    (else False))
  15))

(assert (== (func-with-specials 'five' 2 3 four:4)
            \('five' 2 \(3) {'four': 4})))
