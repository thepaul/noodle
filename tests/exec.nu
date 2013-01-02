# exec

(= change-me 1262)
(exec "change_me = -3")
(assert (== change_me -3))

(= map {'var': 0 'bar': 1})
(= bar 123)
(exec "bar = 'hello'" map)
(assert (== [map 'bar'] 'hello'))
(assert (== bar 123))
