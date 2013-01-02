# docstrings

(define (marklar a b)
  """Marklar two marklars together and return the result, while continuing
  the marklarage of both meta-marklars."""

  (marklar a (.b.marklar)))
 
(assert (in "two marklars together" .marklar.__doc__))
(assert (>= (len (.marklar.__doc__.splitlines)) 2))
